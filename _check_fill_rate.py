"""
check_fill_rate.py - 检查填充率计算差异
"""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\Yy199\Desktop\仿真设计")
JSONL = ROOT / "30_extraction/tables/pdf_native_tables.jsonl"

target = {"TBL-00089", "TBL-00090", "TBL-00001", "TBL-00002", "TBL-00003"}
found = {}

with JSONL.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec["table_id"] in target:
            rows = rec.get("rows", [])
            total_cells_nominal = rec["row_count"] * rec["column_count"]
            total_cells_actual = sum(len(r) for r in rows)
            non_empty = sum(1 for r in rows for c in r if str(c).strip())
            fill_nominal = non_empty / total_cells_nominal if total_cells_nominal else 0
            fill_actual = non_empty / total_cells_actual if total_cells_actual else 0
            found[rec["table_id"]] = {
                "row_count": rec["row_count"],
                "col_count": rec["column_count"],
                "total_cells_nominal": total_cells_nominal,
                "total_cells_actual": total_cells_actual,
                "non_empty": non_empty,
                "fill_nominal": round(fill_nominal, 3),
                "fill_actual": round(fill_actual, 3),
                "rows_preview": rows[:3],
            }

for tid in sorted(found.keys()):
    d = found[tid]
    print(f"{tid}: rows={d['row_count']}x{d['col_count']}")
    print(f"  标称格={d['total_cells_nominal']}  实际rows中格数={d['total_cells_actual']}  非空={d['non_empty']}")
    print(f"  填充率_按标称={d['fill_nominal']}  填充率_按实际rows={d['fill_actual']}")
    for i, row in enumerate(d["rows_preview"]):
        print(f"  row[{i}] = {row}")
    print()
