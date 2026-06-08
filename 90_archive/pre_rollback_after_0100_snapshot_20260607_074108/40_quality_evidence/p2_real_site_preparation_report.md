# P2 真实资料准备报告

## 结论

- 本轮进入的是 `P2 准备`，不是完整仿真建模。
- 已对 `CAD图及其计划` 中的 DOCX、PDF、DWG 建立可追踪输入索引。
- DOCX 已完成文本抽取，可用于项目目标、策划内容、业态/节点/场景假设拆解。
- 北园 PDF 已完成文本抽取和页面画像，可作为北园 CAD 的可读代理。
- DWG 仅完成文件级登记和版本头识别，几何/图层解析状态保持 `pending_conversion`。
- 本轮 P2 主线不使用 PPT；PPT 后续仅在明确需要时作为弱假设或待核验线索。

## 输入资料

- 来源目录：`CAD图及其计划`
- 文件数：4
- 状态统计：{'extracted_local': 2, 'pending_conversion': 2}

## 抽取结果

- DOCX 文本：`30_extraction/p2_real_site/osen_project_plan_text.txt`，字符数 4046，非空行 183。
- DOCX 画像：`30_extraction/p2_real_site/osen_project_plan_profile.json`。
- PDF 文本：`30_extraction/p2_real_site/osen_north_cad_pdf_text.txt`，页数 1，可抽取文本总长度 1765。
- PDF 页面画像：`30_extraction/p2_real_site/osen_north_cad_pdf_pages.csv`。
- 资料目录：`40_quality_evidence/p2_real_site_source_catalog.csv`。
- P2 输入工作单：`70_outputs/processed_tables/p2_real_site_input_worklist.csv`，7 条。
- P2 仿真输入需求表：`70_outputs/processed_tables/p2_simulation_input_requirements.csv`，6 条。

## DWG 状态

- `奥森北园(字体放大)-改造建筑示意_t5.dwg`：header `AC1018`，版本 `AutoCAD 2004/2005/2006`，状态 `pending_conversion`。
- `奥森南园（字体放大）-改造建筑示意_t5.dwg`：header `AC1018`，版本 `AutoCAD 2004/2005/2006`，状态 `pending_conversion`。

## P2 使用边界

- 可以使用：DOCX 目标与策划文本、PDF 页面标签/文字、DWG 文件存在性和版本头。
- 暂不可使用：DWG 几何面积、图层、坐标、动线长度、建筑边界和南北园可比空间量。
- 仍需补充：可信 DWG 转换结果、节点/建筑/业态结构化表、真实客流/转化/收益/成本校准数据。
- 下一步建议：先做 DOCX 语义拆解和 PDF 页面对照复核，再决定是否安装/使用 DWG 转换器。
