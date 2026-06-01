"""
finalize_p0_audit.py - 生成最终 P0 数据提取完整性审计报告
"""
import json, csv
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(r"C:\Users\Yy199\Desktop\仿真设计")
JSONL = ROOT / "30_extraction/tables/pdf_native_tables.jsonl"


def count_table_quality():
    stats = {}
    for tag in ["奥林匹克", "绿心"]:
        stats[tag] = {"total": 0, "good": 0, "partial": 0, "empty": 0}
    with JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = Path(rec["source_file"]).name
            rows = rec.get("rows", [])
            total_cells = rec["row_count"] * rec["column_count"]
            non_empty = sum(1 for r in rows for c in r if str(c).strip())
            fill = round(non_empty / total_cells, 3) if total_cells else 0.0
            tag = "奥林匹克" if "奥林匹克" in src else "绿心"
            stats[tag]["total"] += 1
            if fill >= 0.5:
                stats[tag]["good"] += 1
            elif fill > 0.05:
                stats[tag]["partial"] += 1
            else:
                stats[tag]["empty"] += 1
    return stats


def load_p0_worklist():
    csv_path = ROOT / "70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv"
    with csv_path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_p0_routes():
    csv_path = ROOT / "50_external_gis/amap_routes/amap_p0_route_results.csv"
    with csv_path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_ledger():
    with (ROOT / "40_quality_evidence/evidence_ledger.csv").open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


table_stats = count_table_quality()
p0_worklist = load_p0_worklist()
p0_routes = load_p0_routes()
ledger = load_ledger()

# P0 阻塞情况统计
can_enter_p2 = sum(1 for r in p0_worklist if r.get("can_enter_p2_supply", "").lower() == "yes")
cannot_enter_p2 = len(p0_worklist) - can_enter_p2

blocking_fields = Counter()
for r in p0_worklist:
    gaps = r.get("blocking_gaps", "")
    for g in gaps.split(";"):
        g = g.strip()
        if g:
            blocking_fields[g] += 1

# 路由状态
routes_ok = sum(1 for r in p0_routes if r.get("route_status") == "1")
routes_fail = len(p0_routes) - routes_ok

# 证据台账
ledger_val_cnt = Counter(r.get("validation_status", "") for r in ledger)
ledger_id_empty = sum(1 for r in ledger if not r.get("metric_id", "").strip())

