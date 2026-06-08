from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = ROOT / "30_extraction" / "cad"
QUALITY_DIR = ROOT / "40_quality_evidence"

DXF_INPUTS = [
    {
        "cad_id": "osen_north_t5",
        "source_dwg": "CAD图及其计划/奥森北园(字体放大)-改造建筑示意_t5.dwg",
        "dxf": CAD_DIR / "oda_output_north" / "osen_north_t5.dxf",
        "conversion_tool": "ODA File Converter 27.1.0",
        "conversion_log": "40_quality_evidence/cad_north_oda_conversion_20260605.log",
    },
    {
        "cad_id": "osen_south_t5",
        "source_dwg": "CAD图及其计划/奥森南园（字体放大）-改造建筑示意_t5.dwg",
        "dxf": CAD_DIR / "oda_output_south" / "osen_south_t5.dxf",
        "conversion_tool": "ODA File Converter 27.1.0",
        "conversion_log": "40_quality_evidence/cad_south_oda_conversion_20260605.log",
    },
]

KEYWORDS = [
    "桃花源",
    "白房子",
    "廉洁",
    "展馆",
    "西分区",
    "管理中心",
    "南门",
    "地下",
    "预埋",
    "露天剧场",
    "2A03",
    "咖啡",
    "餐饮",
    "文创",
    "康养",
    "瑜伽",
    "入口",
    "改造",
]

POINT_CODE_GROUPS = {
    "x": {10, 11, 12, 13, 14, 15, 16, 17, 18},
    "y": {20, 21, 22, 23, 24, 25, 26, 27, 28},
}


@dataclass
class DxfScan:
    cad_id: str
    source_dwg: str
    dxf_path: Path
    conversion_tool: str
    conversion_log: str
    dxf_bytes: int = 0
    line_pairs: int = 0
    sections: Counter[str] = field(default_factory=Counter)
    entity_counts: Counter[str] = field(default_factory=Counter)
    layer_counts: Counter[str] = field(default_factory=Counter)
    text_by_layer: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    keyword_hits: list[dict[str, Any]] = field(default_factory=list)
    min_x: float = math.inf
    min_y: float = math.inf
    max_x: float = -math.inf
    max_y: float = -math.inf
    warnings: list[str] = field(default_factory=list)

    def add_point_value(self, code: int, value: str) -> None:
        try:
            number = float(value)
        except ValueError:
            return
        # CAD headers and viewport helpers can contain +/-1e20 sentinel values.
        # They are useful for AutoCAD internals, but would destroy drawing bounds.
        if abs(number) > 1e10:
            return
        if code in POINT_CODE_GROUPS["x"]:
            self.min_x = min(self.min_x, number)
            self.max_x = max(self.max_x, number)
        elif code in POINT_CODE_GROUPS["y"]:
            self.min_y = min(self.min_y, number)
            self.max_y = max(self.max_y, number)

    def bounds(self) -> dict[str, float | None]:
        if any(math.isinf(v) for v in (self.min_x, self.min_y, self.max_x, self.max_y)):
            return {"min_x": None, "min_y": None, "max_x": None, "max_y": None, "width": None, "height": None}
        return {
            "min_x": round(self.min_x, 4),
            "min_y": round(self.min_y, 4),
            "max_x": round(self.max_x, 4),
            "max_y": round(self.max_y, 4),
            "width": round(self.max_x - self.min_x, 4),
            "height": round(self.max_y - self.min_y, 4),
        }


