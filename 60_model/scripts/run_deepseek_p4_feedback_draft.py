from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import run_deepseek_task  # noqa: E402  # type: ignore[import-not-found]


TASK_ID = "LLM-025"
RAW = ROOT / "60_model" / "llm_runs" / "deepseek_p4_feedback_draft_raw.jsonl"
PROGRESS = ROOT / "60_model" / "llm_runs" / "deepseek_p4_feedback_draft_progress.json"
OUT_NODE = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_node_priority_draft_deepseek.csv"
OUT_SCENE = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_scenario_matrix_draft_deepseek.csv"
OUT_REQUEST = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_data_request_to_partner_deepseek.csv"
OUT_JSON = ROOT / "40_quality_evidence" / "deepseek_p4_feedback_draft.json"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p4_feedback_draft.md"

NODE_FIELDS = [
    "node_id",
    "node_name",
    "area_sqm",
    "business_direction",
    "feedback_priority",
    "discussion_score",
    "score_reason",
    "placeholder_inputs_used",
    "must_collect_before_final",
    "use_boundary",
    "output_status",
    "executor",
    "llm_task_id",
]
SCENE_FIELDS = [
    "scenario_id",
    "node_id",
    "scenario_name",
    "target_persona",
    "draft_conversion_band",
    "draft_spending_band_yuan",
    "draft_opex_risk",
    "feedback_question",
    "use_boundary",
    "output_status",
    "executor",
    "llm_task_id",
]
REQUEST_FIELDS = [
    "request_id",
    "node_id",
    "missing_input",
    "why_needed",
    "acceptable_response",
    "priority",
    "output_status",
    "executor",
    "llm_task_id",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_text(path: Path, limit: int = 9000) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")[:limit]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "")) for field in fields})


def parse_json(value: str) -> dict[str, Any]:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text))


