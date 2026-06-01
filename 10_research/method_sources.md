# 方法和资料来源摘要

## 高德 Web 服务

- 搜索 POI 2.0：用于关键字、周边、多边形和 ID 搜索。项目中用于园内外商业供给、竞品和业态补数。  
  来源：https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch

- 地理/逆地理编码：用于把目标公园名称、地址、候选点地址转为坐标，也可把坐标转地址。  
  来源：https://lbs.amap.com/api/webservice/guide/api/georegeo

- 路径规划：用于计算候选点、入口、活动区、竞品之间的步行距离和时间。  
  来源：https://lbs.amap.com/api/webservice/guide/api/direction

## 选址和需求模型

- Huff 模型：用于用吸引力和距离衰减估算消费者选择某商业设施的概率。  
  来源：https://ideas.repec.org/a/uwp/landec/v39y1963i1p81-90.html

- 最大覆盖选址问题 MCLP：用于有限候选点中选择能覆盖最大需求的点位组合。  
  来源：https://cir.nii.ac.jp/crid/1362262946026100736

## 仿真技术

- Agent-Based Modeling：用于模拟不同游客类型在公园内的路径、消费、放弃和外溢。  
  参考：https://www.mdpi.com/2071-1050/13/16/9268

- Mesa：Python Agent-Based Modeling 框架。  
  来源：https://mesa.readthedocs.io/en/stable/

- SimPy：离散事件仿真框架，可用于排队、服务能力和等待时间。  
  来源：https://simpy.readthedocs.io/

- OR-Tools：可用于整数规划和约束优化，服务候选点组合优化。  
  来源：https://developers.google.com/optimization/cp/cp_solver

## 使用规则

- 这些资料是方法基线，不等于项目结论。
- 任何外部资料用于报告时，必须记录访问日期、用途和局限。
