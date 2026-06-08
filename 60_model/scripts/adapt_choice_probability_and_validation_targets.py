from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import polars as pl
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "70_outputs" / "processed_tables"
ENVELOPE_DIR = ROOT / "60_model" / "llm_runs" / "contract_envelopes"
QUALITY_DIR = ROOT / "40_quality_evidence"

PERSONA_CSV = PROCESSED / "p2_persona_state_profiles_20260604.csv"
PROGRAM_CSV = PROCESSED / "p2_behavior_program_templates_20260604.csv"
NODE_CSV = PROCESSED / "p4_node_explanation_from_legacy_20260604.csv"
VALIDATION_CSV = PROCESSED / "p2_simulation_validation_targets_20260604.csv"

CHOICE_SCHEMA = ROOT / "60_model" / "schemas" / "choice_probability.schema.json"
VALIDATION_SCHEMA = ROOT / "60_model" / "schemas" / "simulation_validation_target.schema.json"

CHOICE_ENVELOPE = ENVELOPE_DIR / "choice_probability_from_p2_p4_20260604.json"
VALIDATION_ENVELOPE = ENVELOPE_DIR / "simulation_validation_target_from_p2_20260604.json"
CHOICE_OUTPUT_CSV = PROCESSED / "choice_probability_from_p2_p4_20260604.csv"
VALIDATION_OUTPUT_CSV = PROCESSED / "simulation_validation_target_from_p2_20260604.csv"
CHOICE_REPORT_JSON = QUALITY_DIR / "choice_probability_adapter_20260604.json"
CHOICE_REPORT_MD = QUALITY_DIR / "choice_probability_adapter_20260604.md"
VALIDATION_REPORT_JSON = QUALITY_DIR / "simulation_validation_target_adapter_20260604.json"
VALIDATION_REPORT_MD = QUALITY_DIR / "simulation_validation_target_adapter_20260604.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    frame = pl.read_csv(path, encoding="utf8-lossy")
    return [
        {key: "" if value is None else str(value) for key, value in row.items()}
        for row in frame.to_dicts()
    ]


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def split_parts(value: str) -> list[str]:
    parts = re.split(r"[;；、\n]+", value or "")
    return [part.strip() for part in parts if part.strip()]


def first_sentence(value: str, fallback: str) -> str:
    parts = split_parts(value)
    return parts[0] if parts else fallback


def extract_node_name(row: dict[str, str]) -> str:
    text = row.get("why_now", "")
    match = re.match(r"(.+?)\s+已有旧\s*P4", text)
    if match:
        return match.group(1).strip()
    return row.get("node_id", "节点").strip()


