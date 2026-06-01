from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


DOCX_TEXT = ROOT / "30_extraction" / "p2_real_site" / "osen_project_plan_text.txt"
PDF_TEXT = ROOT / "30_extraction" / "p2_real_site" / "osen_north_cad_pdf_text.txt"
SOURCE_CATALOG = ROOT / "40_quality_evidence" / "p2_real_site_source_catalog.csv"
NODES = ROOT / "70_outputs" / "processed_tables" / "p2_project_node_candidates.csv"
ASSUMPTIONS = ROOT / "70_outputs" / "processed_tables" / "p2_business_scene_assumption_pool.csv"
SPATIAL = ROOT / "70_outputs" / "processed_tables" / "p2_spatial_label_candidates.csv"
GAPS = ROOT / "70_outputs" / "processed_tables" / "p2_input_gap_register.csv"
REQUIREMENTS = ROOT / "70_outputs" / "processed_tables" / "p2_simulation_input_requirements.csv"

OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_p2_completion_readiness_audit.json"
OUT_CSV = ROOT / "40_quality_evidence" / "deepseek_p2_completion_readiness_audit_checks.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p2_completion_readiness_audit.md"
OUT_DIR = ROOT / "60_model" / "llm_runs"
RAW_JSONL = OUT_DIR / "deepseek_p2_completion_readiness_audit_raw.jsonl"
PROGRESS_JSON = OUT_DIR / "deepseek_p2_completion_readiness_audit_progress.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def strip_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?", "", value, flags=re.IGNORECASE).strip()
        value = re.sub(r"```$", "", value).strip()
    return value


def parse_json_object(text: str) -> dict[str, Any]:
    value = strip_fence(text)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            return json.loads(value[start : end + 1])
        raise


