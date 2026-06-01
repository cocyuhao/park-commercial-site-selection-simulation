import fitz, pathlib, sys

pdf_path = pathlib.Path("20_raw_data/pdf/奥林匹克森林公园区域大数据分析报告-20241230-202512291772157987.pdf")
pdf = fitz.open(str(pdf_path))
for i in [0, 1, 2, 5, 10, 20, 50]:
    page = pdf[i]
    text = page.get_text().strip()
    imgs = page.get_images()
    tables = []
    try:
        tables = page.find_tables().tables
    except Exception:
        pass
    text_preview = text[:60].replace("\n", "|") if text else "(empty)"
    print(f"Page {i+1}: imgs={len(imgs)}, tables_found={len(tables)}, text_len={len(text)}, preview={text_preview!r}")