def mark(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        row["output_status"] = "needs_review"
        row["executor"] = "deepseek"
        row["llm_task_id"] = TASK_ID
    return rows


def normalize(payload: dict[str, Any], nodes: list[dict[str, str]]) -> dict[str, Any]:
    node_rows = [row for row in payload.get("node_priority_draft", []) if isinstance(row, dict)]
    node_by_id = {row.get("node_id"): row for row in node_rows}
    clean_nodes: list[dict[str, Any]] = []
    for index, node in enumerate(nodes, start=1):
        row = dict(node_by_id.get(node.get("node_id"), {}))
        row["node_id"] = node.get("node_id", f"P2-NODE-{index:03d}")
        row["node_name"] = node.get("node_name", "")
        row["area_sqm"] = node.get("area_sqm", "")
        row.setdefault("business_direction", node.get("candidate_business_formats", "")[:120])
        row.setdefault("feedback_priority", "discussion_only")
        row.setdefault("discussion_score", str(max(55, 86 - index * 4)))
        row.setdefault("score_reason", "基于用户提供策划书和P2方法原型的反馈草案，非最终排序。")
        row.setdefault("placeholder_inputs_used", "客流分配/转化率/客单价/运营成本为占位假设")
        row.setdefault("must_collect_before_final", "真实客流、转化率、收益成本、运营授权、DWG几何")
        row["use_boundary"] = "feedback_draft_not_final_ranking"
        clean_nodes.append(row)

    scene_rows = [row for row in payload.get("scenario_matrix_draft", []) if isinstance(row, dict)]
    while len(scene_rows) < 12:
        node = nodes[len(scene_rows) % max(1, len(nodes))]
        scene_rows.append(
            {
                "scenario_id": f"P4-FB-SCN-{len(scene_rows) + 1:03d}",
                "node_id": node.get("node_id", ""),
                "scenario_name": "反馈讨论场景",
                "target_persona": "待访谈确认",
                "draft_conversion_band": "placeholder 5%-20%",
                "draft_spending_band_yuan": "placeholder 30-150",
                "draft_opex_risk": "medium",
                "feedback_question": "请确认该场景是否符合运营方预期。",
                "use_boundary": "scenario_feedback_only",
            }
        )
    for row in scene_rows[:12]:
        row["use_boundary"] = "scenario_feedback_only"

    request_rows = [row for row in payload.get("data_request_to_partner", []) if isinstance(row, dict)]
    required_inputs = ["真实客流", "转化率", "客单价", "租金/分成", "装修/人工/运营成本", "运营授权"]
    while len(request_rows) < 12:
        request_rows.append({})
    for idx, row in enumerate(request_rows[:12], start=1):
        node = nodes[(idx - 1) % max(1, len(nodes))]
        missing = required_inputs[(idx - 1) % len(required_inputs)]
        row.setdefault("request_id", f"P4-FB-REQ-{idx:03d}")
        if not row.get("node_id"):
            row["node_id"] = node.get("node_id", "")
        if not row.get("missing_input"):
            row["missing_input"] = missing
        if not row.get("why_needed"):
            row["why_needed"] = "用于把反馈草案升级为可校准P4模型。"
        if not row.get("acceptable_response"):
            row["acceptable_response"] = "表格、合同口径、运营方确认或现场统计均可，缺失则保留为空。"
        row.setdefault("priority", "high")
    mark(clean_nodes)
    mark(scene_rows)
    mark(request_rows)
    return {
        "summary": payload.get("summary", "P4反馈草案可用于向运营/合作方征询数据，不是最终仿真结论。"),
        "node_priority_draft": clean_nodes[:6],
        "scenario_matrix_draft": scene_rows[:12],
        "data_request_to_partner": request_rows[:12],
        "output_status": "needs_review",
        "executor": "deepseek",
        "llm_task_id": TASK_ID,
    }


def main() -> None:
    nodes = read_csv(ROOT / "70_outputs" / "processed_tables" / "p2_project_node_candidates.csv")
    context = {
        "user_correction": "用户确认客流以最开始资料为准，缺失数据保留缺失；允许先用假设做P4反馈草案，用于向别人反馈并启动数据复核。",
        "plan_excerpt": read_text(ROOT / "30_extraction" / "p2_real_site" / "osen_project_plan_text.txt"),
        "nodes": nodes,
        "scenes": read_csv(ROOT / "70_outputs" / "processed_tables" / "p2_business_scene_assumption_pool.csv"),
        "p3_gates": read_csv(ROOT / "70_outputs" / "processed_tables" / "p3_calibration_gate_status.csv"),
    }
    messages = [
        {"role": "system", "content": "你是P4反馈草案助手。多用用户已给资料，但所有输出必须needs_review，不得写成最终排序或checked证据。"},
        {
            "role": "user",
            "content": (
                "请输出严格JSON：summary, node_priority_draft[6], scenario_matrix_draft[12], data_request_to_partner[12], output_status。"
                "这是一版给合作方反馈、推动数据复核的P4 draft，可以使用占位转化率/客单价区间，但必须明确not_final、needs_review、缺失项如何复核。"
                "不要输出最终推荐、最终收益预测或checked结论。上下文："
                + json.dumps(context, ensure_ascii=False)
            ),
        },
    ]
    content = run_deepseek_task(TASK_ID, messages, temperature=0.1)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({"task_id": TASK_ID, "response": content}, ensure_ascii=False) + "\n", encoding="utf-8")
    payload = normalize(parse_json(content), nodes)
    write_csv(OUT_NODE, NODE_FIELDS, payload["node_priority_draft"])
    write_csv(OUT_SCENE, SCENE_FIELDS, payload["scenario_matrix_draft"])
    write_csv(OUT_REQUEST, REQUEST_FIELDS, payload["data_request_to_partner"])
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P4 feedback draft",
                "",
                f"- output_status: {payload['output_status']}",
                "- use_boundary: feedback draft only, not final ranking.",
                f"- node rows: {len(payload['node_priority_draft'])}",
                f"- scenario rows: {len(payload['scenario_matrix_draft'])}",
                f"- data request rows: {len(payload['data_request_to_partner'])}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    PROGRESS.write_text(
        json.dumps({"task_id": TASK_ID, "node_rows": 6, "scenario_rows": 12, "request_rows": 12, "output_status": "needs_review"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{OUT_NODE.name} rows=6")
    print(f"{OUT_SCENE.name} rows=12")
    print(f"{OUT_REQUEST.name} rows=12")
    print("output_status=needs_review")


if __name__ == "__main__":
    main()
