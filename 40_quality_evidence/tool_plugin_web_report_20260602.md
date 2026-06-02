# 2026-06-02 工具 / 插件 / 网页使用与验证报告

本报告用于同步给同事，记录本轮为了修复专家 AI 工作台、空间地图、资料池和总览跳转所实际使用的软件、插件、网页和验证方法。所有 API Key 均只按“已配置/未配置”记录，不写入完整值。

## 实际使用的工具与网页

| 类别 | 名称 | 用途 | 产物 / 证据 |
|---|---|---|---|
| Git / GitHub | Git CLI + GitHub 远端 `cocyuhao/park-commercial-site-selection-simulation` | 同步远端 main 到本地，确认基线为同事最新代码 | 本地 HEAD 已同步到 `74b6aeb` |
| 高德官方网页 | 高德地图 JS API / Web Service 文档与接口 | 学习并改造为可拖拽、可缩放的 JS 地图；Web Service 只作检索补充 | `/api/amap/js-config`、`/api/amap/context` |
| 豆包官网 | `https://www.doubao.com/chat/` | 实际打开学习网页端 AI 工作台布局、输入框、工具条、留白 | `doubao_live_reference_20260602.png/json` |
| Codex 工作台参考 | 用户提供的 Codex 实际截图 + 当前 Codex 会话结构 | 学习项目分组、历史会话、新对话、底部输入和交付动作位置 | `selenium_ai_sessions_report_20260602.png/json` |
| Selenium | Python Selenium 4.44.0 + Chrome | 模拟用户 5 轮点击全界面、地图搜索、AI 快捷工具 | `selenium_ui_roundtrip_20260602.json/png` |
| Chrome | Headless Chrome | 视觉截图和 DOM 状态读取 | `selenium_ai_doubao_style_20260602.png` |
| Python 3.12 | `py -3.12` | 后端语法检查、健康脚本、Selenium 脚本 | 多项命令 PASS |
| Node.js | `node --check` | 前端 JS 语法检查 | `90_p6_expert_dashboard/static/app.js` PASS |
| DeepSeek API | 项目健康验证脚本 | 4 种方式验证 LLM 链路 | `verify_deepseek_api_report.json` PASS |
| PDF 表格验证 | PyMuPDF + pdfplumber | 4 种方式验证 329 张 PDF 表格质量 | `verify_pdf_tables_report.json` PASS |
| 高德 Web Service | 项目烟雾脚本 | 验证高德检索服务可用 | `50_external_gis/amap_smoke_tests/amap_smoke_test_latest.json` |

## 本轮验证方法

1. Git 同步验证：本地基线同步到远端 main 最新提交 `74b6aeb`。
2. 前端语法验证：`node --check 90_p6_expert_dashboard/static/app.js` 通过。
3. 后端语法验证：`py -3.12 -m py_compile 90_p6_expert_dashboard/app.py` 通过。
4. Dashboard API：`GET /api/dashboard` 返回 200。
5. 高德 JS 配置 API：`GET /api/amap/js-config` 返回 200，记录为已配置。
6. 上传资料 API：`GET /api/uploads` 返回 200。
7. DeepSeek 健康验证：4/4 PASS。
8. PDF 表格质量验证：4/4 PASS。
9. 高德烟雾测试：`run_amap_smoke_test.py` 输出 `status=ok`。
10. Selenium 全路径回归：5 轮、98 个动作、0 个失败。
11. 旧问题文案扫描：`默认不锁定 N-001`、`外部预览`、`仅地图预览`、`后端草案分` 均不再出现在核心前端/后端文件。
12. 人工视觉复核：查看豆包官网截图、AI 工作台截图、地图截图，确认 AI 输入区、留白、工具条和地图 loading 状态已改。
13. AI 会话链路验证：新建项目会话、发送中文需求、写入历史记录、生成报告文件，证据为 `ai_session_report_api_test_20260602.json`。
14. AI 工作台视觉验证：Selenium 确认页面存在项目列表、历史列表、新对话按钮、生成报告按钮和当前聊天内容，证据为 `selenium_ai_sessions_report_20260602.png/json`。
15. 最终报告按钮复核：Selenium 打开 `/#ai` 后确认“新对话”和“生成报告”可见，输入框可见，页面不含固定 `N-001 桃花源白房子`，证据为 `selenium_final_report_button_20260602.png/json`。

## 关键修复结论

- 专家 AI 工作台不再默认锁定 N-001；普通入口进入“项目综合分析”，只有明确点击节点按钮才分析当前节点。
- AI 工作台已参考豆包真实网页端，改为中央阅读区、底部居中大输入框、输入框内快捷工具条。
- AI 工作台已参考 Codex 的项目化工作流，新增项目分组、历史会话、新对话和“生成报告”按钮。
- “生成报告”按钮放在当前对话标题区右侧；AI 回复过程中禁用，生成后保存到 `80_delivery/ai_chat_reports/`。
- 概览节点跳转已修复，点击不同节点会带着具体 `node_id` 进入节点清单。
- “外部预览 / 仅地图预览”等面向内部的说法已替换为“位置参考 / 仅看位置关系”。
- 资料池已增加右侧抽屉，支持查看上传资料、使用、放弃使用、恢复解析和删除。
- 地图改为优先加载高德 JS 地图，可拖拽、缩放；静态地图只作为兜底。
- 地图搜索和建议列表的 loading 竞态已修复，切换 POI/全部视图不再错误清掉加载状态。

## 后续仍需同事确认

- 若要正式上线高德 JS 地图，建议单独申请 Web 端 JS API Key，并配置 `AMAP_JS_API_KEY` / `AMAP_JS_SECURITY_CODE`，不要长期复用 Web Service Key。
- 当前 AI 输出仍标记为 `needs_review`，不能直接作为最终商业结论。
- 上传计划自动拆节点已有交互入口，但完整“计划 -> 节点 -> 证据 -> 报告”的业务闭环还需要继续扩展真实规则。
