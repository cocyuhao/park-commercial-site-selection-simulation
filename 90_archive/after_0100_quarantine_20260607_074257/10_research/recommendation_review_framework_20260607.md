# 节点建议与报告评审框架补强（2026-06-07）

## 1. 为什么要重做节点建议表

当前 DOCX 的节点表已经能渲染，但建议颗粒度仍偏粗，容易让业务读者觉得像粗略方案。后续报告必须把每个节点拆成“依据、可选方案、推荐动作、定案条件、风险控制、复核动作”，而不是只给一句修改建议或神秘分数。

## 2. 已采用的本地方法约束

- 老板六份方法资料：状态对齐、行为程序、真实数据校准、微观/宏观双验证，不能让 LLM 直接给最终结论。
- 项目证据链：CAD/DWG、北园图纸 PDF、证据台账、高德 POI、策划书都分层使用；PPT/策划表述不能直接当强证据。
- 产品优先级方法：不只排序，要给分歧解释、置信度、工作量和下一步验证动作。

## 3. 官方与实践来源

- [HM Treasury The Green Book 2026](https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government/the-green-book-2026)：把节点判断拆成战略、经济/价值、商业、财务、管理五类问题；报告必须提供可选方案和推荐理由。
- [GOV.UK business case guidance for projects and programmes](https://www.gov.uk/government/publications/business-case-guidance-for-projects-and-programmes)：把当前报告定位成可迭代 business case，不把工作稿写成最终投资结论。
- [US National Park Service Commercial Services](https://www.nps.gov/subjects/concessions/index.htm)：公园商业服务必须服务游客体验和公共使用边界，不只追求商业收入。
- [Purdue OWL Abstracts and Executive Summaries](https://owl.purdue.edu/owl/subject_specific_writing/writing_in_engineering/handbook_on_report_formats/abstracts_and_executive_summaries.html)：执行摘要应自足、简洁、具体，不能把结论埋进机器式长段落。
- [University of Nottingham Business reports](https://www.nottingham.ac.uk/studyingeffectively/assessment/types/business.aspx)：商业报告应解释建议如何得出，帮助决策者快速找到信息。

## 4. 近年论文候选筛选

| 题名 | 年份 | 引用 | 用到哪里 |
|---|---:|---:|---|
| Industrial applications of large language models | 2025 | 104 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Generative spatial artificial intelligence for sustainable smart cities: A pioneering large flow model for urban digital twin | 2025 | 51 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Governance Networks in the Public Sector | 2025 | 24 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Hospitality Investment in the Afar Region, Ethiopia: Trends, Challenges, and Opportunities | 2025 | 4 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Tourism Management in National Parks: Development, Aspects, and Conceptual Framework | 2025 | 3 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Urban heat mitigation by green and blue infrastructure: Drivers, effectiveness, and future needs | 2024 | 208 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Index insurance and climate risk: prospects for development and disaster management | 2024 | 188 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Electric Vehicle Adoption: A Comprehensive Systematic Review of Technological, Environmental, Organizational and Policy Impacts | 2024 | 150 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Revolutionizing the food industry: The transformative power of artificial intelligence-a review | 2024 | 120 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Understanding food choice: A systematic review of reviews | 2024 | 106 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Generative AI in innovation and marketing processes: A roadmap of research opportunities | 2024 | 104 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| The digital transformation in pharmacy: embracing online platforms and the cosmeceutical paradigm shift | 2024 | 82 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Internet of Things: a comprehensive overview, architectures, applications, simulation tools, challenges and future directions | 2024 | 80 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Large Language Models for Intelligent Transportation: A Review of the State of the Art and Challenges | 2024 | 42 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Perceived Quality of Service in Tourist Transportation in the City of Baños de Agua Santa, Ecuador | 2024 | 20 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| Measuring the relationship between museum attributes and visitors: An application of topic model on museum online reviews | 2024 | 16 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |
| 6G autonomous radio access network empowered by artificial intelligence and network digital twin | 2024 | 9 | 用于校准 LLM agent、城市移动、选址选择、商业报告或多方案评审结构。 |

## 5. 落到报告的硬结构

每个节点必须至少写清：

1. 适合服务的人群状态：运动、亲子、文化、康养、夜间、通勤或游客。
2. 需求触发：口渴、疲劳、等待、拍照、活动前后、亲子照护、康复体验等。
3. 可选方案：低改造试点、标准运营、重资产/暂缓条件。
4. 推荐动作：先做什么、放在哪里、用什么运营形态、如何验证。
5. 定案条件：客流、转化、成本、审批、消防、资质、路径和控制点。
6. 风险控制：哪些内容不能先承诺，哪些应作为备选或折叠。
7. 会改变判断的证据：补到什么数据后，建议可能升级或降级。

## 6. 禁止继续使用的报告方式

- 不用裸分数当主结论。
- 不用一句“建议做咖啡/康养/文创”替代运营方案。
- 不把 POI/TGI 相关性写成收益结论。
- 不把 CAD 坐标写成高德坐标。
- 不把模型初稿、PPT 表达、热门 POI 表写成经营事实。
