"""
deep_extraction_audit.py
========================
P0 工作数据提取完整性深度审计

检查范围：
  A1  PDF 文本层全量内容质量（奥林匹克 + 城市绿心）
  A2  PDF 表格质量分层（好表 / 部分 / 空壳）
  A3  PPT 文本提取完整性（AI (1)(1).pptx 34MB + 奥森修改稿0306.pptx）
  A4  topic 分类覆盖（pdf_table_topic_draft_deepseek.csv）
  A5  证据台账覆盖（evidence_ledger.csv）
  A6  P0 路径数据完整性（amap_p0_route_results.csv）

输出：40_quality_evidence/deep_extraction_audit_report.json
"""
from __future__ import annotations
import csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

def audit_a1_pdf_text() -> dict:
    """A1: 检查 PDF 全文提取质量。"""
    results = {}
    for jf in sorted((ROOT / "30_extraction/pdf_text").glob("*.json")):
        data = json.loads(jf.read_text(encoding="utf-8"))
        pages = data.get("pages", data.get("page_texts", []))
        if not pages and "text" in data:
            # 平铺格式
            text = data["text"]
            results[jf.stem[:40]] = {
                "format": "flat",
                "total_chars": len(text),
                "chinese_chars": len(re.findall(r"[\u4e00-\u9fff]", text)),
                "numbers": len(re.findall(r"\d+\.?\d*%?", text)),
                "has_content": len(text) > 1000,
                "preview": text[:200].replace("\n", "↵"),
            }
            continue

        total_chars = 0
        chinese_count = 0
        number_count = 0
        page_samples = []
        for page in pages[:5]:
            txt = page.get("text", "") if isinstance(page, dict) else str(page)
            total_chars += len(txt)
            chinese_count += len(re.findall(r"[\u4e00-\u9fff]", txt))
            number_count += len(re.findall(r"\d+\.?\d*%?", txt))
            page_samples.append(txt[:100].replace("\n", "↵"))

        # estimate total from full data
        all_text = ""
        for page in pages:
            all_text += page.get("text", "") if isinstance(page, dict) else str(page)

        results[jf.stem[:40]] = {
            "format": "paged",
            "page_count": len(pages),
            "total_chars": len(all_text),
            "chinese_chars": len(re.findall(r"[\u4e00-\u9fff]", all_text)),
            "numbers": len(re.findall(r"\d+\.?\d*%?", all_text)),
            "has_content": len(all_text) > 5000,
            "page_samples": page_samples[:3],
        }

    return {"check": "A1_pdf_text_quality", "results": results}


def audit_a2_table_quality() -> dict:
    """A2: PDF 表格分层统计（好/部分/空壳）。"""
    jsonl = ROOT / "30_extraction/tables/pdf_native_tables.jsonl"
    if not jsonl.exists():
        return {"check": "A2_table_quality", "verdict": "FAIL", "error": "JSONL不存在"}

    pdf_stats: dict[str, Any] = defaultdict(lambda: {
        "total": 0, "good": 0, "partial": 0, "empty": 0,
        "good_tables": [], "partial_tables": [],
    })

    with jsonl.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = Path(rec["source_file"]).name
            rows = rec.get("rows", [])
            total_cells = sum(len(r) for r in rows)
            non_empty = sum(1 for r in rows for c in r if str(c).strip())
            fill = round(non_empty / total_cells, 3) if total_cells else 0.0

            pdf_stats[src]["total"] += 1
            entry = {
                "id": rec["table_id"],
                "page": rec["page"],
                "rows": rec["row_count"],
                "cols": rec["column_count"],
                "fill": fill,
                "first_row": [str(c)[:20] for c in (rows[0] if rows else [])][:5],
                "sample_data": [" | ".join(str(c)[:12] for c in r if str(c).strip())[:60]
                                for r in rows if any(str(c).strip() for c in r)][:3],
            }
            if fill >= 0.5:
                pdf_stats[src]["good"] += 1
                pdf_stats[src]["good_tables"].append(entry)
            elif fill > 0.05:
                pdf_stats[src]["partial"] += 1
                pdf_stats[src]["partial_tables"].append(entry)
            else:
                pdf_stats[src]["empty"] += 1

    summary = {}
    for pdf, s in pdf_stats.items():
        good_rate = round(s["good"] / s["total"], 3) if s["total"] else 0
        summary[pdf] = {
            "total": s["total"],
            "good_count": s["good"],
            "partial_count": s["partial"],
            "empty_count": s["empty"],
            "good_rate": good_rate,
            "verdict": "GOOD" if good_rate >= 0.3 else ("PARTIAL" if good_rate >= 0.1 else "MOSTLY_EMPTY"),
            "good_table_samples": s["good_tables"][:5],
            "partial_table_samples": s["partial_tables"][:3],
        }

    return {"check": "A2_table_quality", "summary": summary}


