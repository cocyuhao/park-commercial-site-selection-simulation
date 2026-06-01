# Evidence Ledger Schema

`evidence_ledger.csv` 是整个项目最重要的真实性底表。任何关键数字进入报告、模型或 PPT 前，都必须先进入这里。

## 字段说明

| 字段 | 说明 |
|---|---|
| `metric_id` | 指标唯一 ID，例如 `MET-0001` |
| `metric_name` | 指标名称，例如 `年总客流` |
| `value` | 数值，尽量只放标准化后的数字 |
| `unit` | 单位，例如 `人次/年`、`%`、`元/次` |
| `source_file` | 来源文件路径 |
| `source_page_or_slide` | 页码或幻灯片号 |
| `source_quote` | 原文片段，保留足够上下文 |
| `extraction_method` | 抽取方式，例如 `pdf_text`、`ppt_text`、`manual_review`、`amap_api` |
| `evidence_type` | 证据类型，例如 `source_report_pdf`、`presentation_assumption`、`amap_poi` |
| `confidence` | `high`、`medium`、`low`、`assumption` |
| `validation_status` | `raw`、`checked`、`conflict`、`needs_review`、`rejected` |
| `notes` | 备注，包括口径问题、单位问题、异常解释 |

## 使用规则

- 报告中的每个关键数字都要能通过 `metric_id` 找回来源。
- PPT 中的数字默认 `confidence=low` 或 `assumption`，除非回查到 PDF/GIS/经营数据。
- 单位不明的数字不得进入模型，只能进入 `needs_review`。
- 同一指标多来源冲突时，保留多行并标记 `conflict`。
