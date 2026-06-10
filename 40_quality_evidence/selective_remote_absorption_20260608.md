# 2026-06-08 远端最新改动选择性吸收记录

- 本地吸收前 HEAD：`168409f1be0e8a66a496498eb28dc6471014e221`
- 远端最新 HEAD：`96690980aabfa922e43fb9acf510b32a8e63a229`
- 本地备份分支：`backup/local-before-selective-sync-20260608-165111`
- 吸收方式：先 `fetch` 只读比较，再 `ff-only` 快进；没有做整仓镜像覆盖。

## 差异判断

- `4d74a2f Add full-stack automation test suite`：吸收。新增 `TestFiles` 自动化入口、fixtures、数据库健康检查，以及 `60_model/db/store.py` 的 SQLite busy timeout / import lock，属于低冲突质量能力。
- `9669098 Fix local automation report download check`：吸收。`httpx trust_env=False` 修复与本机代理导致的假 502 结论一致。
- `TestFiles/README.md`：吸收后修正。原文含协作者个人路径 `G:\...`，已改成 `<your-local-checkout>`。
- `30_extraction/scripts/build_osen_real_calibration_inputs_20260607.py` 与 `90_p6_expert_dashboard/app.py`：吸收后修正。默认“补来源文件”改成“复核来源文件”，避免客户报告边界被误导。
- `90_p6_expert_dashboard/app.py`：额外修正。`rebuild_real_calibration_outputs()` 现在显式使用 UTF-8 捕获子进程输出，并对 `stdout/stderr=None` 容错，修复真实测试中 `None.strip()`。

## 历史问题回归判断

- 远端 `origin/main` 是从本地上传提交 `168409f1be0e8a66a496498eb28dc6471014e221` 之后继续提交的，`git merge-base --is-ancestor 168409f origin/main` 通过；这次不是旧 main 直接覆盖回来。
- 新增 diff 中确实带入两类旧风险：个人路径 `G:\...`、默认“补来源文件”措辞。本轮已修正。
- 新增 `TestFiles/run_all_tests.py` 中的 `payload/debug/traceback` 只存在于测试记录和失败诊断，不属于客户 UI 或报告正文。
- `py -3.12 30_extraction\scripts\verify_project_implementation.py` 当前会失败 84 项，但抽样检查显示这些缺失文件在吸收前备份分支和吸收后 HEAD 都不存在，且本轮远端没有改动 `verify_project_implementation.py`。因此它是既有历史门禁口径失配，不是本次吸收引入的新破坏。
- 这些缺失项多指向曾被隔离到 `90_archive/pre_rollback_after_0100_snapshot_20260607_074108` 或 `90_archive/after_0100_quarantine_20260607_074257` 的旧产物。后续应单独做“门禁重基线”，不能简单把归档产物恢复成当前事实。

## 验证

- `py -3.12 -m py_compile 90_p6_expert_dashboard\app.py 60_model\db\store.py 30_extraction\scripts\build_osen_real_calibration_inputs_20260607.py TestFiles\run_all_tests.py TestFiles\check_db_health.py` 通过。
- `rg "G:\\|wxjwWorks|works\\park_commercial|补来源文件" TestFiles 30_extraction\scripts\build_osen_real_calibration_inputs_20260607.py 90_p6_expert_dashboard\app.py` 无命中。
- `py -3.12 TestFiles\run_all_tests.py` 通过，报告 `TestFiles/reports/test_report_20260608_165623.md`，结果 `passed=79 warning=1 failed=0`。
- `py -3.12 TestFiles\check_db_health.py` 返回 `integrity=ok`。
- `py -3.12 30_extraction\scripts\verify_project_implementation.py` 未通过，`checks=1135 failures=84`；已确认属于既有历史门禁债，不作为本次吸收通过条件。

## 剩余警告

- `TestFiles` 报告仍提示 21 个控件缺少 id 或可见名称。这是自动化可识别性/无障碍质量问题，不阻塞本轮吸收，但后续网页重做时应统一补齐。
