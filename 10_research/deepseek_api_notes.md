# DeepSeek API 资料摘要

资料来源：

- 官方文档首页：https://api-docs.deepseek.com/zh-cn/
- 价格页：https://api-docs.deepseek.com/zh-cn/quick_start/pricing
- JSON Output：https://api-docs.deepseek.com/zh-cn/guides/json_mode

检查日期：2026-05-23

## 当前采用规则

- Base URL：`https://api.deepseek.com`
- API Key：只从环境变量 `DEEPSEEK_API_KEY` 读取。
- 禁止把 Key 写入代码、日志、报告、交接文件。
- DeepSeek 作为低成本批处理和结构化辅助模型，不作为最终事实裁判。

## 模型路由

官方文档中已出现：

- `deepseek-v4-pro`
- `deepseek-v4-flash`

项目默认使用：

- `deepseek-v4-pro`：批量文本分类、表格候选解释、证据草稿生成、低风险代码草稿。
- `deepseek-v4-flash`：更低风险的大量摘要、去重、标签建议；暂不作为默认主力。

## 适合交给 DeepSeek 的任务

- 批量读取抽取文本后做页面主题分类。
- 批量判断表格属于客流、画像、TGI、POI、消费、收益哪一类。
- 从表格行生成候选证据草稿，但不能直接入账。
- 根据已有字段生成清洗建议。
- 生成低风险 Markdown 初稿、报告草稿、检查清单。
- 对 GitHub 仓库 README 做摘要和相关性初判。

## 不交给 DeepSeek 的任务

- 最终商业结论。
- API Key、凭据、隐私数据处理。
- 证据表最终入账。
- 高风险代码合并。
- GitHub 远程写入。
- 数据真实性最终裁定。

## 输出要求

DeepSeek 输出必须是中间结果，状态为 `draft` 或 `needs_review`。进入正式证据链前必须由本地脚本和人工规则复核。
