# DeepSeek P2 真实资料覆盖细审

- 任务：LLM-020
- 模型：deepseek-v4-pro
- 输出状态：needs_review
- 覆盖结论：P2 structured outputs are partially covered; source documents have been extracted into text and planning semantics, but DWG geometry remains unparsed, and calibration-intensive inputs (visitor flow, revenue, cost, exact coordinates, layers) are still missing or placeholders, keeping the overall status as needs_review.

## 不能声称
- DWG几何已解析
- P3真实校准已完成
- P4完整仿真已完成
- PPT可回填缺口
- 候选评分是最终选址排序
- needs_review可当checked

## 下一步核验
- Execute DWG conversion for north and south park files and parse layer/geometry information.
- Obtain a readable CAD proxy (PDF or DXF) for the south park to verify spatial nodes.
- Collect real visitor flow data by entrance, node, and time for simulation calibration.
- Define and calibrate business format conversion rate assumptions with field or benchmark evidence.
- Secure revenue, cost, rent, and sharing parameters from operational plans or comparable cases.
- Validate operator authorization, lease feasibility, and construction/renovation permissions for each project node.