def program_by_persona(programs: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    grouped: dict[str, dict[str, str]] = {}
    for row in programs:
        name = row.get("persona_name", "").strip()
        if name and name not in grouped:
            grouped[name] = row
    return grouped


def unique_list(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            result.append(cleaned)
            seen.add(cleaned)
    return result


def build_choice_items(
    personas: list[dict[str, str]],
    programs: list[dict[str, str]],
    nodes: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_persona = program_by_persona(programs)
    items: list[dict[str, Any]] = []
    for persona_idx, persona in enumerate(personas, start=1):
        persona_name = persona.get("persona_name", "").strip()
        program = by_persona.get(persona_name, {})
        program_id = program.get("program_id", f"PROGRAM-PLACEHOLDER-{persona_idx:03d}")
        for node_idx, node in enumerate(nodes, start=1):
            node_id = node.get("node_id", f"NODE-{node_idx:03d}").strip()
            node_name = extract_node_name(node)
            gaps = unique_list(
                split_parts(node.get("evidence_gaps", ""))
                + split_parts(persona.get("calibration_status", ""))
                + [
                    "按入口/节点/时段的真实客流",
                    "从到访到消费的转化率",
                    "路线距离、绕行、排队和营业时段",
                    "收益成本和运营授权",
                ]
            )
            persona_need = persona.get("primary_consumption_needs", "").strip() or persona.get("visit_purpose", "").strip()
            action_summary = first_sentence(program.get("actions", ""), "先补齐行为程序再判断消费选择。")
            node_advice = split_parts(node.get("specific_advice", ""))
            offer_id = f"OFFER-{node_id}-{persona.get('persona_id', persona_idx)}"
            choice_id = f"CHOICE-{persona_idx:02d}-{node_idx:02d}"
            items.append(
                {
                    "choice_id": choice_id,
                    "project_id": "park-commercial-site-selection-simulation",
                    "persona_id": persona.get("persona_id", f"PERSONA-{persona_idx:03d}"),
                    "program_id": program_id,
                    "node_id": node_id,
                    "offer_id": offer_id,
                    "scenario_id": "SCENARIO-P2-P4-NEEDS-REVIEW-20260604",
                    "method_family": [
                        "behavior_program",
                        "poi_tgi_gap",
                        "placeholder",
                    ],
                    "probability_status": "needs_review",
                    "probability_value": None,
                    "priority_label": "补资料后判断",
                    "factor_inputs": {
                        "segment_weight": None,
                        "time_weight": None,
                        "distance_decay": None,
                        "queue_penalty": None,
                        "price_budget_match": None,
                        "opening_hours_match": None,
                        "poi_supply_capacity": None,
                        "evidence_confidence": None,
                    },
                    "plain_language_explanation": [
                        f"{persona_name or '该人群'}在{node_name}的消费选择目前只能做候选判断，不能给真实概率。",
                        f"已有行为草稿提示：{action_summary}",
                        f"当前可讨论的需求方向是：{persona_need or '待补充消费需求'}。",
                        "缺少真实客流、路径、排队、转化率和授权信息，因此不能把该候选写成最终推荐。",
                    ],
                    "specific_advice": unique_list(
                        [
                            f"先围绕{persona_name or '该人群'}补齐触发时段、路线、停留和放弃条件。",
                            f"把{node_name}的业态假设拆成可验证的小服务项，再决定是否采用。",
                            "补齐真实客流和转化率后，再允许从候选优先级进入概率估计。",
                        ]
                        + node_advice[:2]
                    ),
                    "source_refs": [
                        PERSONA_CSV.relative_to(ROOT).as_posix(),
                        PROGRAM_CSV.relative_to(ROOT).as_posix(),
                        NODE_CSV.relative_to(ROOT).as_posix(),
                        "10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md",
                        "10_research/boss_method_materials_20260604/method_absorption_landing_register_20260604.md",
                    ],
                    "missing_inputs": gaps,
                    "user_locked": False,
                }
            )
    return items


def validation_mapping(domain: str) -> tuple[str, list[str]]:
    mapping: dict[str, tuple[str, list[str]]] = {
        "visitor_flow_time": ("time_series", ["peak_shift", "correlation", "dtw_r2", "sarima_consistency"]),
        "route_choice": ("route_access", ["route_reachability", "field_check", "manual_review"]),
        "dwell_time": ("state_behavior_chain", ["state_behavior_consistency", "manual_review"]),
        "conversion_rate": ("choice_probability", ["field_check", "manual_review"]),
        "spending_band": ("choice_probability", ["field_check", "manual_review"]),
        "supply_poi": ("business_decision", ["field_check", "manual_review"]),
        "geometry": ("route_access", ["route_reachability", "field_check"]),
        "authorization": ("business_decision", ["field_check", "manual_review"]),
        "scenario_sensitivity": ("macro_distribution", ["correlation", "kl_divergence", "ssim", "manual_review"]),
        "human_review": ("business_decision", ["manual_review", "llm_draft_consistency_review"]),
    }
    return mapping.get(domain, ("business_decision", ["manual_review"]))


def reference_status(current_status: str) -> str:
    value = current_status.lower()
    if "not_provided" in value or "not_started" in value:
        return "missing"
    if "blocked" in value:
        return "missing"
    if "pending" in value:
        return "available_needs_review"
    return "placeholder"


def candidate_status(current_status: str) -> str:
    value = current_status.lower()
    if "blocked" in value:
        return "blocked"
    if "not_provided" in value or "not_started" in value:
        return "not_run"
    return "needs_review"


def build_validation_items(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        domain = row.get("validation_domain", "")
        level, metrics = validation_mapping(domain)
        target_id = row.get("target_id", f"VAL-{idx:03d}")
        needed = split_parts(row.get("needed_data", ""))
        acceptable = row.get("acceptable_evidence", "").strip()
        current = row.get("current_status", "")
        blocks = (row.get("blocks_full_simulation", "") or "").lower() == "yes"
        plain_rule = (
            f"只有补齐「{row.get('needed_data', '必要资料')}」并完成业务复核后，"
            f"才能把「{row.get('what_to_validate', target_id)}」从草稿升级。"
        )
        if acceptable:
            plain_rule += f" 可接受证据包括：{acceptable}。"
        items.append(
            {
                "target_id": target_id,
                "project_id": "park-commercial-site-selection-simulation",
                "target_name": row.get("what_to_validate", target_id),
                "validation_level": level,
                "metric_family": metrics,
                "reference_data": {
                    "data_status": reference_status(current),
                    "description": row.get("acceptable_evidence", "") or row.get("needed_data", ""),
                    "required_fields": needed or [row.get("needed_data", "待补充资料")],
                },
                "candidate_output": {
                    "output_status": candidate_status(current),
                    "description": "当前只登记验证目标，不代表模型已经跑出可信结果。",
                },
                "acceptance_rule": {
                    "rule_status": "needs_review",
                    "plain_language_rule": plain_rule,
                    "thresholds": {
                        "blocks_full_simulation": "yes" if blocks else "no",
                        "numeric_threshold_pending": None,
                    },
                },
                "status": "blocked" if "blocked" in current.lower() else "needs_review",
                "source_refs": [
                    VALIDATION_CSV.relative_to(ROOT).as_posix(),
                    "10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md",
                    "10_research/boss_method_materials_20260604/simulation_accuracy_plan_20260604.md",
                ],
                "missing_inputs": needed or [row.get("needed_data", "待补充资料")],
                "review_notes": [
                    row.get("method_source", "方法来源待补充"),
                    "该目标用于阻止旧 dry-run 或 DeepSeek 草稿被误写成完整仿真。",
                ],
                "user_locked": False,
            }
        )
    return items


def validate_items(items: list[dict[str, Any]], schema_path: Path) -> list[str]:
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    failures: list[str] = []
    for index, item in enumerate(items):
        for error in validator.iter_errors(item):
            location = ".".join(str(part) for part in error.path) or "<root>"
            failures.append(f"items[{index}].{location}: {error.message}")
    return failures


def build_envelope(task_id: str, task_type: str, source_refs: list[dict[str, str]], items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_type": task_type,
        "output_status": "needs_review",
        "source_refs": source_refs,
        "assumptions": [
            "This adapter converts current P2/P4 draft rows into schema-bound needs_review candidates.",
            "The generated items are not final simulation results and do not contain checked business conclusions.",
        ],
        "uncertainties": [
            "P3 real geometry, visitor flow, route, queue, conversion, revenue/cost, and authorization inputs remain incomplete.",
            "DeepSeek or legacy drafts may only be used after schema validation and human review.",
        ],
        "needs_human_review": True,
        "items": items,
    }


def write_choice_csv(items: list[dict[str, Any]]) -> None:
    CHOICE_OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CHOICE_OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "choice_id",
            "persona_id",
            "program_id",
            "node_id",
            "offer_id",
            "probability_status",
            "probability_value",
            "priority_label",
            "method_family",
            "plain_language_explanation",
            "specific_advice",
            "missing_inputs",
            "user_locked",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "choice_id": item["choice_id"],
                    "persona_id": item["persona_id"],
                    "program_id": item["program_id"],
                    "node_id": item["node_id"],
                    "offer_id": item["offer_id"],
                    "probability_status": item["probability_status"],
                    "probability_value": "" if item["probability_value"] is None else item["probability_value"],
                    "priority_label": item["priority_label"],
                    "method_family": ";".join(item["method_family"]),
                    "plain_language_explanation": "；".join(item["plain_language_explanation"]),
                    "specific_advice": "；".join(item["specific_advice"]),
                    "missing_inputs": "；".join(item["missing_inputs"]),
                    "user_locked": str(item["user_locked"]).lower(),
                }
            )


def write_validation_csv(items: list[dict[str, Any]]) -> None:
    VALIDATION_OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with VALIDATION_OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "target_id",
            "target_name",
            "validation_level",
            "metric_family",
            "reference_data_status",
            "candidate_output_status",
            "status",
            "acceptance_rule",
            "missing_inputs",
            "user_locked",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "target_id": item["target_id"],
                    "target_name": item["target_name"],
                    "validation_level": item["validation_level"],
                    "metric_family": ";".join(item["metric_family"]),
                    "reference_data_status": item["reference_data"]["data_status"],
                    "candidate_output_status": item["candidate_output"]["output_status"],
                    "status": item["status"],
                    "acceptance_rule": item["acceptance_rule"]["plain_language_rule"],
                    "missing_inputs": "；".join(item["missing_inputs"]),
                    "user_locked": str(item["user_locked"]).lower(),
                }
            )


