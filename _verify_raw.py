import json, pathlib

JSONL = pathlib.Path(r"C:\Users\Yy199\Desktop\仿真设计\30_extraction\tables\pdf_native_tables.jsonl")
lines = [l for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
print(f"JSONL 总行数: {len(lines)}")

olym  = [json.loads(l) for l in lines if "奥林匹克" in json.loads(l)["source_file"]]
green = [json.loads(l) for l in lines if "绿心"   in json.loads(l)["source_file"]]
print(f"奥林匹克行数: {len(olym)}  绿心行数: {len(green)}  合计: {len(olym)+len(green)}")

first = json.loads(lines[0])
last  = json.loads(lines[-1])
print(f"第一条 table_id: {first['table_id']}  最后一条: {last['table_id']}")

# ---------- 全量填充率（raw 逐格计数）----------
def quality(records, label):
    good = part = empty = 0
    fills = []
    for rec in records:
        total = rec["row_count"] * rec["column_count"]
        nonempty = sum(1 for r in rec["rows"] for c in r if str(c).strip())
        fill = nonempty / total if total else 0.0
        fills.append(fill)
        if fill >= 0.5:   good  += 1
        elif fill > 0.05: part  += 1
        else:             empty += 1
    avg = sum(fills) / len(fills) if fills else 0
    print(f"{label}: 总={len(records)}, good={good}({good/len(records):.1%}), partial={part}, empty={empty}, 均值fill={avg:.3f}")
    # 抽查3张：最小fill, 最大fill, 中位
    sorted_r = sorted(zip(fills, records), key=lambda x: x[0])
    for tag, (f, r) in [("最小fill", sorted_r[0]), ("中位fill", sorted_r[len(sorted_r)//2]), ("最大fill", sorted_r[-1])]:
        row0 = " | ".join(str(c) for c in r["rows"][0]) if r["rows"] else ""
        row1 = " | ".join(str(c) for c in r["rows"][1]) if len(r["rows"])>1 else ""
        print(f"  [{tag}] {r['table_id']} p{r['page']} {r['row_count']}x{r['column_count']} fill={f:.3f}")
        print(f"         header: {row0[:80]}")
        print(f"         row1:   {row1[:80]}")

quality(olym,  "奥林匹克")
quality(green, "绿心")
