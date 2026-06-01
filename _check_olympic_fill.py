"""
check_olympic_fill.py - 检查奥林匹克 PDF 全部表格填充分布
"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:\Users\Yy199\Desktop\仿真设计")
JSONL = ROOT / "30_extraction/tables/pdf_native_tables.jsonl"

olympic_tables = []
green_tables = []

with JSONL.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        src = Path(rec["source_file"]).name
        rows = rec.get("rows", [])
        total_cells = rec["row_count"] * rec["column_count"]  # 用标称值
        non_empty = sum(1 for r in rows for c in r if str(c).strip())
        fill = round(non_empty / total_cells, 3) if total_cells else 0.0

        entry = {
            "id": rec["table_id"],
            "page": rec["page"],
            "rows": rec["row_count"],
            "cols": rec["column_count"],
            "fill": fill,
        }
        if "奥林匹克" in src:
            olympic_tables.append(entry)
        else:
            green_tables.append(entry)

# 分布直方图
def print_dist(name, tables):
    print(f"\n=== {name} ({len(tables)} 张) ===")
    buckets = Counter()
    for t in tables:
        if t["fill"] == 0:
            buckets["0.00"] += 1
        elif t["fill"] < 0.05:
            buckets["0.01-0.05"] += 1
        elif t["fill"] < 0.1:
            buckets["0.05-0.10"] += 1
        elif t["fill"] < 0.3:
            buckets["0.10-0.30"] += 1
        elif t["fill"] < 0.5:
            buckets["0.30-0.50"] += 1
        elif t["fill"] < 0.8:
            buckets["0.50-0.80"] += 1
        else:
            buckets["0.80-1.00"] += 1

    for k in ["0.00", "0.01-0.05", "0.05-0.10", "0.10-0.30", "0.30-0.50", "0.50-0.80", "0.80-1.00"]:
        cnt = buckets[k]
        bar = "#" * min(cnt, 40)
        print(f"  fill {k}: {cnt:4d}  {bar}")

    good = [t for t in tables if t["fill"] >= 0.5]
    print(f"\n  好表(≥0.5): {len(good)} 张")
    if good:
        print("  前10张样本:")
        for t in good[:10]:
            print(f"    {t['id']} page={t['page']} {t['rows']}x{t['cols']} fill={t['fill']}")

    # 实际平均
    avg = sum(t["fill"] for t in tables) / len(tables) if tables else 0
    print(f"  平均填充率: {avg:.3f}")

print_dist("奥林匹克森林公园", olympic_tables)
print_dist("城市绿心公园", green_tables)

# 奥林匹克 fill=0 的例子（看前5张）
zero_fill = [t for t in olympic_tables if t["fill"] == 0]
print(f"\n奥林匹克 fill=0 的表: {len(zero_fill)} 张")

# 检查 deep_extraction_audit 的逻辑是否有 bug
print("\n=== 检查 deep_extraction_audit 的 A2 计算 ===")
from collections import defaultdict
pdf_stats_audit = defaultdict(lambda: {"good": 0, "partial": 0, "empty": 0})

with JSONL.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        src = Path(rec["source_file"]).name
        rows = rec.get("rows", [])
        # audit 脚本用的是 sum(len(r)) 而非 row_count * col_count
        total_cells_actual = sum(len(r) for r in rows)
        non_empty = sum(1 for r in rows for c in r if str(c).strip())
        fill = round(non_empty / total_cells_actual, 3) if total_cells_actual else 0.0

        if fill >= 0.5:
            pdf_stats_audit[src]["good"] += 1
        elif fill > 0.05:
            pdf_stats_audit[src]["partial"] += 1
        else:
            pdf_stats_audit[src]["empty"] += 1

print("(audit脚本按实际rows长度计算fill)")
for pdf, s in pdf_stats_audit.items():
    total = s["good"] + s["partial"] + s["empty"]
    print(f"  {pdf[:30]}: total={total} good={s['good']} partial={s['partial']} empty={s['empty']}")