def duckdb_count(path: Path) -> int:
    rel_path = path.relative_to(ROOT).as_posix()
    with duckdb.connect(database=":memory:") as conn:
        return int(conn.execute("select count(*) from read_csv_auto(?)", [rel_path]).fetchone()[0])


def write_reports(choice_items: list[dict[str, Any]], validation_items: list[dict[str, Any]], choice_failures: list[str], validation_failures: list[str]) -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    choice_count = duckdb_count(CHOICE_OUTPUT_CSV)
    validation_count = duckdb_count(VALIDATION_OUTPUT_CSV)
    common = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_files": [
            PERSONA_CSV.relative_to(ROOT).as_posix(),
            PROGRAM_CSV.relative_to(ROOT).as_posix(),
            NODE_CSV.relative_to(ROOT).as_posix(),
            VALIDATION_CSV.relative_to(ROOT).as_posix(),
        ],
        "important_boundary": "All items remain needs_review; this is schema-bound candidate generation, not completed simulation.",
    }
    CHOICE_REPORT_JSON.write_text(
        json.dumps(
            {
                **common,
                "adapter": "adapt_choice_probability_and_validation_targets.py",
                "task_type": "choice_probability",
                "status": "needs_review" if not choice_failures else "fail",
                "item_count": len(choice_items),
                "duckdb_csv_count": choice_count,
                "schema_failure_count": len(choice_failures),
                "schema_failures": choice_failures,
                "envelope_path": CHOICE_ENVELOPE.relative_to(ROOT).as_posix(),
                "csv_path": CHOICE_OUTPUT_CSV.relative_to(ROOT).as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    VALIDATION_REPORT_JSON.write_text(
        json.dumps(
            {
                **common,
                "adapter": "adapt_choice_probability_and_validation_targets.py",
                "task_type": "simulation_validation_target",
                "status": "needs_review" if not validation_failures else "fail",
                "item_count": len(validation_items),
                "duckdb_csv_count": validation_count,
                "schema_failure_count": len(validation_failures),
                "schema_failures": validation_failures,
                "envelope_path": VALIDATION_ENVELOPE.relative_to(ROOT).as_posix(),
                "csv_path": VALIDATION_OUTPUT_CSV.relative_to(ROOT).as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    CHOICE_REPORT_MD.write_text(
        "\n".join(
            [
                "# choice_probability adapter 报告（2026-06-04）",
                "",
                "## 口径",
                "",
                "本轮把 P2 人群状态、P2 行为程序和 P4 节点解释转成选择概率候选。所有 `probability_value` 保持空值，状态为 `needs_review`，因为真实客流、路线、排队、转化率、收益成本和授权仍未闭合。",
                "",
                f"- 候选数：{len(choice_items)}",
                f"- DuckDB 复核 CSV 行数：{choice_count}",
                f"- Schema 失败数：{len(choice_failures)}",
                f"- Envelope：`{CHOICE_ENVELOPE.relative_to(ROOT).as_posix()}`",
                f"- CSV：`{CHOICE_OUTPUT_CSV.relative_to(ROOT).as_posix()}`",
                "",
                "## 下一步",
                "",
                "- 接入 P6 对象池，允许用户采用、放弃、编辑、锁定这些候选。",
                "- 补齐真实客流和转化率后，再用 SALib/Optuna 做敏感性和校准，不直接让 DeepSeek 给概率。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    VALIDATION_REPORT_MD.write_text(
        "\n".join(
            [
                "# simulation_validation_target adapter 报告（2026-06-04）",
                "",
                "## 口径",
                "",
                "本轮把 P2 验证目标草稿转成可复核对象，覆盖状态-行为链、路线可达、选择概率、时间序列、宏观分布和业务决策。它们用于阻止旧 dry-run 或 LLM 草稿被误写成完整仿真。",
                "",
                f"- 验证目标数：{len(validation_items)}",
                f"- DuckDB 复核 CSV 行数：{validation_count}",
                f"- Schema 失败数：{len(validation_failures)}",
                f"- Envelope：`{VALIDATION_ENVELOPE.relative_to(ROOT).as_posix()}`",
                f"- CSV：`{VALIDATION_OUTPUT_CSV.relative_to(ROOT).as_posix()}`",
                "",
                "## 下一步",
                "",
                "- 把这些验证目标接到 P6 资料/仿真门禁面板。",
                "- 优先补 `visitor_flow_time`、`route_choice`、`conversion_rate` 和 `geometry`，否则不能宣称真实仿真完成。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    personas = read_rows(PERSONA_CSV)
    programs = read_rows(PROGRAM_CSV)
    nodes = read_rows(NODE_CSV)
    validation_rows = read_rows(VALIDATION_CSV)

    choice_items = build_choice_items(personas, programs, nodes)
    validation_items = build_validation_items(validation_rows)

    choice_failures = validate_items(choice_items, CHOICE_SCHEMA)
    validation_failures = validate_items(validation_items, VALIDATION_SCHEMA)
    if choice_failures or validation_failures:
        write_choice_csv(choice_items)
        write_validation_csv(validation_items)
        write_reports(choice_items, validation_items, choice_failures, validation_failures)
        for failure in choice_failures + validation_failures:
            print(f"SCHEMA_FAIL {failure}")
        return 1

    ENVELOPE_DIR.mkdir(parents=True, exist_ok=True)
    choice_envelope = build_envelope(
        "CHOICE-PROBABILITY-ADAPTER-20260604",
        "choice_probability",
        [
            {
                "source_file": PERSONA_CSV.relative_to(ROOT).as_posix(),
                "page_or_slide": "csv",
                "quote_or_table_ref": "persona state profile rows",
            },
            {
                "source_file": PROGRAM_CSV.relative_to(ROOT).as_posix(),
                "page_or_slide": "csv",
                "quote_or_table_ref": "behavior program template rows",
            },
            {
                "source_file": NODE_CSV.relative_to(ROOT).as_posix(),
                "page_or_slide": "csv",
                "quote_or_table_ref": "P4 node explanation rows",
            },
        ],
        choice_items,
    )
    validation_envelope = build_envelope(
        "SIMULATION-VALIDATION-TARGET-ADAPTER-20260604",
        "simulation_validation_target",
        [
            {
                "source_file": VALIDATION_CSV.relative_to(ROOT).as_posix(),
                "page_or_slide": "csv",
                "quote_or_table_ref": "P2 simulation validation target rows",
            },
            {
                "source_file": "10_research/boss_method_materials_20260604/modern_practical_method_rescreen_20260604.md",
                "page_or_slide": "method",
                "quote_or_table_ref": "modern hybrid simulation and calibration route",
            },
        ],
        validation_items,
    )
    CHOICE_ENVELOPE.write_text(json.dumps(choice_envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    VALIDATION_ENVELOPE.write_text(json.dumps(validation_envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    write_choice_csv(choice_items)
    write_validation_csv(validation_items)
    write_reports(choice_items, validation_items, choice_failures, validation_failures)

    print(f"wrote choice envelope to {CHOICE_ENVELOPE}")
    print(f"wrote validation envelope to {VALIDATION_ENVELOPE}")
    print(f"choice_items={len(choice_items)} validation_items={len(validation_items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
