from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUALITY_DIR = ROOT / "40_quality_evidence"
OUTPUT_CSV = QUALITY_DIR / "rebaseline_artifact_trust_audit_20260604.csv"
OUTPUT_MD = QUALITY_DIR / "rebaseline_artifact_trust_audit_20260604.md"


@dataclass(frozen=True)
class AuditRule:
    artifact: str
    category: str
    trust_level: str
    reason: str
    allowed_use: str
    required_action: str
    pattern: str = ""


RULES: list[AuditRule] = [
    AuditRule(
        artifact="40_quality_evidence/evidence_ledger.csv",
        category="evidence",
        trust_level="A_底座可信",
        reason="证据台账仍是可追溯资料底座。",
        allowed_use="仅使用有来源、状态和可回查字段的行；checked 行仍需来源一致。",
        required_action="后续新增证据继续按 evidence_id 和 verification_status 入账。",
    ),
    AuditRule(
        artifact="30_extraction/tables/pdf_native_tables.jsonl",
        category="extraction",
        trust_level="A_底座可信",
        reason="PDF 原生表格抽取结果可复跑、可回查。",
        allowed_use="用于证据候选和表格回查，不直接推出商业结论。",
        required_action="继续用 verify_pdf_tables.py 作为抽取门禁。",
    ),
    AuditRule(
        artifact="90_p6_expert_dashboard/",
        category="product_shell",
        trust_level="B_产品壳可用",
        reason="AI 工作台、资料池、项目总览和报告入口可作为业务人员操作界面。",
        allowed_use="用于可用性、复核和交互原型，不证明人物仿真准确。",
        required_action="接入人群状态和行为程序 CRUD，并隐藏旧测试/后端文案。",
    ),
    AuditRule(
        artifact="60_model/simulation/engine.py",
        category="simulation",
        trust_level="B_需改口径",
        reason="当前是结构化 dry-run，不是老板资料意义上的完整仿真。",
        allowed_use="可保留为门禁、阻塞原因和缺口整理模块。",
        required_action="不得输出完整仿真、最终排序、ROI 或最终推荐。",
    ),
    AuditRule(
        artifact="60_model/simulation/persona_behavior.py",
        category="simulation",
        trust_level="C_草稿候选",
        reason="可作为状态/行为 schema 思路，但未完成真实校准。",
        allowed_use="用于候选字段和测试样例。",
        required_action="映射到 persona_state / behavior_program schema 后再进入 UI。",
    ),
    AuditRule(
        artifact="60_model/llm_runs/*",
        category="deepseek_legacy",
        trust_level="C_历史草稿",
        reason="旧 DeepSeek 输出未使用新 envelope，不能直接进入新主线。",
        allowed_use="仅用于追踪历史、复核和重新抽取。",
        required_action="通过 adapt_deepseek_legacy_outputs.py 包装为审计 envelope 或标记不可适配。",
        pattern="60_model/llm_runs/*",
    ),
    AuditRule(
        artifact="70_outputs/processed_tables/p2_*_20260604.csv",
        category="p2_method_draft",
        trust_level="C_草稿候选",
        reason="按老板资料补出的 persona/behavior/validation 表仍未被真实资料校准。",
        allowed_use="用于 schema、UI 和测试样例，不作为最终模型。",
        required_action="逐行映射到 schema，补 source_refs、missing_inputs 和 adoption_state。",
        pattern="70_outputs/processed_tables/p2_*_20260604.csv",
    ),
    AuditRule(
        artifact="70_outputs/processed_tables/p2_*deepseek*.csv",
        category="p2_deepseek_draft",
        trust_level="C_历史草稿",
        reason="DeepSeek 草稿只能提供语义线索。",
        allowed_use="用于复核队列和候选解释。",
        required_action="进入 envelope 后重新抽样检查，不得入 checked。",
        pattern="70_outputs/processed_tables/p2_*deepseek*.csv",
    ),
    AuditRule(
        artifact="70_outputs/processed_tables/p3_*deepseek*.csv",
        category="p3_deepseek_draft",
        trust_level="C_历史草稿",
        reason="P3 校准相关文件是待补资料工作包，不代表门禁已闭合。",
        allowed_use="用于向合作方索要资料和记录阻塞。",
        required_action="保持 gate pending，直到真实资料或现场复核闭合。",
        pattern="70_outputs/processed_tables/p3_*deepseek*.csv",
    ),
    AuditRule(
        artifact="70_outputs/processed_tables/p4_*deepseek*.csv",
        category="p4_deepseek_draft",
        trust_level="D_必须降级",
        reason="P4 反馈草稿容易被误读为完整仿真或最终排序。",
        allowed_use="只用于合作方反馈和补资料请求。",
        required_action="移除或折叠裸排名/裸分数，重写为优先级、依据、建议和缺口。",
        pattern="70_outputs/processed_tables/p4_*deepseek*.csv",
    ),
    AuditRule(
        artifact="80_delivery/ai_chat_reports/CHAT-*.md",
        category="delivery_draft",
        trust_level="C_测试痕迹",
        reason="多数由 Selenium/AI 工作台验证生成，不是客户正式报告。",
        allowed_use="用于报告格式回归和交互验证证据。",
        required_action="正式报告生成时要重新按商业报告结构和证据状态输出。",
        pattern="80_delivery/ai_chat_reports/CHAT-*.md",
    ),
    AuditRule(
        artifact="choice_probability.schema.json",
        category="missing_object",
        trust_level="E_需新增",
        reason="消费选择不能继续靠 LLM 直接判断或裸分数。",
        allowed_use="尚无。",
        required_action="新增选择概率 schema，连接状态、行为、空间成本、排队、价格、竞品和证据。",
    ),
    AuditRule(
        artifact="macro_validation_plan.md",
        category="missing_object",
        trust_level="E_需新增",
        reason="老板资料要求状态-行为-证据链一致性和宏观统计一致性双门禁。",
        allowed_use="尚无。",
        required_action="定义 SARIMA/SSIM/KL/DTW/峰谷/现场复核等验证目标与数据缺口。",
    ),
]


