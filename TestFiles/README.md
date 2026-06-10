# TestFiles 自动化测试

本目录用于存放项目级自动化测试脚本和测试报告，不写入业务结论。

## 一键运行

```powershell
cd "<your-local-checkout>"
py TestFiles\run_all_tests.py
```

## 输出

- `TestFiles/reports/test_report.md`：中文测试报告。
- `TestFiles/reports/test_report.json`：机器可读测试结果。
- `TestFiles/reports/state_backup_*`：运行态备份。脚本结束会自动恢复这些文件，避免测试节点、测试上传、测试会话污染项目。

## 覆盖范围

- 后端：根据 FastAPI OpenAPI 清单覆盖全部接口。
- 前端：覆盖总览、资料导入、资料闭合、节点、地图、AI 工作台、报告页等主要交互。
- 跳转：逐项检查所有页面跳转入口是否可用，并核对入口文字与实际目标页面是否一致。
- 实时显示：上传资料、新增节点、新增分析对象、地图搜索和新建 AI 对话后，检查相关总览卡片、列表与计数是否同步变化。

## 环境

沿用当前机器 `py` 指向的 Python 环境，不切换 Python 版本。
前端测试优先使用系统 Chrome；未检测到 Chrome 时，回退到 Playwright Chromium。
