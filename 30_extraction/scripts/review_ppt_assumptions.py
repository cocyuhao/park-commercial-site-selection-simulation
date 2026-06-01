from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "40_quality_evidence" / "evidence_ledger.csv"
OUT_CSV = ROOT / "40_quality_evidence" / "ppt_assumption_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "ppt_assumption_review.md"

FIELDS = [
    "assumption_metric_id",
    "assumption_name",
    "assumption_value",
    "review_status",
    "supporting_metric_ids",
    "finding",
    "required_next_evidence",
]


REVIEW_ROWS = [
    {
        "assumption_metric_id": "MET-0029",
        "review_status": "unsupported_financial_assumption",
        "supporting_metric_ids": "",
        "finding": "城市绿心四大改造投入 380 万元目前只来自 PPT，缺少造价清单、工程量或招商报价。",
        "required_next_evidence": "改造清单、设备报价、施工估算、品牌方投入边界。",
    },
    {
        "assumption_metric_id": "MET-0030",
        "review_status": "unsupported_financial_assumption",
        "supporting_metric_ids": "",
        "finding": "城市绿心预计年公园收益 620 万元只来自 PPT，缺少转化率、客单价、租金和分成参数来源。",
        "required_next_evidence": "经营流水、租金合同、客单价、分成比例、转化率试点数据。",
    },
    {
        "assumption_metric_id": "MET-0031",
        "review_status": "formula_consistent_but_inputs_unverified",
        "supporting_metric_ids": "MET-0029;MET-0030",
        "finding": "7.3 个月回收期与 380/620*12 的内部公式基本一致，但投入和收益输入均未验证。",
        "required_next_evidence": "先核验 MET-0029 和 MET-0030，再保留或修正回收期。",
    },
    {
        "assumption_metric_id": "MET-0032",
        "review_status": "unsupported_business_assumption",
        "supporting_metric_ids": "",
        "finding": "12% 营业额分成下限目前只来自 PPT，未见合同或可比项目依据。",
        "required_next_evidence": "招商条款、同类公园分成案例、商户访谈。",
    },
    {
        "assumption_metric_id": "MET-0033",
        "review_status": "unsupported_business_assumption",
        "supporting_metric_ids": "",
        "finding": "15% 营业额分成上限目前只来自 PPT，未见合同或可比项目依据。",
        "required_next_evidence": "招商条款、同类公园分成案例、商户访谈。",
    },
    {
        "assumption_metric_id": "MET-0034",
        "review_status": "partial_support_with_scope_gaps",
        "supporting_metric_ids": "MET-0003;MET-0017;MET-0018;MET-0044;MET-0045;MET-0046;MET-0047;MET-0048",
        "finding": "城市绿心五大缺口中的需求侧信号有部分 PDF 支持，如咖啡 TGI=241、已育占比 69.49%、星级酒店 TGI=155、国家级景点 TGI=195；但园内供给、现场调研和五个缺口数量仍未被强证据闭合。另需注意 PPT 中“咖啡厅覆盖度 1.35%”应是北京市大盘值，PDF 目标客群覆盖度为 3.26%。",
        "required_next_evidence": "高德 POI、现场业态清单、园内营业点坐标、缺口评分公式。",
    },
    {
        "assumption_metric_id": "MET-0035",
        "review_status": "partial_support_with_scope_gaps",
        "supporting_metric_ids": "MET-0007;MET-0008;MET-0025;MET-0026;MET-0027;MET-0028;MET-0049;MET-0050",
        "finding": "奥森五大缺口中的需求侧信号有部分 PDF 支持，如咖啡厅 TGI=286、瑜伽 TGI=382、冷饮店 TGI=332；但文创、夜间餐酒流量占比和供给覆盖仍未闭合。",
        "required_next_evidence": "高德 POI、17-22 时段完整小时序列、文创/餐酒现有点位、现场清单。",
    },
    {
        "assumption_metric_id": "MET-0036",
        "review_status": "conflict_needs_external_validation",
        "supporting_metric_ids": "MET-0052",
        "finding": "PPT 称奥森精品咖啡仅 2 家，但 PDF 热门到访表内已能看到 3 个咖啡相关 POI；该表不是完整供给清单，因此不能直接反证，但足以标记为冲突待核验。",
        "required_next_evidence": "高德关键词 POI 抓取、园内边界过滤、现场营业状态核验。",
    },
    {
        "assumption_metric_id": "MET-0037",
        "review_status": "conflict_needs_external_validation",
        "supporting_metric_ids": "MET-0051",
        "finding": "PPT 称奥森瑜伽/普拉提 0 家，但 PDF 热门到访表可见“悦健达专项体能·康复·普拉提运动中心”；需核验是否在园内、是否营业、是否可计入供给。",
        "required_next_evidence": "高德 POI、园区边界、现场清单。",
    },
    {
        "assumption_metric_id": "MET-0038",
        "review_status": "unsupported_financial_assumption",
        "supporting_metric_ids": "",
        "finding": "奥森 P0 改造当前日收益 1.13 万元只来自 PPT，未见经营台账或分项流水。",
        "required_next_evidence": "现有商户流水、租金、分成、分业态收入。",
    },
    {
        "assumption_metric_id": "MET-0039",
        "review_status": "unsupported_financial_assumption",
        "supporting_metric_ids": "",
        "finding": "奥森 P0 改造优化后日收益 5.06 万元只来自 PPT，缺少转化率和客单价模型参数。",
        "required_next_evidence": "转化率、客单价、业态容量、分成比例、营业天数假设。",
    },
    {
        "assumption_metric_id": "MET-0040",
        "review_status": "formula_consistent_but_inputs_unverified",
        "supporting_metric_ids": "MET-0038;MET-0039",
        "finding": "日收益增量 3.93 万元与 5.06-1.13 的内部计算一致，但两个输入值仍未验证。",
        "required_next_evidence": "先核验当前日收益和优化后日收益。",
    },
    {
        "assumption_metric_id": "MET-0041",
        "review_status": "formula_consistent_but_inputs_unverified",
        "supporting_metric_ids": "MET-0040",
        "finding": "年收入增量 1,430 万元与 3.93 万元/日按全年折算基本接近，但营业天数和淡旺季未独立核验。",
        "required_next_evidence": "营业日历、季节系数、节假日/工作日分场景测算。",
    },
    {
        "assumption_metric_id": "MET-0042",
        "review_status": "formula_consistent_but_inputs_unverified",
        "supporting_metric_ids": "MET-0041;MET-0043",
        "finding": "2.9 个月回收期与 350/1430*12 的内部公式基本一致，但投入和收益输入仍未验证。",
        "required_next_evidence": "先核验年收入增量和总改造投入。",
    },
    {
        "assumption_metric_id": "MET-0043",
        "review_status": "unsupported_financial_assumption",
        "supporting_metric_ids": "",
        "finding": "奥森 P0 总改造投入 350 万元只来自 PPT，缺少工程量、设备、品牌引入、不可预见费明细的外部核验。",
        "required_next_evidence": "改造工程量、设备报价、品牌合作条款、施工估算。",
    },
]