def audit_a3_ppt_text() -> dict:
    """A3: PPT 文本提取完整性。"""
    results = {}
    ppt_dir = ROOT / "30_extraction/ppt_text"
    raw_dir = ROOT / "20_raw_data/ppt"

    for jf in sorted(ppt_dir.glob("*.json")):
        data = json.loads(jf.read_text(encoding="utf-8"))
        slides = data.get("slides", [])

        all_text = ""
        for s in slides:
            all_text += s.get("text", "") + " "

        # 对应原始 PPT 大小
        raw_pptx = None
        for pf in raw_dir.glob("*.pptx"):
            if pf.stem[:10] in jf.stem or jf.stem[:10] in pf.stem:
                raw_pptx = pf
                break
        raw_mb = round(raw_pptx.stat().st_size / (1024 * 1024), 1) if raw_pptx else None

        chinese_count = len(re.findall(r"[\u4e00-\u9fff]", all_text))
        number_count = len(re.findall(r"\d+\.?\d*%?", all_text))

        # 文本密度：KB文本 / MB原始文件
        density = round(len(all_text) / 1024 / raw_mb, 2) if raw_mb else None

        # 抽样幻灯片
        samples = []
        for s in slides[:5]:
            txt = s.get("text", "").strip()
            if txt:
                samples.append({
                    "slide": s.get("slide_number"),
                    "text_len": len(txt),
                    "preview": txt[:100].replace("\n", "↵"),
                })

        # 判断是否充分：34MB PPT 只有 9.6KB 文本很可疑
        total_kb = round(len(all_text) / 1024, 1)
        suspicious = raw_mb is not None and (total_kb / raw_mb) < 1.0  # 每MB原始文件文本<1KB

        results[jf.name] = {
            "slide_count": len(slides),
            "total_text_kb": total_kb,
            "raw_pptx_mb": raw_mb,
            "text_density_kb_per_mb": density,
            "chinese_chars": chinese_count,
            "numbers": number_count,
            "suspicious_low_text": suspicious,
            "verdict": "SUSPICIOUS_INCOMPLETE" if suspicious else "OK",
            "note": f"每MB原始文件仅提取到 {density}KB 文本" if suspicious else "文本密度正常",
            "slide_samples": samples,
        }

    return {"check": "A3_ppt_text_quality", "results": results}


def audit_a4_topic_coverage() -> dict:
    """A4: DeepSeek 表格主题分类覆盖率。"""
    csv_path = ROOT / "30_extraction/tables/pdf_table_topic_draft_deepseek.csv"
    if not csv_path.exists():
        return {"check": "A4_topic_coverage", "verdict": "SKIP", "reason": "CSV不存在"}

    rows = []
    with csv_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {"check": "A4_topic_coverage", "verdict": "EMPTY"}

    total = len(rows)
    topic_counts: dict[str, int] = defaultdict(int)
    has_topic = 0
    for r in rows:
        topic = r.get("topic_draft", r.get("topic", "")).strip()
        if topic and topic not in ("", "null", "None"):
            has_topic += 1
            topic_counts[topic] += 1

    noise_count = topic_counts.get("empty_or_visual_noise", 0)
    business_count = total - noise_count

    return {
        "check": "A4_topic_coverage",
        "total_rows": total,
        "classified": has_topic,
        "coverage_rate": round(has_topic / total, 3),
        "noise_tables": noise_count,
        "business_tables": business_count,
        "topic_distribution": dict(sorted(topic_counts.items(), key=lambda x: -x[1])[:15]),
        "verdict": "OK" if has_topic / total >= 0.8 else "INCOMPLETE",
        "columns_found": list(rows[0].keys())[:10] if rows else [],
    }


def audit_a5_evidence_ledger() -> dict:
    """A5: 证据台账覆盖情况。"""
    ledger = ROOT / "40_quality_evidence/evidence_ledger.csv"
    if not ledger.exists():
        return {"check": "A5_evidence_ledger", "verdict": "FAIL", "error": "文件不存在"}

    rows = []
    with ledger.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {"check": "A5_evidence_ledger", "verdict": "EMPTY"}

    status_counts: dict[str, int] = defaultdict(int)
    source_counts: dict[str, int] = defaultdict(int)
    confidence_counts: dict[str, int] = defaultdict(int)

    for r in rows:
        status_counts[r.get("verification_status", "unknown")] += 1
        source_counts[r.get("source_type", "unknown")] += 1
        confidence_counts[r.get("confidence", "unknown")] += 1

    checked = status_counts.get("checked", 0)
    needs_review = status_counts.get("needs_review", 0)
    draft = status_counts.get("draft", 0)

    # 抽样几条具体数据
    samples = []
    for r in rows[:5]:
        samples.append({
            "id": r.get("evidence_id"),
            "indicator": r.get("indicator_name"),
            "value": r.get("value"),
            "unit": r.get("unit"),
            "status": r.get("verification_status"),
            "confidence": r.get("confidence"),
        })

    return {
        "check": "A5_evidence_ledger",
        "total_entries": len(rows),
        "status_distribution": dict(status_counts),
        "source_distribution": dict(source_counts),
        "confidence_distribution": dict(confidence_counts),
        "checked_count": checked,
        "needs_review_count": needs_review,
        "draft_count": draft,
        "sample_entries": samples,
        "verdict": "OK" if len(rows) >= 10 else "SPARSE",
    }


