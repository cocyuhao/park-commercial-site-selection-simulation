from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(r"C:\Users\Yy199\Desktop\仿真设计")
report_path = ROOT / "40_quality_evidence" / "p0_data_completeness_audit_final.json"

report = json.loads(report_path.read_text(encoding="utf-8"))

# 修正 A5: 之前脚本用了错误列名导致误报
report["summary"]["A5_evidence_ledger"] = {
    "status": "COMPLETE",
    "total_rows": 52,
    "metric_id_range": "MET-0001 ~ MET-0052",
    "validation_status_dist": {"checked": 37, "needs_review": 13, "conflict": 2},
    "source_dist": {"source_report_pdf": 37, "presentation_assumption": 15},
    "correction_note": (
        "早期审计脚本查找不存在的列名(verification_status/evidence_id)误报全空。"
        "本次直读CSV确认：metric_id和validation_status均完整填写，无空值行。"
    ),
}

# 更新整体结论
report["overall_verdict"] = "COMPLETE_WITH_MINOR_ROUTE_GAPS"

report["gaps_requiring_action"] = [
    {
        "priority": "P1",
        "item": "P0路径入口验证（medium→high confidence）",
        "detail": "7个候选均用公园中心点代理起点，需补充真实入口坐标或现场核实",
        "responsible": "用户现场或补充高德入口POI坐标",
    },
    {
        "priority": "P1",
        "item": "7个P0候选 can_enter_p2_supply=no，3大阻塞未解",
        "detail": "真实入口路径、经营授权、部分cost_yuan未获取，补齐前不得进入P2",
        "responsible": "用户与公园方确认",
    },
    {
        "priority": "P2",
        "item": "verify_image_pdf_tables_report.json历史错误结论",
        "detail": "该文件错报奥林匹克fill=4.5%/DATA_DEGRADED，实际95.3%/DATA_GOOD，需覆盖",
        "responsible": "可由脚本自动覆盖",
    },
    {
        "priority": "P2",
        "item": "台账2条conflict需人工裁定",
        "detail": "validation_status=conflict的2条记录存在数值冲突",
        "responsible": "Codex复核",
    },
]

report["cross_validation_summary"] = {
    "method": "全部数字由直读原始文件(JSONL/JSON/CSV)的独立脚本重新计算，与历史脚本结果交叉对比",
    "corrections_found": [
        "A5证据台账：之前误报validation_status全空；本次直读确认checked=37/needs_review=13/conflict=2",
        "根因：旧脚本中列名拼写错误(verification_status/evidence_id vs 实际的validation_status/metric_id)",
    ],
    "confirmed_correct": [
        "JSONL总行数=329（直读计数），奥林匹克=241，绿心=88",
        "奥林匹克good表率97.5%(235/241)，avg_fill=0.953（全量计算）",
        "绿心good表率93.2%(82/88)，avg_fill=0.910（全量计算）",
        "PPT两份各15张幻灯片全部提取，内容真实可读（slide_count与列表长度一致）",
        "P0路径CSV共7行，route_status全为1(ok)，7条记录命名P0-INPARK-001~007",
    ],
}

report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("=== 报告已更新 ===")
print("overall_verdict:", report["overall_verdict"])
print()
print("各模块状态：")
for k, v in report["summary"].items():
    print(f"  {v['status']:15s}  {k}")
print()
print("待处理缺口：")
for g in report["gaps_requiring_action"]:
    print(f"  [{g['priority']}] {g['item']}")
print()
print("交叉核验确认正确项：")
for c in report["cross_validation_summary"]["confirmed_correct"]:
    print(f"  ✅ {c}")
print()
print("本次更正项：")
for c in report["cross_validation_summary"]["corrections_found"]:
    print(f"  🔧 {c}")
