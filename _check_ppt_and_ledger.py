"""
check_ppt_and_ledger.py - PPT 完整性 + 证据台账 + P0 路径数据
"""
import json, csv
from pathlib import Path
import re

ROOT = Path(r"C:\Users\Yy199\Desktop\仿真设计")

# ---- PPT 内容详查 ----
print("=" * 60)
print("PPT 文本提取详查")
print("=" * 60)

for jf in sorted((ROOT / "30_extraction/ppt_text").glob("*.json")):
    data = json.loads(jf.read_text(encoding="utf-8"))
    slides = data.get("slides", [])
    raw_name = jf.stem

    # 对应原始 PPT 大小
    raw_mb = None
    for pf in (ROOT / "20_raw_data/ppt").glob("*.pptx"):
        if pf.stem[:6] in jf.stem or jf.stem[:6] in pf.stem:
            raw_mb = round(pf.stat().st_size / (1024 * 1024), 1)
            break

    print(f"\n【{raw_name[:30]}】原始文件={raw_mb}MB  幻灯片={len(slides)}张")

    total_text_len = 0
    for s in slides:
        txt = s.get("text", "").strip()
        total_text_len += len(txt)

    print(f"  总提取文本: {total_text_len} 字符 ({total_text_len/1024:.1f}KB)")

    # 每张幻灯片的文本情况
    print("  幻灯片详情:")
    for s in slides:
        txt = s.get("text", "").strip()
        n = s.get("slide_number", "?")
        title = s.get("title", "")
        cn = len(re.findall(r"[\u4e00-\u9fff]", txt))
        num = len(re.findall(r"\d+\.?\d*%?", txt))
        snippet = txt[:60].replace("\n", "↵") if txt else "(空)"
        print(f"    Slide {n:2}: len={len(txt):4d} zh={cn:3d} num={num:3d} | {snippet}")

# ---- 证据台账状态 ----
print("\n" + "=" * 60)
print("证据台账详查 (前15条)")
print("=" * 60)

ledger = ROOT / "40_quality_evidence/evidence_ledger.csv"
with ledger.open(encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"字段: {list(rows[0].keys()) if rows else 'N/A'}")
print(f"总条数: {len(rows)}")

from collections import Counter
status_cnt = Counter(r.get("verification_status", "") for r in rows)
confidence_cnt = Counter(r.get("confidence", "") for r in rows)
source_cnt = Counter(r.get("source_type", "") for r in rows)

print(f"verification_status 分布: {dict(status_cnt)}")
print(f"confidence 分布: {dict(confidence_cnt)}")
print(f"source_type 分布: {dict(source_cnt)}")

print("\n前15条数据:")
for r in rows[:15]:
    print(f"  [{r.get('evidence_id')}] {r.get('indicator_name','')[:30]} | {r.get('value','')} {r.get('unit','')} | {r.get('verification_status','')} | {r.get('confidence','')} | {r.get('source_type','')[:20]}")

# ---- P0 路径结果 ----
print("\n" + "=" * 60)
print("P0 路径数据")
print("=" * 60)

routes_csv = ROOT / "50_external_gis/amap_routes/amap_p0_route_results.csv"
if routes_csv.exists():
    with routes_csv.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rrows = list(reader)
    print(f"字段: {list(rrows[0].keys()) if rrows else []}")
    print(f"共 {len(rrows)} 行")
    for r in rrows:
        print(f"  {r}")
else:
    print("文件不存在!")

# P0 跟进清单
p0_worklist = ROOT / "70_outputs/processed_tables/poi_supply_p0_followup_worklist.csv"
if p0_worklist.exists():
    with p0_worklist.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        wrows = list(reader)
    print(f"\nP0候选清单 ({p0_worklist.name}): 共{len(wrows)}行")
    print(f"字段: {list(wrows[0].keys()) if wrows else []}")
    for r in wrows[:5]:
        print(f"  {r}")
