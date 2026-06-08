# 仿真任务入口补充学习与依据加固（2026-06-05）

> 状态：主线补强记录。  
> 触发原因：用户指出当前实现看起来仍可能像“空想”，要求先补充资料学习，再继续推进。  
> 适用范围：只约束“策划文案 + CAD/空间资料 + 人物仿真任务入口 + DeepSeek 受限角色”，不宣称完整仿真已完成。

## 1. 当前判断

继续推进前必须先承认边界：

- 本地已经有真实资料线索：证据台账、PDF 表格、高德 POI、园内复核工单、奥森策划 DOCX、CAD/DWG/PDF 图纸、老板六份方法资料。
- 这些资料可以支撑“运行前预检”和“对象组合”，但还不足以支撑完整人物仿真结论。
- 因此当前正确动作不是直接生成最终报告，而是让平台先做到：选择对象、说明依据、暴露缺口、阻止完整仿真误声明。

## 2. 补充资料吸收

| 来源 | 年份 | 关键启发 | 对本项目的落点 |
|---|---:|---|---|
| MobileCity: An Efficient Framework for Large-Scale Urban Behavior Simulation | 2026 | 大规模城市行为仿真不能只靠静态画像；需要需求、习惯、义务随时间演化，并用异步批处理和低 token 通信降低成本。 | DeepSeek 不能逐游客实时调用；后续采用批处理、缓存、本地生成器和对象级预检。 |
| M2LSimu: Guiding LLM-Based Human Mobility Simulation with Mobility Measures from Shared Data | 2026 | 个体轨迹独立生成会丢失群体层行为；共享数据和群体移动指标要反向约束个体 prompt。 | 预检必须要求时段客流、路线观察、停留和转化等宏观验证目标；没有这些不能说完整仿真。 |
| MobCache: Mobility-Aware Cache Framework | 2026 | LLM 移动仿真成本高，需要可重构缓存支持大规模模拟。 | DeepSeek 任务后续必须接缓存、队列、429 退避和任务级 trace；不是每个游客每一步问模型。 |
| GTA: Generative Traffic Agents | 2026 | 使用 persona-based agents 做活动日程和交通选择，也要对照真实数据验证。 | 本项目的人群状态、行为程序和选择概率只能先做候选；最终要用真实数据回放校准。 |
| GATSim: Urban Mobility Simulation with Generative Agents | 2025/2026 | 生成式移动 agent 要有认知结构、记忆、计划、反应和交通/空间环境耦合。 | 当前对象池必须继续从“标签”升级到状态、行为程序、空间语境、选择概率和验证目标组合。 |
| HumanLM | 2026 | 用户模拟应对齐潜在状态，而不是只模仿表面回答。 | 人群画像要保留目的、疲劳、时间压力、预算、同行、绕行和排队容忍；报告不能只写“像人”的话。 |
| Towards a foundational platform for generative agents in simulated city environment | 2026 | LLM agent 需要 grounded urban environment，不是脱离城市环境的文本聊天。 | 策划文案、CAD/图纸、POI、地图目标和验证目标要进入同一对象链。 |
| Urban planning in the era of large language models | 2025 | LLM 适合作为规划师助手，用于概念、设计和评估，但不能替代规划师责任。 | 专家 AI 工作台应协助综合、解释、找缺口、写工作稿；不能直接替用户下最终判断。 |
| Designing meaningful human oversight in AI | 2026 | 要区分 AI 的解决方案生成能力与人的评估、质疑、覆盖能力。 | 采用/放弃/锁定/生成报告/运行仿真都必须保留人工评估权，不能被 AI 自动覆盖。 |
| LSDTs: LLM-Augmented Semantic Digital Twins | 2025/2026 | LLM 可把非结构化规划资料组织成语义层，再服务数字孪生和仿真。 | 奥森策划文案应该先转成节点、业态、约束、证据引用和待复核对象，再进仿真。 |
| Urban traffic digital twin system development in Unity | 2025 | 高保真空间系统要融合 GIS/BIM/多源数据，并处理交互和计算效率。 | 当前 CAD/DWG 只登记为资料；未完成可信转换和空间校准前，不得宣称路线、面积或容量已闭合。 |
| Human-Centric Digital Twins for Spatial Sustainability | 2026 | 行为模型常受数据稀缺影响，需要把观察到的行为模式翻译成 agent 规则。 | 当前必须把“缺真实行为观察”显式标成阻止项，不能用 AI 常识填空。 |

## 3. 对当前实现的修正

刚才新增的“仿真任务入口”可以保留，但必须以更保守的口径存在：

1. 它是 `preflight`，不是 `simulation result`。
2. 它只能组合四类对象：`persona_state`、`behavior_program`、`choice_probability`、`simulation_validation_target`。
3. 它必须显示本地资料用途：证据台账、PDF 表格、POI、园内复核、奥森策划、CAD/图纸、老板资料。
4. 它必须明确：完整仿真被阻止，除非真实校准数据和 P3 门禁闭合。
5. 它必须保留生产端 DeepSeek-only：最终网站只允许 DeepSeek 做候选、解释、工作稿，不嵌入 Codex。
6. 它不能把策划文案、CAD、POI 和老板资料混成一种“万能证据”。每类资料都有不同用途。

## 4. 终局报告的正确路径

用户希望最后由平台基于策划文案和 CAD 图跑出一份高质量结果。正确路径应是：

1. `奥森重点项目策划思路20260521.docx` 转成节点、业态、合作模式、活动场景和待复核约束。
2. CAD/DWG/PDF 图纸转成可核对空间对象：建筑位置、面积、入口、路径、边界、容量或至少可信几何备注。
3. 证据台账/PDF 表格提供客流、TGI、热门到访、时段等背景指标。
4. 高德 POI 提供外部供给和竞品线索。
5. 人群状态和行为程序描述为什么来、怎么走、何时停、何时买、何时放弃。
6. 选择概率只输出优先级、解释、敏感缺口和建议动作，不输出伪精确最终概率。
7. 验证目标检查客流、路线、停留、转化、授权和收益成本。
8. 报告只在这些链路被平台回放后生成，不由 Codex 在系统外手写。

## 5. 当前下一步

- 保留并强化 `90_p6_expert_dashboard` 的仿真任务入口。
- 把 QA 固化为证据：`simulation_task_entry_preflight_validation_20260605`。
- 下一轮继续补：策划文案 -> 节点/业态对象；CAD/图纸 -> 空间待转换对象；DeepSeek 队列/缓存/trace。
- 不进入最终报告，直到平台能回放上述链路。

## 6. 参考链接

- MobileCity: https://aclanthology.org/2026.eacl-industry.21/
- M2LSimu: https://arxiv.org/abs/2602.16726
- MobCache: https://arxiv.org/abs/2602.16727
- GTA: https://arxiv.org/abs/2601.16778
- GATSim: https://arxiv.org/abs/2506.23306
- HumanLM: https://humanlm.stanford.edu/HumanLM_paper.pdf
- Urban Generative Intelligence platform: https://journals.plos.org/complexsystems/article?id=10.1371/journal.pcsy.0000093
- Urban planning with LLMs: https://www.nature.com/articles/s43588-025-00846-1
- Meaningful human oversight: https://link.springer.com/article/10.1007/s43681-026-01147-7
- LSDTs: https://arxiv.org/abs/2508.06799
- Urban traffic digital twin system: https://www.nature.com/articles/s41598-025-23943-7
- Human-centric digital twins: https://www.mdpi.com/2071-1050/18/3/1482
