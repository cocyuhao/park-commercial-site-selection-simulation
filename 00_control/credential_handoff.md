# 凭据交接和安全规则

## 当前本地配置

本项目允许在本地 `.env` 保存真实运行凭据，但禁止把真实值写入代码、Markdown 报告、CSV、JSON 输出、日志、截图或最终交付材料。

当前 `.env` 应包含两个字段，值只在本地文件里保存。字段名如下：

```text
AMAP_WEB_SERVICE_KEY
DEEPSEEK_API_KEY
```

`.env` 已在 `.gitignore` 中，不能提交到 GitHub。

## 运行时读取规则

- 高德脚本只从 `AMAP_WEB_SERVICE_KEY` 读取 Key。
- DeepSeek 脚本只从 `DEEPSEEK_API_KEY` 读取 Key。
- `.env.example` 只保留空占位，不保存真实值。
- 任何日志只允许记录“是否配置、调用状态、模型名、任务 ID、结果条数、脱敏参数摘要”，不能记录真实 Key。

## 交接时怎么说

下一段对话只需要知道：

- 本地 `.env` 已保存高德和 DeepSeek 凭据；
- 不要要求用户再次粘贴 Key；
- 运行脚本时让脚本从 `.env` 或进程环境变量读取；
- 任何测试报告都必须脱敏。

## 安全扫描口径

后续验证脚本应允许 `.env` 内存在真实 Key，但继续扫描并禁止以下位置出现真实 Key：

- `.py`
- `.md`
- `.csv`
- `.json`
- `.ps1`
- `.txt`
- `.yml`
- `.yaml`
- `.toml`
- 除 `.env` 以外的 `.env*` 文件