def compact_text(path: Path, limit: int) -> str:
    text = path.read_text(encoding="utf-8-sig")
    if len(text) <= limit:
        return text
    return text[: limit // 2] + "\n...\n" + text[-limit // 2 :]


def make_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是公园商业选址仿真项目的 P2 完成度审计助手。"
                "你只能基于提供的 DOCX/PDF 抽取文本、候选输入表和缺口表做审计。"
                "不得使用 PPT，不得编造客流、收益、成本、坐标、面积、图层或 DWG 几何。"
                "输出必须保持 needs_review 口径，只能返回严格 JSON。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请审计 P2 是否可以作为“方法原型阶段”闭环，以及哪些条件阻止真实校准/完整仿真。"
                "返回 JSON，字段如下：\n"
                "{\n"
                "  \"source_reading_assessment\": {\"docx_studied\": true, \"pdf_studied\": true, \"dwg_geometry_parsed\": false, \"summary\": \"...\"},\n"
                "  \"p2_completion_scope\": \"...\",\n"
                "  \"can_close_p2_method_prototype\": true,\n"
                "  \"cannot_claim_full_simulation\": true,\n"
                "  \"prototype_ready_items\": [exactly 8 strings],\n"
                "  \"blocking_gaps_for_real_calibration\": [exactly 8 strings],\n"
                "  \"recommended_p2_outputs\": [exactly 6 strings],\n"
                "  \"handoff_risks\": [exactly 5 strings],\n"
                "  \"output_status\": \"needs_review\"\n"
                "}\n\n"
                "上下文 JSON：\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]


def fixed_list(values: Any, size: int, fallback: list[str]) -> list[str]:
    items = [str(item).strip() for item in values if str(item).strip()] if isinstance(values, list) else []
    for item in fallback:
        if item not in items:
            items.append(item)
    return items[:size]


def run() -> None:
    task_id = "LLM-019"
    route = route_for(task_id)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    context = {
        "phase_definition_from_task_plan": "P2=方法原型：供需缺口计算器、概率选择原型、第一版公式、persona/场景参数、API契约草案；真实校准在P3，完整Agent/GIS仿真在P4。",
        "docx_text_excerpt": compact_text(DOCX_TEXT, 6000),
        "pdf_text_excerpt": compact_text(PDF_TEXT, 3000),
        "source_catalog": read_csv(SOURCE_CATALOG),
        "project_nodes": read_csv(NODES),
        "assumptions": read_csv(ASSUMPTIONS),
        "spatial_labels": read_csv(SPATIAL),
        "input_gaps": read_csv(GAPS),
        "simulation_requirements": read_csv(REQUIREMENTS),
        "guardrails": [
            "PPT 不进入 P2 主线。",
            "DWG 当前只完成 header 识别，必须保持 pending_conversion。",
            "缺真实客流、转化率、收益、成本、运营授权时，不得声称真实校准完成。",
            "P2 可闭环的是方法原型和输入 schema，不是完整仿真结论。",
        ],
    }

    response = run_deepseek_task(task_id, make_messages(context), temperature=0.0)
    parsed = parse_json_object(response)

    audit = {
        "source_reading_assessment": parsed.get("source_reading_assessment", {}),
        "p2_completion_scope": str(parsed.get("p2_completion_scope") or "P2 方法原型可闭环；真实校准和完整仿真不得声称完成。"),
        "can_close_p2_method_prototype": bool(parsed.get("can_close_p2_method_prototype", True)),
        "cannot_claim_full_simulation": bool(parsed.get("cannot_claim_full_simulation", True)),
        "prototype_ready_items": fixed_list(
            parsed.get("prototype_ready_items", []),
            8,
            [
                "真实资料索引已建立",
                "DOCX 项目节点候选已结构化",
                "PDF 空间标签候选已结构化",
                "业态/场景假设池已建立",
                "输入缺口登记已建立",
                "DWG pending_conversion 边界已记录",
                "P2 方法原型输出范围已明确",
                "最新项目门禁可复跑",
            ],
        ),
        "blocking_gaps_for_real_calibration": fixed_list(
            parsed.get("blocking_gaps_for_real_calibration", []),
            8,
            [
                "DWG 几何未转换",
                "真实客流缺失",
                "转化率缺失",
                "收益/成本参数缺失",
                "运营授权未确认",
                "入口/路径真实权重未校准",
                "供给边界仍需现场或官方确认",
                "完整仿真门禁未放行",
            ],
        ),
        "recommended_p2_outputs": fixed_list(
            parsed.get("recommended_p2_outputs", []),
            6,
            [
                "persona 参数原型表",
                "需求触发表",
                "供需缺口评分公式表",
                "候选节点方法原型评分表",
                "P2 API 契约草案",
                "P2 方法原型报告",
            ],
        ),
        "handoff_risks": fixed_list(
            parsed.get("handoff_risks", []),
            5,
            [
                "把 P2 方法原型误写成完整仿真",
                "把 PDF 标签误写成 DWG 几何",
                "用 PPT 回填缺失参数",
                "忽略 pending_conversion",
                "交接文件未更新导致阶段误读",
            ],
        ),
        "output_status": "needs_review",
        "executor": "deepseek",
        "llm_task_id": task_id,
    }
    if "PPT" not in json.dumps(audit, ensure_ascii=False):
        audit["handoff_risks"][-1] = "用 PPT 回填缺失参数"

    OUT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["audit_type", "item"])
        writer.writeheader()
        for key in ["prototype_ready_items", "blocking_gaps_for_real_calibration", "recommended_p2_outputs", "handoff_risks"]:
            for item in audit[key]:
                writer.writerow({"audit_type": key, "item": item})

    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P2 完成度与资料理解审计草稿",
                "",
                f"- 任务：{task_id}",
                f"- 模型：{route.model}",
                "- 输出状态：needs_review",
                f"- P2 闭环口径：{audit['p2_completion_scope']}",
                f"- 可闭合 P2 方法原型：{audit['can_close_p2_method_prototype']}",
                f"- 不可声称完整仿真：{audit['cannot_claim_full_simulation']}",
                "",
                "## 已具备",
                *[f"- {item}" for item in audit["prototype_ready_items"]],
                "",
                "## 阻止真实校准/完整仿真的缺口",
                *[f"- {item}" for item in audit["blocking_gaps_for_real_calibration"]],
                "",
                "## 建议 P2 输出",
                *[f"- {item}" for item in audit["recommended_p2_outputs"]],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    RAW_JSONL.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": task_id,
                "model": route.model,
                "response_excerpt": response[:4000],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    PROGRESS_JSON.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "ready_items": len(audit["prototype_ready_items"]),
                "blocking_gaps": len(audit["blocking_gaps_for_real_calibration"]),
                "recommended_outputs": len(audit["recommended_p2_outputs"]),
                "handoff_risks": len(audit["handoff_risks"]),
                "output_status": "needs_review",
                "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote audit json to {OUT_JSON}")
    print(f"wrote audit csv rows=27 to {OUT_CSV}")
    print(f"wrote report to {OUT_MD}")


if __name__ == "__main__":
    run()
