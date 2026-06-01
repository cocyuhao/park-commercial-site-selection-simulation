from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ZONES = ROOT / "70_outputs" / "processed_tables" / "p2_pdf_proxy_zone_candidates_deepseek.csv"
DWG = ROOT / "70_outputs" / "processed_tables" / "p2_dwg_conversion_worklist_deepseek.csv"
LIMITS = ROOT / "70_outputs" / "processed_tables" / "p2_geometry_proxy_limitations_deepseek.csv"
AUDIT_JSON = ROOT / "40_quality_evidence" / "deepseek_p2_geometry_proxy_audit.json"
OUT_CSV = ROOT / "40_quality_evidence" / "deepseek_p2_geometry_proxy_audit_review.csv"
OUT_MD = ROOT / "40_quality_evidence" / "deepseek_p2_geometry_proxy_audit_review.md"

FIELDS = ["check_id", "status", "severity", "finding", "evidence"]


def add(rows: list[dict[str, str]], status: str, severity: str, finding: str, evidence: str) -> None:
    rows.append({"check_id": f"P2-GEOM-PROXY-REVIEW-{len(rows) + 1:03d}", "status": status, "severity": severity, "finding": finding, "evidence": evidence})


def ok(condition: bool) -> str:
    return "pass" if condition else "fail"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows: list[dict[str, str]] = []
    zones = read_csv(ZONES)
    dwg = read_csv(DWG)
    limits = read_csv(LIMITS)
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8-sig"))
    joined = json.dumps(audit, ensure_ascii=False) + "\n" + "\n".join(
        " ".join(row.values()) for table in [zones, dwg, limits] for row in table
    )

    add(rows, ok(len(zones) == 10), "error", f"PDF proxy zone rows={len(zones)}", str(ZONES))
    add(rows, ok(len(dwg) == 8), "error", f"DWG conversion rows={len(dwg)}", str(DWG))
    add(rows, ok(len(limits) == 8), "error", f"geometry limitation rows={len(limits)}", str(LIMITS))
    for name, table, path in [("zones", zones, ZONES), ("dwg", dwg, DWG), ("limits", limits, LIMITS)]:
        statuses = Counter(row.get("output_status", "") for row in table)
        executors = Counter(row.get("executor", "") for row in table)
        task_ids = Counter(row.get("llm_task_id", "") for row in table)
        add(rows, ok(statuses == {"needs_review": len(table)}), "error", f"{name} output statuses={dict(statuses)}", str(path))
        add(rows, ok(executors == {"deepseek": len(table)}), "error", f"{name} executors={dict(executors)}", str(path))
        add(rows, ok(task_ids == {"LLM-021": len(table)}), "error", f"{name} task_ids={dict(task_ids)}", str(path))

    add(rows, ok(all(row.get("geometry_status") == "pdf_proxy_label_only_pending_dwg_conversion" for row in zones)), "error", "PDF proxy zones preserve label-only geometry status", str(ZONES))
    add(rows, ok(all("pending_conversion" in row.get("blocking_status", "") for row in dwg)), "error", "DWG tasks remain pending_conversion", str(DWG))
    boundary_aliases = {
        "coordinates": ["坐标", "coordinate", "coordinates"],
        "area": ["面积", "area"],
        "layer": ["图层", "layer"],
        "movement": ["动线", "path", "route", "movement"],
        "DWG": ["DWG", "dwg"],
        "geometry": ["几何", "geometry"],
        "PDF": ["PDF", "pdf"],
        "pending_conversion": ["pending_conversion"],
    }
    joined_lower = joined.lower()
    for label, aliases in boundary_aliases.items():
        add(rows, ok(any(alias.lower() in joined_lower for alias in aliases)), "error", f"boundary keyword covered: {label}", str(AUDIT_JSON))
    forbidden_precision = ["geometry_status=parsed", "checked_geometry", "area_sqm_calculated", "coordinates_extracted"]
    add(rows, ok(not any(token in joined for token in forbidden_precision)), "error", "no false precision claims", str(AUDIT_JSON))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "pass"]
    OUT_MD.write_text(
        "\n".join(
            [
                "# DeepSeek P2 图纸代理与DWG转换前置审计复核",
                "",
                f"- 检查项：{len(rows)}",
                f"- 失败项：{len(failures)}",
                "",
                "## 结论",
                "",
                "- PDF代理分区、DWG转换工作单和几何代理限制均已生成并通过本地复核。",
                "- 当前仍不是DWG几何解析结果，只能作为P3转换和校准前置。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote p2 geometry proxy review rows={len(rows)} to {OUT_CSV}")
    print(f"wrote review report to {OUT_MD}")
    print(f"failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