def expand_rule(rule: AuditRule) -> list[dict[str, str]]:
    if rule.pattern:
        paths = sorted(ROOT.glob(rule.pattern))
    else:
        paths = [ROOT / rule.artifact]

    if not paths:
        return [
            {
                "artifact": rule.artifact,
                "exists": "false",
                "bytes": "",
                "category": rule.category,
                "trust_level": rule.trust_level,
                "reason": rule.reason,
                "allowed_use": rule.allowed_use,
                "required_action": rule.required_action,
            }
        ]

    rows: list[dict[str, str]] = []
    for path in paths:
        if path.name == "contract_envelopes":
            continue
        rel = path.relative_to(ROOT).as_posix()
        exists = path.exists()
        rows.append(
            {
                "artifact": rel,
                "exists": str(exists).lower(),
                "bytes": str(path.stat().st_size) if exists and path.is_file() else "",
                "category": rule.category,
                "trust_level": rule.trust_level,
                "reason": rule.reason,
                "allowed_use": rule.allowed_use,
                "required_action": rule.required_action,
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "artifact",
        "exists",
        "bytes",
        "category",
        "trust_level",
        "reason",
        "allowed_use",
        "required_action",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, str]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["trust_level"]] = counts.get(row["trust_level"], 0) + 1

    lines = [
        "# 老板方法重基线后的旧产物可信度审计（2026-06-04）",
        "",
        "本报告由 `60_model/scripts/audit_rebaseline_artifacts.py` 生成。它不删除旧文件，只按新主控方法给旧产物打标签，防止旧 dry-run、DeepSeek 草稿、测试报告和裸分数继续被误读为已完成仿真。",
        "",
        "## 汇总",
        "",
    ]
    for trust_level in sorted(counts):
        lines.append(f"- {trust_level}: {counts[trust_level]} 项")
    lines.extend(
        [
            "",
            "## 关键结论",
            "",
            "- A 类可以继续作为资料和工具底座，但不能直接证明商业结论。",
            "- B 类是产品壳或结构化 dry-run，必须改口径。",
            "- C 类只能作为草稿候选或历史记录，必须进入 schema/envelope 后复核。",
            "- D 类必须降级，尤其是 P4 草稿、裸分数、排名和收益相关内容。",
            "- E 类是新方向缺失对象，必须补齐后才能声称人物仿真链路推进。",
            "",
            "## 明细",
            "",
            "| artifact | exists | trust | required_action |",
            "|---|---:|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row['artifact']}` | {row['exists']} | {row['trust_level']} | {row['required_action']} |"
        )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows: list[dict[str, str]] = []
    for rule in RULES:
        rows.extend(expand_rule(rule))
    rows.sort(key=lambda item: (item["trust_level"], item["category"], item["artifact"]))
    write_csv(rows)
    write_md(rows)
    print(f"wrote {len(rows)} artifact audit rows to {OUTPUT_CSV}")
    print(f"wrote markdown report to {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
