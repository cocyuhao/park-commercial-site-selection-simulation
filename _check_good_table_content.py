"""
check_good_table_content.py - 抽样验证"好表"实际内容
"""
import json
from pathlib import Path
import random

ROOT = Path(r"C:\Users\Yy199\Desktop\仿真设计")
JSONL = ROOT / "30_extraction/tables/pdf_native_tables.jsonl"

olympic_good = []
green_good = []

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
        rec["_fill"] = fill

        if fill >= 0.5:
            if "奥林匹克" in src:
                olympic_good.append(rec)
            else:
                green_good.append(rec)

random.seed(42)

def show_sample(name, tables, n=10):
    sample = random.sample(tables, min(n, len(tables)))
    sample.sort(key=lambda x: int(x["table_id"].split("-")[1]))
    print(f"\n=== {name} 好表随机抽样 {len(sample)} 张 (共{len(tables)}张) ===")
    for rec in sample:
        rows = rec.get("rows", [])
        print(f"\n  {rec['table_id']} page={rec['page']} {rec['row_count']}x{rec['column_count']} fill={rec['_fill']}")
        # 显示前5行
        for i, row in enumerate(rows[:5]):
            # 显示非空单元格
            non_empty_cells = [str(c)[:15] for c in row if str(c).strip()]
            if non_empty_cells:
                print(f"    row[{i}]: {' | '.join(non_empty_cells)}")
        if rec["row_count"] > 5:
            print(f"    ... (共{rec['row_count']}行)")

show_sample("奥林匹克森林公园", olympic_good)
show_sample("城市绿心公园", green_good)

# 统计内容类型
print("\n\n=== 内容类型分析 ===")
for name, tables in [("奥林匹克", olympic_good), ("城市绿心", green_good)]:
    has_chinese = 0
    has_pct = 0
    has_number = 0
    all_single_vals = 0
    for rec in tables:
        rows = rec.get("rows", [])
        all_text = " ".join(str(c) for r in rows for c in r)
        if any("\u4e00" <= c <= "\u9fff" for c in all_text):
            has_chinese += 1
        if "%" in all_text:
            has_pct += 1
        import re
        if re.search(r"\d+\.?\d+", all_text):
            has_number += 1
        # 3x3以下、单值表（可能是单个数字框）
        if rec["row_count"] <= 3 and rec["column_count"] <= 3:
            all_single_vals += 1

    total = len(tables)
    print(f"\n{name} ({total}张好表):")
    print(f"  含中文: {has_chinese} ({has_chinese/total:.1%})")
    print(f"  含%:    {has_pct} ({has_pct/total:.1%})")
    print(f"  含数字: {has_number} ({has_number/total:.1%})")
    print(f"  3x3以下小表: {all_single_vals} ({all_single_vals/total:.1%})")

# 检查 3x3 小表内容（奥林匹克大量fill=1.0 的 11x3/3x3）
print("\n\n=== 奥林匹克 3x3 以下表格样本 ===")
small = [t for t in olympic_good if t["row_count"] <= 4 and t["column_count"] <= 3][:10]
for rec in small:
    print(f"\n  {rec['table_id']} p{rec['page']} {rec['row_count']}x{rec['column_count']}")
    for row in rec["rows"]:
        non_empty = [str(c)[:20] for c in row if str(c).strip()]
        if non_empty:
            print(f"    {non_empty}")

print("\n\n=== 奥林匹克 11x3 表格样本 ===")
med = [t for t in olympic_good if t["row_count"] == 11 and t["column_count"] == 3][:3]
for rec in med:
    print(f"\n  {rec['table_id']} p{rec['page']} {rec['row_count']}x{rec['column_count']}")
    for row in rec["rows"]:
        non_empty = [str(c)[:20] for c in row if str(c).strip()]
        if non_empty:
            print(f"    {non_empty}")