def decode_value(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030", "latin-1"):
        try:
            return raw.decode(encoding).rstrip("\r\n")
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").rstrip("\r\n")


def iter_group_pairs(path: Path):
    with path.open("rb") as f:
        while True:
            code_raw = f.readline()
            if not code_raw:
                break
            value_raw = f.readline()
            if not value_raw:
                break
            code_text = decode_value(code_raw).strip()
            value = decode_value(value_raw).strip()
            try:
                code = int(code_text)
            except ValueError:
                continue
            yield code, value


def record_text(scan: DxfScan, entity_type: str, layer: str, text: str, x: float | None, y: float | None) -> None:
    clean = " ".join(text.replace("\\P", " ").replace("\\~", " ").split())
    if not clean:
        return
    bucket = scan.text_by_layer[layer]
    if len(bucket) < 40:
        bucket.append({"entity": entity_type, "text": clean[:160], "x": x, "y": y})
    for keyword in KEYWORDS:
        if keyword in clean and len(scan.keyword_hits) < 200:
            scan.keyword_hits.append(
                {
                    "keyword": keyword,
                    "layer": layer,
                    "entity": entity_type,
                    "text": clean[:180],
                    "x": x,
                    "y": y,
                }
            )


def analyze_dxf(meta: dict[str, Any]) -> DxfScan:
    path = Path(meta["dxf"])
    scan = DxfScan(
        cad_id=meta["cad_id"],
        source_dwg=meta["source_dwg"],
        dxf_path=path,
        conversion_tool=meta["conversion_tool"],
        conversion_log=meta["conversion_log"],
    )
    if not path.exists():
        scan.warnings.append("DXF file is missing.")
        return scan

    scan.dxf_bytes = path.stat().st_size
    section = ""
    in_entities = False
    current_type = ""
    current_layer = "0"
    current_text_parts: list[str] = []
    current_x: float | None = None
    current_y: float | None = None
    pending_section_name = False

    def flush_entity() -> None:
        nonlocal current_type, current_layer, current_text_parts, current_x, current_y
        if current_type in {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}:
            record_text(scan, current_type, current_layer, "".join(current_text_parts), current_x, current_y)
        current_type = ""
        current_layer = "0"
        current_text_parts = []
        current_x = None
        current_y = None

    for code, value in iter_group_pairs(path):
        scan.line_pairs += 1
        if code in POINT_CODE_GROUPS["x"] | POINT_CODE_GROUPS["y"]:
            scan.add_point_value(code, value)

        if code == 0 and value == "SECTION":
            section = ""
            pending_section_name = True
            continue
        if pending_section_name and code == 2:
            section = value
            scan.sections[section] += 1
            in_entities = section == "ENTITIES"
            pending_section_name = False
            continue
        if code == 0 and value == "ENDSEC":
            flush_entity()
            in_entities = False
            section = ""
            continue

        if in_entities and code == 0:
            flush_entity()
            current_type = value
            current_layer = "0"
            scan.entity_counts[value] += 1
            continue

        if in_entities and current_type:
            if code == 8:
                current_layer = value or "0"
                scan.layer_counts[current_layer] += 1
            elif current_type in {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"} and code in {1, 3}:
                current_text_parts.append(value)
            elif code == 10:
                try:
                    current_x = float(value)
                except ValueError:
                    current_x = None
            elif code == 20:
                try:
                    current_y = float(value)
                except ValueError:
                    current_y = None

    flush_entity()
    return scan


def scan_to_dict(scan: DxfScan) -> dict[str, Any]:
    text_samples = []
    for layer, rows in scan.text_by_layer.items():
        text_samples.extend({"layer": layer, **row} for row in rows[:10])
        if len(text_samples) >= 80:
            break
    return {
        "cad_id": scan.cad_id,
        "source_dwg": scan.source_dwg,
        "dxf_path": str(scan.dxf_path.relative_to(ROOT)),
        "conversion_tool": scan.conversion_tool,
        "conversion_log": scan.conversion_log,
        "dxf_bytes": scan.dxf_bytes,
        "line_pairs": scan.line_pairs,
        "sections": dict(scan.sections),
        "entity_counts": dict(scan.entity_counts.most_common()),
        "top_layers": dict(scan.layer_counts.most_common(30)),
        "bounds": scan.bounds(),
        "text_layer_count": len(scan.text_by_layer),
        "text_sample_count": sum(len(v) for v in scan.text_by_layer.values()),
        "text_samples": text_samples,
        "keyword_hits": scan.keyword_hits,
        "warnings": scan.warnings,
    }


def write_outputs(results: list[dict[str, Any]]) -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    json_path = QUALITY_DIR / "cad_dxf_analysis_20260605.json"
    md_path = QUALITY_DIR / "cad_dxf_analysis_20260605.md"
    csv_path = QUALITY_DIR / "cad_dxf_keyword_hits_20260605.csv"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "method": "ODA File Converter for DWG to DXF; streaming DXF group-code scan for counts, text, bounds.",
        "results": results,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["cad_id", "keyword", "layer", "entity", "text", "x", "y"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            for hit in result.get("keyword_hits", []):
                writer.writerow({"cad_id": result["cad_id"], **hit})

    lines = ["# CAD/DWG 转换与 DXF 解析证据（2026-06-05）", ""]
    for result in results:
        bounds = result["bounds"]
        lines.extend(
            [
                f"## {result['cad_id']}",
                "",
                f"- 源 DWG：`{result['source_dwg']}`",
                f"- DXF：`{result['dxf_path']}`",
                f"- 转换工具：{result['conversion_tool']}",
                f"- DXF 大小：{result['dxf_bytes']:,} bytes",
                f"- 实体类型数：{len(result['entity_counts'])}",
                f"- 文字图层数：{result['text_layer_count']}",
                f"- 关键词命中：{len(result['keyword_hits'])}",
                f"- 图纸坐标范围：X {bounds['min_x']} ~ {bounds['max_x']}，Y {bounds['min_y']} ~ {bounds['max_y']}；宽 {bounds['width']}，高 {bounds['height']}",
                "",
                "### 主要实体",
            ]
        )
        for entity, count in list(result["entity_counts"].items())[:10]:
            lines.append(f"- {entity}: {count}")
        lines.extend(["", "### 关键词样例"])
        for hit in result.get("keyword_hits", [])[:12]:
            lines.append(f"- {hit['keyword']} / {hit['layer']} / {hit['entity']}：{hit['text']}")
        if result.get("warnings"):
            lines.extend(["", "### 警告"])
            lines.extend(f"- {warning}" for warning in result["warnings"])
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    results = [scan_to_dict(analyze_dxf(meta)) for meta in DXF_INPUTS]
    write_outputs(results)
    print(json.dumps({"results": len(results), "cad_ids": [r["cad_id"] for r in results]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