def main() -> None:
    ledger = pd.read_csv(LEDGER, dtype=str).fillna("")
    lookup = ledger.set_index("metric_id").to_dict(orient="index")

    output_rows: list[dict[str, str]] = []
    missing_ids: list[str] = []
    for row in REVIEW_ROWS:
        metric_id = row["assumption_metric_id"]
        item = lookup.get(metric_id)
        if item is None:
            missing_ids.append(metric_id)
            continue
        output_rows.append(
            {
                "assumption_metric_id": metric_id,
                "assumption_name": item["metric_name"],
                "assumption_value": f"{item['value']}{item['unit']}",
                "review_status": row["review_status"],
                "supporting_metric_ids": row["supporting_metric_ids"],
                "finding": row["finding"],
                "required_next_evidence": row["required_next_evidence"],
            }
        )

    if missing_ids:
        raise ValueError(f"台账缺少假设指标：{missing_ids}")

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    status_counts = pd.Series([r["review_status"] for r in output_rows]).value_counts().to_dict()
    lines = [
        "# PPT 假设核验报告",
        "",
        "## 结论",
        "",
        f"- 已核验 PPT 假设指标：{len(output_rows)} 条。",
        f"- 核验状态统计：{status_counts}",
        "- 财务类指标目前只能确认公式内部一致，不能确认输入真实。",
        "- 城市绿心 PPT 的“咖啡厅覆盖度仅 1.35%”存在口径问题：PDF 原生表格显示 1.35% 是北京市大盘值，目标客群覆盖度是 3.26%，TGI=241。",
        "- 奥森 PPT 的“精品咖啡仅 2 家”和“瑜伽/普拉提 0 家”已标记为冲突待核验，因为 PDF 热门到访表已有相反线索。",
        "",
        "## 优先核验项",
        "",
        "1. 高德 POI：按园区边界过滤咖啡、茶饮、瑜伽/普拉提、文创、餐酒和冷饮点位。",
        "2. 经营数据：现有商户收入、租金、分成、客单价和转化率。",
        "3. 小时客流：补出 17-22 时段占比，不能只用 17 时峰值替代夜间流量结论。",
        "4. 供需缺口：把 PPT 的 5 个缺口拆成需求证据、供给证据、空间证据和财务证据四列。",
        "",
        "## 输出文件",
        "",
        "- `40_quality_evidence/ppt_assumption_review.csv`",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(output_rows)} rows to {OUT_CSV}")
    print(f"wrote report to {OUT_MD}")


if __name__ == "__main__":
    main()
