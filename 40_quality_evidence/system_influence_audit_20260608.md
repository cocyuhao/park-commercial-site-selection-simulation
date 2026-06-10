# 系统影响面审计

- 生成时间：2026-06-09T09:55:29
- 状态：review
- Python：`C:\Users\Yy199\AppData\Local\Programs\Python\Python312\python.exe`
- Chrome：`True`

## 风险

- `medium` workspace：90_archive 存在大量历史产物；全仓脚本必须显式排除或标记 archive，避免旧口径回流。

## 关键结论

- 这份审计只读环境，不修改配置。
- 代理、归档目录、运行态端口、全局技能/插件缓存都可能影响当前程序判断。
- 后续修历史问题时，必须先判断命中属于客户可见、当前运行、工程证据、还是归档历史。