def audit_a6_p0_routes() -> dict:
    """A6: P0 候选路径数据完整性。"""
    routes_csv = ROOT / "50_external_gis/amap_routes/amap_p0_route_results.csv"
    raw_dir = ROOT / "50_external_gis/amap_routes/raw"

    if not routes_csv.exists():
        return {"check": "A6_p0_routes", "verdict": "FAIL", "error": "结果CSV不存在"}

    rows = []
    with routes_csv.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    raw_files = list(raw_dir.glob("*.json")) if raw_dir.exists() else []

    # 检查 P0 候选数量
    candidates = set()
    success_rows = []
    fail_rows = []
    for r in rows:
        cid = r.get("candidate_id", r.get("id", ""))
        candidates.add(cid)
        status = r.get("status", r.get("fetch_status", ""))
        if "ok" in status.lower() or "success" in status.lower() or status == "200":
            success_rows.append(r)
        else:
            fail_rows.append(r)

    # 样本
    samples = []
    for r in rows[:5]:
        samples.append({k: v for k, v in r.items() if v.strip()}[:8])

    return {
        "check": "A6_p0_routes",
        "total_candidates": len(candidates),
        "total_rows": len(rows),
        "raw_json_count": len(raw_files),
        "success_count": len(success_rows),
        "fail_count": len(fail_rows),
        "columns": list(rows[0].keys()) if rows else [],
        "sample_rows": rows[:3],
        "verdict": "OK" if len(success_rows) == len(rows) else "PARTIAL_FAILURE",
    }


def main():
    print("=== P0 数据提取完整性深度审计 ===\n")

    checks = []

    print("[A1] PDF 全文提取质量...")
    a1 = audit_a1_pdf_text()
    checks.append(a1)
    for k, v in a1["results"].items():
        icon = "✅" if v.get("has_content") else "❌"
        print(f"  {icon} {k[:35]} chars={v['total_chars']} zh={v['chinese_chars']} nums={v['numbers']}")

    print()
    print("[A2] 表格质量分层...")
    a2 = audit_a2_table_quality()
    checks.append(a2)
    for pdf, s in a2["summary"].items():
        icon = "✅" if s["verdict"] == "GOOD" else ("⚠️" if s["verdict"] == "PARTIAL" else "❌")
        print(f"  {icon} {pdf[:35]} 好={s['good_count']} 部分={s['partial_count']} 空={s['empty_count']} 好率={s['good_rate']}")

    print()
    print("[A3] PPT 文本提取完整性...")
    a3 = audit_a3_ppt_text()
    checks.append(a3)
    for fname, v in a3["results"].items():
        icon = "❌" if v.get("suspicious_low_text") else "✅"
        print(f"  {icon} {fname[:40]} slides={v['slide_count']} 文本={v['total_text_kb']}KB 原始={v['raw_pptx_mb']}MB 密度={v['text_density_kb_per_mb']}KB/MB")
        print(f"     → {v['note']}")

    print()
    print("[A4] 表格主题分类覆盖...")
    a4 = audit_a4_topic_coverage()
    checks.append(a4)
    print(f"  共 {a4.get('total_rows',0)} 行，分类率={a4.get('coverage_rate',0):.1%}，业务表={a4.get('business_tables',0)}，噪声={a4.get('noise_tables',0)}")

    print()
    print("[A5] 证据台账...")
    a5 = audit_a5_evidence_ledger()
    checks.append(a5)
    print(f"  共 {a5.get('total_entries',0)} 条  checked={a5.get('checked_count',0)} needs_review={a5.get('needs_review_count',0)} draft={a5.get('draft_count',0)}")

    print()
    print("[A6] P0 路径数据...")
    a6 = audit_a6_p0_routes()
    checks.append(a6)
    print(f"  候选={a6.get('total_candidates',0)} 成功={a6.get('success_count',0)} 失败={a6.get('fail_count',0)} 原始JSON={a6.get('raw_json_count',0)}")

    # 汇总结论
    problems = []
    if not all(v.get("has_content") for v in a1["results"].values()):
        problems.append("PDF文本层提取不完整")
    for pdf, s in a2["summary"].items():
        if s["verdict"] == "MOSTLY_EMPTY":
            problems.append(f"{pdf[:20]}...表格几乎全空(好率{s['good_rate']:.1%})")
    for fname, v in a3["results"].items():
        if v.get("suspicious_low_text"):
            problems.append(f"PPT {fname[:20]}...文本严重不足(密度{v['text_density_kb_per_mb']}KB/MB)")

    report = {
        "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_verdict": "PARTIAL_SUCCESS" if problems else "ALL_OK",
        "problems_found": problems,
        "checks": checks,
    }

    out = ROOT / "40_quality_evidence/deep_extraction_audit_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(f"总体评估: {report['overall_verdict']}")
    if problems:
        for p in problems:
            print(f"  ❌ {p}")
    else:
        print("  ✅ 所有数据提取完整")
    print(f"\n报告已写入: {out}")


if __name__ == "__main__":
    main()
