# 10_research/staging/

> 预装的免费开源依赖库
> 更新时间：2026-05-28
> Python 3.12+
> 总计: 128+ 个包

---

## 一、快速验证

```powershell
py -3.12 -c "import pandas, numpy, scipy, sklearn, folium, geopandas, fastapi, pydantic, rich; print('ALL OK')"
```

---

## 二、已安装包概览（按功能分类）

### 数据处理
| 包 | 版本 | 用途 |
|-----|------|------|
| pandas | 2.2.x | DataFrame |
| numpy | 1.26.x | 数组/矩阵 |
| scipy | 1.11.x | 科学计算 |
| scikit-learn | 1.8.0 | 机器学习 |
| statsmodels | - | 统计建模 |

### GIS & 地理
| 包 | 版本 | 用途 |
|-----|------|------|
| shapely | 2.0.x | 几何计算 |
| folium | 0.18.x | 地图生成 |
| geopandas | 0.14.x | GeoDataFrame |
| geopy | 2.4.1 | 地理编码 |
| haversine | - | 距离计算 |

### CAD & 可视化
| 包 | 版本 | 用途 |
|-----|------|------|
| ezdxf | 1.4.x | DWG读取 |
| matplotlib | 3.8.x | 绘图 |
| seaborn | 0.13.x | 统计绘图 |
| plotly | 6.7.0 | 交互图表 |

### 网络 & 优化
| 包 | 版本 | 用途 |
|-----|------|------|
| networkx | 3.6.x | 图网络 |
| deap | 1.4.x | 遗传算法 |
| pulp | 3.3.x | 线性规划 |
| ortools | 9.10.x | OR求解器 |
| sympy | 1.14.x | 符号计算 |

### 图像 & CV
| 包 | 版本 | 用途 |
|-----|------|------|
| Pillow | 12.1.x | 图像处理 |
| opencv-python | 4.13.x | 计算机视觉 |

### API & Web
| 包 | 版本 | 用途 |
|-----|------|------|
| fastapi | 0.115.x | Web API |
| uvicorn | 0.34.x | ASGI服务器 |
| requests | 2.32.x | HTTP客户端 |
| httpx | 0.28.x | 异步HTTP |

### 数据验证
| 包 | 版本 | 用途 |
|-----|------|------|
| pydantic | 2.10.x | 数据验证 |
| sqlalchemy | 2.0.x | ORM |

### 测试 & 日志
| 包 | 版本 | 用途 |
|-----|------|------|
| pytest | 8.3.x | 单元测试 |
| rich | 13.9.x | 富文本输出 |
| loguru | 0.7.3 | 日志 |

### 文本 & 爬虫
| 包 | 用途 |
|-----|------|
| beautifulsoup4 | HTML解析 |
| jinja2 | 模板引擎 |
| click | CLI框架 |

---

## 三、文件说明

| 文件 | 说明 |
|------|------|
| `requirements.txt` | 最小集（之前的版本）|
| `requirements_best.txt` | 推荐安装 |
| `requirements_comprehensive.txt` | 大全版（可能有兼容问题）|
| `requirements_full.txt` | 最全版 |
| `README.md` | 使用说明 |

---

## 四、自动调用说明

在 Claude Code 中，这些包会在运行时自动调用。使用示例：

```python
import pandas as pd
import numpy as np
import folium
import fastapi
```

不需要额外配置，直接 import 即可。

---

## 五、验证脚本

```powershell
py -3.12 -c "
import pandas; import numpy; import scipy
import sklearn; import folium; import geopandas
import shapely; import networkx; import ezdxf
import fastapi; import uvicorn; import pydantic
import matplotlib; import seaborn; import requests
import httpx; import pytest; import jinja2
import click; import tqdm; from PIL import Image
import cv2; import sympy; import geopy
print('ALL OK')
"
```

---

## 六、更新记录

- 2026-05-28: 从 20+ 包扩展到 128+ 包