from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
NODE_DRAFT_CSV = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_node_priority_draft_deepseek.csv"
REQUEST_CSV = ROOT / "70_outputs" / "processed_tables" / "p4_feedback_data_request_to_partner_deepseek.csv"
ENVELOPE_PATH = ROOT / "60_model" / "llm_runs" / "contract_envelopes" / "p4_node_explanation_from_legacy_20260604.json"
OUTPUT_CSV = ROOT / "70_outputs" / "processed_tables" / "p4_node_explanation_from_legacy_20260604.csv"
REPORT_JSON = ROOT / "40_quality_evidence" / "p4_node_explanation_adapter_20260604.json"
REPORT_MD = ROOT / "40_quality_evidence" / "p4_node_explanation_adapter_20260604.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_cn_list(value: str) -> list[str]:
    return [part.strip() for part in value.replace("；", "、").replace("，", "、").split("、") if part.strip()]


def parse_business_direction(value: str) -> list[str]:
    if not value.strip():
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return split_cn_list(value)
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return split_cn_list(str(parsed))


def requests_by_node(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row.get("node_id", ""), []).append(row)
    return grouped


def make_review_actions(node_id: str, request_rows: list[dict[str, str]], fallback_gaps: list[str]) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()
    for row in request_rows:
        missing = row.get("missing_input", "").strip()
        why = row.get("why_needed", "").strip()
        acceptable = row.get("acceptable_response", "").strip()
        if not missing or missing in seen:
            continue
        seen.add(missing)
        detail = f"补齐「{missing}」"
        if why:
            detail += f"：{why}"
        if acceptable:
            detail += f" 可接受材料：{acceptable}"
        actions.append(detail)
    for gap in fallback_gaps:
        if gap and gap not in seen:
            actions.append(f"补齐「{gap}」后再更新节点优先级。")
    actions.append(f"把 {node_id} 的旧讨论分折叠展示，主界面只展示推进动作、证据缺口和待复核状态。")
    return actions


