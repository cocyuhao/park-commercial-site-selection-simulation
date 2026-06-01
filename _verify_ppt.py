import json
from pathlib import Path

for jf in sorted(Path(r"C:\Users\Yy199\Desktop\仿真设计\30_extraction\ppt_text").glob("*.json")):
    raw = json.loads(jf.read_text(encoding="utf-8"))
    slides = raw.get("slides", [])
    src = raw.get("source_file", "")
    slide_count_header = raw.get("slide_count")
    print("=== " + jf.name + " ===")
    print(f"  source_file        : {src}")
    print(f"  slide_count(header): {slide_count_header}  slides列表长度: {len(slides)}")
    total_chars = sum(
        s.get("text_length", len(s.get("text", "").strip())) for s in slides
    )
    print(f"  全部幻灯片合计字符 : {total_chars}")
    print()
    for s in slides:
        n   = s.get("slide", s.get("slide_number", "?"))
        tl  = s.get("text_length", len(s.get("text", "").strip()))
        txt = s.get("text", "").strip()
        snippet = txt[:60].replace("\n", "|")
        print(f"  Slide{n:2}: len={tl:4d}  [{snippet}]")
    print()
