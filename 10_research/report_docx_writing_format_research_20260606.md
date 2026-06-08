# DOCX 商业报告写作格式吸收记录（2026-06-06）

## 目的

本记录用于约束 `奥森商业改造综合评估与修正建议工作稿` 的 DOCX 导出格式。它不是报告正文的一部分，而是内部写作和排版依据，避免最终文件继续像机器日志或旧模板。

## 外部资料吸收

1. HM Treasury / GOV.UK `The Green Book (2026)`
   - 链接：https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026
   - 吸收点：采用五类视角作为判断框架：战略、经济/价值、商业、财务、管理。对本项目不照搬政府模板，但把节点判断拆成“定位是否成立、价值逻辑、商业可行、成本收益边界、落地管理”。

2. GOV.UK `Business case guidance for projects and programmes`
   - 链接：https://www.gov.uk/government/publications/business-case-guidance-for-projects-and-programmes
   - 吸收点：工作稿必须是可迭代的 business case，不把初版写成最终结论；在 DOCX 中保留“使用边界”和“待补资料”。

3. UMGC Effective Writing Center `Executive Summary`
   - 链接：https://www.umgc.edu/current-students/learning-resources/writing-center/writing-resources/professional-and-presentation/executive-summary
   - 吸收点：执行摘要要能独立阅读，包含目的、问题、分析方法、结果、建议；建议尽量用列表，避免引用正文表格。

4. Purdue OWL `Abstracts and Executive Summaries`
   - 链接：https://owl.purdue.edu/owl/subject_specific_writing/writing_in_engineering/handbook_on_report_formats/abstracts_and_executive_summaries.html
   - 吸收点：摘要不要把方法、结果和建议埋在长段落里；要完整、简洁、具体、自足。

5. University of Nottingham `Business reports`
   - 链接：https://www.nottingham.ac.uk/studyingeffectively/assessment/types/business.aspx
   - 吸收点：商业报告应帮助决策者快速找到信息，并解释建议如何得出；结构包含 executive summary、introduction/background、methodology、results/discussion、recommendations、appendices。

6. Massey University `Business report structure`
   - 链接：https://www.massey.ac.nz/study/study-and-assignment-support-and-guides/types-of-assignments/report/business-report-structure/
   - 吸收点：商业报告需要分析现实情况、权衡方案、得出结论并提供后续行动；风格应简洁，必要时用编号、表格和清单代替长篇散文。

## 应用到本项目的结构

- 封面：报告名、对象、版本、状态边界。
- 执行摘要：一页内读完，写“现在能确认什么 / 不应直接定案什么 / 本轮建议怎么推进”。
- 关键依据：列项目资料、CAD 锚点、客流消费证据，不堆技术日志。
- 节点判断：六个节点按“原计划理解、修正建议、定案前资料”呈现；不使用裸分数。
- 综合修改意见：按南门簇、北园轻活动点、康养/国医资质边界、Live House 降级等组织。
- 仿真与定案边界：明确哪些可以做、哪些不能宣称、哪些必须补齐。
- 当前推进事项：用可执行动作，不写空泛建议。
- 附录：证据摘要、CAD 锚点、数据来源，不把 backend/debug/API 字段放给读者。

## DOCX 视觉预设

- 采用 Documents skill 的 `standard_business_brief` 作为基础。
- 中文商业交付做命名覆盖：A4 页面，2.54cm 页边距，正文使用微软雅黑/等线兼容字体，标题使用深蓝强调。
- 表格只用于真正需要比较的内容：节点表、证据表、CAD 锚点表。长段落不塞进窄表格。
- 使用真实 Word 标题样式、列表样式和表格几何；避免假标题、假项目符号和机器字段。

## 禁止项

- 不出现 `needs_review`、`not_final`、`payload`、`debug`、`traceback`、`ConnectError`。
- 不把 DeepSeek、API contract、smoke test 当客户正文。
- 不写最终 ROI、最终排名、最终收益。
- 不把 CAD 坐标直接写成高德坐标；必须写明仍需控制点校准。