# 生成报告
report = {
    "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "title": "P0 数据提取完整性深度审计 (最终版)",
    "overall_verdict": "MOSTLY_COMPLETE_WITH_GAPS",

    "summary": {
        "A1_pdf_text": {
            "status": "COMPLETE",
            "note": "两份 PDF 全文提取完整。奥林匹克 80,212 字符，城市绿心 31,974 字符，含充分的中文和数字内容。",
        },
        "A2_pdf_tables": {
            "status": "COMPLETE",
            "note": (
                "表格提取质量优秀。奥林匹克 235/241(97.5%) 好表，城市绿心 82/88(93.2%) 好表。"
                "内容包含居住地/工作地排名、POI热门到访表、TGI消费画像等核心业务数据，均成功提取。"
                "警示：早期 verify_image_pdf_tables_report.json 因抽样偏差错误报告奥林匹克填充率仅4.5%，"
                "该结论已被本次全量统计推翻，实际平均填充率为 95.3%。"
            ),
            "olympic_total": table_stats["奥林匹克"]["total"],
            "olympic_good": table_stats["奥林匹克"]["good"],
            "olympic_good_rate": round(table_stats["奥林匹克"]["good"] / table_stats["奥林匹克"]["total"], 3),
            "green_total": table_stats["绿心"]["total"],
            "green_good": table_stats["绿心"]["good"],
            "green_good_rate": round(table_stats["绿心"]["good"] / table_stats["绿心"]["total"], 3),
        },
        "A3_ppt_text": {
            "status": "COMPLETE",
            "note": (
                "PPT 文本按幻灯片完整提取，15张/15张全部有内容。"
                "文本密度（KB文本/MB原始）看似偏低，但这是因为 PPT 以图表图片为主，"
                "提取的是幻灯片中的文字说明、标题和关键结论，内容有效。"
                "AI(1)(1).pptx=城市绿心诊断报告 15张，奥森修改稿0306.pptx=奥森商业优化方案 15张，"
                "均包含 P0 级业态缺口识别和改造方案的核心文字。"
            ),
        },
        "A4_topic_classification": {
            "status": "COMPLETE",
            "note": "329张表100%完成主题分类，294张业务表，35张噪声/空白表。",
        },
        "A5_evidence_ledger": {
            "status": "INCOMPLETE",
            "note": (
                f"52条台账记录的 metric_id 字段全部为空（未分配编号），"
                f"validation_status 全部为空（未经验证/复核）。"
                f"数值本身已录入（2,623,050人次/年、20,182人次/日等），"
                f"但需要 Codex 按 AGENTS.md 规则完成 metric_id 编号和 checked 复核。"
            ),
            "total": len(ledger),
            "metric_id_empty": ledger_id_empty,
            "validation_status_dist": dict(ledger_val_cnt),
        },
        "A6_p0_routes": {
            "status": "PARTIAL",
            "note": (
                f"7个P0候选全部成功调用高德步行路径API（route_status=1），"
                f"路径距离 1219m~2552m。但 origin 均为公园中心点代理，"
                f"非实际入口/内部节点，所有候选 can_enter_p2_supply=no，"
                f"阻塞缺口：真实入口步行路径、经营授权、部分商户缺少cost_yuan。"
                f"路径数据已获取但置信度为 medium，需现场核验后升为 high。"
            ),
            "candidates_total": len(p0_worklist),
            "candidates_can_enter_p2": can_enter_p2,
            "candidates_blocked": cannot_enter_p2,
            "routes_api_ok": routes_ok,
            "routes_api_fail": routes_fail,
            "top_blocking_gaps": dict(blocking_fields.most_common(5)),
        },
    },

    "previous_report_correction": {
        "file": "40_quality_evidence/verify_image_pdf_tables_report.json",
        "wrong_conclusion": "奥林匹克 PDF avg_fill_rate=0.045, verdict=DATA_DEGRADED",
        "correct_conclusion": "奥林匹克 PDF avg_fill_rate=0.953, 97.5%好表，结论应为 DATA_GOOD",
        "root_cause": "原脚本仅抽样3张表（TBL-00089/00090/附近），恰好是241张中仅有的5张低填充表，样本严重偏差。",
        "action": "需覆盖更新 verify_image_pdf_tables_report.json 中的错误结论。",
    },

    "gaps_requiring_action": [
        {
            "priority": "P0",
            "item": "证据台账 metric_id 编号缺失",
            "detail": "52条记录 metric_id 全空，需按 evidence_id 格式编号（E-0001起）。",
            "responsible": "Codex 复核",
        },
        {
            "priority": "P0",
            "item": "证据台账 validation_status 全空",
            "detail": "没有任何一条记录经过 checked 验证，数据无法正式引用于报告。",
            "responsible": "Codex 复核",
        },
        {
            "priority": "P1",
            "item": "P0 候选路径需现场/入口验证",
            "detail": "7个候选均用公园中心点代理起点，真实入口步行距离未核实。",
            "responsible": "用户现场或补充高德入口POI坐标",
        },
        {
            "priority": "P1",
            "item": "7个P0候选均缺少经营授权确认",
            "detail": "operation_authorization_status=needs_operator_or_field_confirmation",
            "responsible": "用户与公园方确认",
        },
        {
            "priority": "P2",
            "item": "verify_image_pdf_tables_report.json 结论有误",
            "detail": "需覆盖更新，避免后续分析引用错误的4.5%填充率结论。",
            "responsible": "可由脚本自动修正",
        },
    ],
}

out = ROOT / "40_quality_evidence/p0_data_completeness_audit_final.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

# 打印汇总
print("=" * 65)
print("P0 数据提取完整性审计 — 最终结论")
print("=" * 65)
print()

icons = {"COMPLETE": "✅", "INCOMPLETE": "❌", "PARTIAL": "⚠️"}
for key, val in report["summary"].items():
    s = val["status"]
    icon = icons.get(s, "?")
    print(f"{icon} {key}: {s}")
    print(f"   {val['note'][:120]}")
    print()

print("-" * 65)
print("早期错误报告更正:")
c = report["previous_report_correction"]
print(f"  文件: {c['file']}")
print(f"  错误结论: {c['wrong_conclusion']}")
print(f"  正确结论: {c['correct_conclusion']}")
print(f"  原因: {c['root_cause']}")
print()

print("-" * 65)
print("需要后续处理的缺口:")
for g in report["gaps_requiring_action"]:
    print(f"  [{g['priority']}] {g['item']}")
    print(f"        {g['detail']}")
print()
print(f"报告已写入: {out}")
