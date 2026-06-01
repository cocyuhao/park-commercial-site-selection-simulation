# 后续阶段软件与技术学习议程

> 基于 `task_plan.md` 阶段路线图和 `00_control/p6_expert_website_design_brief.md` 工具路线生成
> 更新时间：2026-05-28

---

## 一、当前已验证安装的基础依赖

| 类别 | 库 | 版本 | 状态 |
|------|-----|------|------|
| 数据处理 | pandas, numpy | 已预装 | ✅ |
| 空间分析 | shapely | 已预装 | ✅ |
| PDF解析 | PyMuPDF, pdfplumber | 已预装 | ✅ |
| HTTP/网络 | requests, httpx | 已预装 | ✅ |
| AI/LLM | openai, tiktoken | 已预装 | ✅ |
| 科学计算 | scipy | 已预装 | ✅ |
| CAD转换 | ezdxf | 1.4.4 | ✅ 2026-05-28 |
| 图网络 | networkx | 3.6.1 | ✅ 2026-05-28 |
| 遗传算法 | deap | 1.4.4 | ✅ 2026-05-28 |
| 线性规划 | pulp | 3.3.2 | ✅ 2026-05-28 |

> **验证命令**: `py -3.12 -c "import ezdxf, networkx, deap, pulp; print('All loaded')"`

---

## 二、阶段进入预判与依赖

### P2 方法原型（进行中）

当前 P2 已完成方法原型闭环，产出了：
- `p2_persona_parameter_prototype.csv` - 游客分群参数
- `p2_demand_trigger_matrix.csv` - 需求触发矩阵
- `p2_supply_gap_scoring_formula.csv` - 缺口评分公式
- `p2_postman_api_contract_draft.csv` - API契约草案

**P2 需要的额外依赖**（如需完整跑通）：

| 软件 | 用途 | 安装方式 |
|-----|------|---------|
| `ezdxf` | DWG文件读取（非写入） | `pip install ezdxf` |
| `GDAL/OGR` | 矢量转换 | 需要手动安装wheel |
| `folium` | 简易地图生成（备选） | `pip install folium` |

### P3 真实公园接入

需要补的输入：
- DWG 几何解析（或 DXF/GeoJSON 格式转换）
- 真实客流数据接入
- 转化率/收益/成本参数校准

### P4 GIS 和仿真

| 软件 | 用途 | 安装方式 |
|-----|------|---------|
| `networkx` | 路径网络、最短路、中心性 | `pip install networkx` |
| `deap` | 遗传算法/粒子群优化 | `pip install deap` |
| `pulp` | 线性规划/选址优化 | `pip install pulp` |
| `playwright` | 浏览器自动化测试 | `pip install playwright` |
| `maplibregl` (JS) | 地图渲染（Web侧） | CDN引入 |

### P5 决策交付

| 软件 | 用途 | 安装方式 |
|-----|------|---------|
| `python-pptx` | 已安装 | PPT生成 |
| `weasyprint` | HTML转PDF | `pip install weasyprint` |
| `matplotlib` | 已安装 | 静态图表 |

### P6 专家网站化交付（见 p6_expert_website_design_brief.md）

| 软件 | 用途 | 安装方式 |
|-----|------|---------|
| Next.js | Web框架 | 需Node.js环境 |
| React | 组件库 | via Next.js |
| TypeScript | 类型安全 | via Next.js |
| shadcn/ui | UI组件 | npx命令 |
| Tailwind CSS | 样式 | via Next.js |
| MapLibre GL JS | 地图渲染 | CDN/npm |
| deck.gl | 大规模地理可视化 | CDN/npm |
| Apache ECharts | 数据图表 | CDN/npm |
| TanStack Table | 表格组件 | npm |
| Postman CLI | API测试 | 安装包 |
| FastAPI | 后端API | `pip install fastapi` |
| uvicorn | ASGI服务器 | `pip install uvicorn` |

---

## 三、优先学习清单（TODOs + 行动计划）

### 紧急度 P0：DWG/CAD 转换

当前两个 DWG 文件（南北园）状态为 `pending_conversion`。

**挑战**：
- DWG 是 Autodesk 专有格式，Python 只能读取，无法写入
- 需要 DXF 中转或直接获取 GeoJSON/DXF 导出

**解决方案**：
1. 首选：让用户在 AutoCAD 中手动导出为 DXF 或 GeoJSON
2. 备选：`ezdxf` 库读取 DXF（不需要 AutoCAD）
3. 备选：`gdal` 的 `ogr2ogr` 命令行转换

**行动计划**：
```powershell
# 安装 ezdxf
pip install ezdxf

# 尝试读取一个 DXF 示例
python -c "import ezdxf; print(ezdxf.__version__)"
```

### 紧急度 P1：MapLibre GL JS + deck.gl

后续 GIS 展示需要地图、热力、轨迹可视化。

**建议学习资源**：
- MapLibre GL JS Docs: https://maplibre.org/maplibre-gl-js/docs/
- deck.gl Docs: https://deck.gl/docs

**行动计划**：
- 先用 `folium` 做简易地图（已有 shapely 配合）
- 再迁移到 MapLibre/deck.gl 用于生产

### 紧急度 P2：Huff 模型 + 重力模型

用于 P2 人群概率原型。

**模型原理**：
- Huff模型：基于距离的业态吸引力模型
- 重力模型：基于人口/距离的交互引力

**行动计划**：
```python
# scikit-learn 或 scipy 已有概率分布支持
from scipy import stats
# 幂函数衰减
def huff_attraction(distance, alpha):
    return distance ** (-alpha)
```

### 紧急度 P3：选址优化算法

最大覆盖选址模型（Maximum Coverage Location Problem, MCLP）。

**工具**：`pulp` (PuLP) 是最简单的选择

**行动计划**：
```powershell
pip install pulp

# MCLP 示例
from pulp import *
```

### 紧急度 P4：FastAPI + Postman CLI

P2 Postman 契约草案需要变成可执行的 API。

**行动计划**：
```powershell
pip install fastapi uvicorn
# 创建第一个 API
# python -c "from fastapi import FastAPI; print('ok')"
```

---

## 四、按阶段依赖关系汇总

```
P2 ——P3(需DWG转换)—— P4(GIS+仿真) —— P5(交付报告) —— P6(网站化)
 |    |                |             |              |
 v    v                v             v              v
ezdxf    网络x/deap    Folium       python-pptx    Next.js
shapely  pulp        MapLibre     matplotlib    React
         蒙特卡洛     deck.gl                    Tailwind
         simulation  ECharts                    FastAPI
                                             Postman
```

---

## 五、安装验证批处理脚本

后续进入下一阶段前，可以运行以下检查：

```powershell
# 数据分析验证
python -c "import pandas; import numpy; import shapely; print('Data OK')"

# PDF解析验证
python -c "import PyMuPDF; import pdfplumber; print('PDF OK')"

# 科学计算验证
python -c "import scipy; print('SciPy OK')"

# API框架验证
python -c "import fastapi; import uvicorn; print('API OK')"

# 优化求解验证
python -c "import pulp; print('PuLP OK')"
```

---

## 六、后续补装依赖清单

建议在进入 P3/P4 前一次性安装：

```powershell
pip install ezdxf networkx deap pulp folium fastapi uvicorn playwright weasyprint
```

注意：
- `GDAL` 需要 wheel 手动安装
- `playwright` 安装后需要 `playwright install`
- 前端部分需要 Node.js + npm