def score_value(row: dict[str, str]) -> float | None:
    raw = row.get("discussion_score", "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def build_item(row: dict[str, str], request_rows: list[dict[str, str]]) -> dict[str, Any]:
    node_id = row.get("node_id", "").strip()
    node_name = row.get("node_name", "").strip()
    business = parse_business_direction(row.get("business_direction", ""))
    business_short = "、".join(business[:3]) if business else "业务方向草案"
    gaps = split_cn_list(row.get("must_collect_before_final", ""))
    actions = make_review_actions(node_id, request_rows, gaps)
    score = score_value(row)

    why_now = [
        f"{node_name or node_id} 已有旧 P4 反馈草案和候选业态方向，可转成待复核的节点解释。",
        "旧讨论分只表示当时资料条件下的讨论顺序，不能作为最终排序、收益判断或运营决策。",
        "老板方法重基线后，该节点必须先补齐人群状态、行为程序、空间可达和运营授权，再进入仿真判断。",
    ]
    if business_short:
        why_now.append(f"当前可先围绕「{business_short}」组织假设，但必须保持 needs_review。")

    specific_advice = [
        "先把该节点标为「补资料后判断」，不要进入最终推荐或收益测算。",
        f"围绕「{business_short}」拆出服务人群、触发时段、消费/放弃条件和运营约束。",
        "把真实客流、转化率、收益成本、运营授权和 DWG/GIS 几何作为升级前置门禁。",
        "在用户界面中提供采用、放弃、编辑和锁定动作，把是否采用交还给用户。",
    ]

    evidence_support = [
        f"来源：{NODE_DRAFT_CSV.relative_to(ROOT).as_posix()} 中 {node_id} 的旧 P4 feedback draft。",
        f"节点名称：{node_name or node_id}。",
        f"旧用途边界：{row.get('use_boundary', '').strip() or 'feedback draft only'}。",
    ]
    if row.get("score_reason", "").strip():
        evidence_support.append(f"旧分数说明：{row['score_reason'].strip()}")

    evidence_gaps = gaps or ["真实客流", "转化率", "收益成本", "运营授权", "DWG/GIS 几何"]
    for request in request_rows:
        missing = request.get("missing_input", "").strip()
        if missing and missing not in evidence_gaps:
            evidence_gaps.append(missing)

    return {
        "node_id": node_id,
        "mode": "node",
        "priority_label": "补资料后判断",
        "why_now": why_now,
        "specific_advice": specific_advice,
        "evidence_support": evidence_support,
        "evidence_gaps": evidence_gaps,
        "review_actions": actions,
        "score_if_any": {
            "value": score,
            "meaning": "旧 P4 feedback draft 的讨论分，已降级为折叠辅助说明；不代表最终排序、收益测算或运营决策。",
            "hidden_by_default": True,
        },
    }


def build_envelope(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "task_id": "P4-NODE-EXPLANATION-ADAPTER-20260604",
        "task_type": "node_explanation",
        "output_status": "needs_review",
        "source_refs": [
            {
                "source_file": NODE_DRAFT_CSV.relative_to(ROOT).as_posix(),
                "page_or_slide": "csv",
                "quote_or_table_ref": "p4 feedback node priority draft rows",
            },
            {
                "source_file": REQUEST_CSV.relative_to(ROOT).as_posix(),
                "page_or_slide": "csv",
                "quote_or_table_ref": "p4 feedback data request rows",
            },
            {
                "source_file": "10_research/boss_method_materials_20260604/full_system_rebaseline_20260604.md",
                "page_or_slide": "method",
                "quote_or_table_ref": "node score downgrade and state-behavior-demand-advice constraint",
            },
        ],
        "assumptions": [
            "This adapter downgrades old P4 score/ranking language into human-readable node explanation.",
            "All node explanations remain needs_review because P3 calibration inputs are missing.",
            "Scores are hidden by default and are not final rankings.",
        ],
        "uncertainties": [
            "The old CSV does not contain complete persona state, behavior program, route, queue, or conversion evidence.",
            "DWG/GIS geometry, visitor flow, conversion rate, revenue/cost, and operation authorization remain unresolved.",
        ],
        "needs_human_review": True,
        "items": items,
    }


def write_outputs(items: list[dict[str, Any]], envelope: dict[str, Any]) -> None:
    ENVELOPE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)

    ENVELOPE_PATH.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "node_id",
            "priority_label",
            "why_now",
            "specific_advice",
            "evidence_gaps",
            "review_actions",
            "score_hidden",
            "score_value",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "node_id": item["node_id"],
                    "priority_label": item["priority_label"],
                    "why_now": "；".join(item["why_now"]),
                    "specific_advice": "；".join(item["specific_advice"]),
                    "evidence_gaps": "；".join(item["evidence_gaps"]),
                    "review_actions": "；".join(item["review_actions"]),
                    "score_hidden": str(item["score_if_any"]["hidden_by_default"]).lower(),
                    "score_value": item["score_if_any"]["value"],
                }
            )

    report = {
        "adapter": "adapt_p4_node_explanations.py",
        "status": "needs_review",
        "item_count": len(items),
        "envelope_path": ENVELOPE_PATH.relative_to(ROOT).as_posix(),
        "csv_path": OUTPUT_CSV.relative_to(ROOT).as_posix(),
        "boundary": "Old P4 scores are downgraded to hidden helper metadata; node UI/report should use priority, advice, evidence gaps, and review actions.",
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# P4 节点解释 adapter 报告（2026-06-04）",
        "",
        "本报告由 `60_model/scripts/adapt_p4_node_explanations.py` 生成。",
        "",
        "## 口径",
        "",
        "旧 P4 节点分数和排名语言已降级为 `node_explanation` 草稿。主输出是优先级、依据、具体建议、证据缺口和复核动作；旧分数只保留在 `score_if_any` 中，并默认隐藏。",
        "",
        f"- 节点数：{len(items)}",
        f"- Envelope：`{ENVELOPE_PATH.relative_to(ROOT).as_posix()}`",
        f"- CSV：`{OUTPUT_CSV.relative_to(ROOT).as_posix()}`",
        "",
        "## 下一步",
        "",
        "- 前端节点详情和报告生成优先读取 `specific_advice`、`evidence_gaps`、`review_actions`。",
        "- 补齐 persona_state 和 behavior_program 后，再把节点解释升级为 `state -> behavior -> demand -> advice` 完整链条。",
        "- 不得把旧讨论分当最终排序或收益预测。",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    node_rows = read_csv(NODE_DRAFT_CSV)
    request_rows = read_csv(REQUEST_CSV)
    grouped_requests = requests_by_node(request_rows)
    items = [build_item(row, grouped_requests.get(row.get("node_id", ""), [])) for row in node_rows]
    envelope = build_envelope(items)
    write_outputs(items, envelope)
    print(f"wrote node explanation envelope to {ENVELOPE_PATH}")
    print(f"wrote node explanation csv to {OUTPUT_CSV}")
    print(f"node_explanation_items={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
