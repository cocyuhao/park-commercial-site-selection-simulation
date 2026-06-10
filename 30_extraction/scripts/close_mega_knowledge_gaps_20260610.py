from __future__ import annotations

import importlib.util
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "10_research" / "recent_knowledge_base_20260609"
CN_DIR = ROOT / "10_research" / "china_academic_sources_20260610"
QUALITY_DIR = ROOT / "40_quality_evidence"
BASE_SCRIPT = ROOT / "30_extraction" / "scripts" / "build_recent_knowledge_base_20260609.py"

SIM_SCREENED = KB_DIR / "screened_simulation_stack_mega_20260609.jsonl"
SIM_CLOSED = KB_DIR / "screened_simulation_stack_mega_closed_20260610.jsonl"
SIM_CLASSIC = KB_DIR / "classic_theory_reference_mega_20260609.jsonl"
SIM_CLASSIC_CLOSED = KB_DIR / "classic_theory_reference_mega_closed_20260610.jsonl"
COMP_SCREENED = KB_DIR / "screened_computation_model_mega_20260609.jsonl"
COMP_CLOSED = KB_DIR / "screened_computation_model_mega_closed_20260610.jsonl"
MODEL_PACK = KB_DIR / "model_computation_knowledge_pack_20260609.jsonl"
CORE = KB_DIR / "curated_core_knowledge_base_20260609.jsonl"
METHOD_REFERENCE = KB_DIR / "method_reference_knowledge_base_20260609.csv"
SIM_SUPPLEMENT = KB_DIR / "screened_simulation_stack_supplement_20260609.jsonl"
COMP_CLASSIC = KB_DIR / "classic_computation_model_reference_mega_20260609.jsonl"
BASE_CLASSIC = KB_DIR / "classic_model_reference_20260609.jsonl"
CN_VERIFY = QUALITY_DIR / "china_academic_source_registry_verification_20260610.json"
VERIFY_JSON = QUALITY_DIR / "mega_knowledge_gap_closure_verification_20260610.json"

SIM_TARGET = 6_500
COMP_TARGET = 4_600

POSITIVE_RE = re.compile(
    r"park|public space|urban|visitor|touris|retail|commercial|consumer|pedestrian|crowd|plaza|"
    r"green space|recreation|amenit|facility location|site selection|GIS|geospatial|POI|"
    r"agent|simulation|microsimulation|queue|capacity|monte carlo|uncertainty|sensitivity|"
    r"choice model|logit|huff|gravity|activity chain|dwell time|footfall|mobility|"
    r"revenue|spending|conversion|food beverage|coffee|kiosk",
    re.I,
)
METHOD_RE = re.compile(
    r"agent|simulation|microsimulation|pedestrian|crowd|queue|capacity|monte carlo|uncertainty|"
    r"sensitivity|choice|logit|huff|gravity|facility location|site selection|GIS|geospatial|"
    r"activity chain|dwell time|forecast|optimization|calibration|validation|digital twin",
    re.I,
)
OFF_DOMAIN_RE = re.compile(
    r"molecular|protein|gene|genome|cancer|tumou?r|clinical|patient|drug|battery|quantum|"
    r"photovoltaic|semiconductor|crop|soil|irrigation|livestock|poultry|nanoencapsulation|"
    r"nutraceutical|dietary supplement|enzyme|microplastics|wastewater|aquaculture",
    re.I,
)
CLASSIC_RE = re.compile(
    r"monte carlo|sensitivity|sobol|latin hypercube|queue|simulation|validation|"
    r"agent|choice|logit|huff|gravity|location|spatial interaction|activity|microsimulation|"
    r"discrete event|bayesian|uncertainty|forecast|optimization",
    re.I,
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("recent_kb_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def text_of(row: dict[str, Any]) -> str:
    parts = [
        str(row.get("title") or ""),
        str(row.get("abstract") or ""),
        str(row.get("theme") or ""),
        str(row.get("query") or ""),
        str(row.get("project_landing") or ""),
    ]
    return " ".join(parts)


def key_for(row: dict[str, Any]) -> str:
    doi = str(row.get("doi") or row.get("DOI") or "").lower().strip()
    if doi:
        return doi
    return re.sub(r"\s+", " ", str(row.get("title") or "").lower()).strip()


def is_relevant(row: dict[str, Any], *, classic: bool = False) -> bool:
    text = text_of(row)
    if not text.strip():
        return False
    if OFF_DOMAIN_RE.search(text):
        return False
    if classic:
        return bool(CLASSIC_RE.search(text))
    return bool(POSITIVE_RE.search(text) and METHOD_RE.search(text))


def merge_unique(primary: list[dict[str, Any]], candidates: list[dict[str, Any]], target: int, tag: str) -> list[dict[str, Any]]:
    existing = {key_for(row) for row in primary if key_for(row)}
    merged = list(primary)
    for row in sorted(candidates, key=lambda r: (float(r.get("score") or 0), int(r.get("year") or 0), int(r.get("cited_by_count") or 0)), reverse=True):
        key = key_for(row)
        if not key or key in existing:
            continue
        if not is_relevant(row):
            continue
        updated = dict(row)
        updated["closure_added_20260610"] = tag
        updated["quality_reason"] = str(updated.get("quality_reason") or "") + "；20260610 闭合补充：通过严格正负词过滤，用于补足 Mega 多源/方法覆盖。"
        merged.append(updated)
        existing.add(key)
        if len(merged) >= target:
            break
    return merged


def close_classics() -> list[dict[str, Any]]:
    candidates = read_jsonl(COMP_CLASSIC) + read_jsonl(BASE_CLASSIC)
    by_key: dict[str, dict[str, Any]] = {}
    for row in candidates:
        if not is_relevant(row, classic=True):
            continue
        row = dict(row)
        row["reference_class"] = "classic_theory"
        row["curation_tier"] = "theory_reference"
        row["closure_added_20260610"] = "simulation_stack_classic_gap"
        row["quality_reason"] = "经典理论补充：用于仿真、选择、排队、位置、敏感性或校准的方法骨架，不直接作为客户结论。"
        by_key.setdefault(key_for(row), row)
    rows = list(by_key.values())
    rows.sort(key=lambda r: (int(r.get("cited_by_count") or 0), int(r.get("year") or 0)), reverse=True)
    write_jsonl(SIM_CLASSIC, rows)
    write_jsonl(SIM_CLASSIC_CLOSED, rows)
    return rows


def merge_into_base(base: Any, supplements: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    existing = read_jsonl(base.SCREENED_JSONL)
    by_key: dict[str, dict[str, Any]] = {}
    for row in existing + supplements:
        scored = {**row, **base.score_record(row)}
        key = base.record_key(scored)
        if key not in by_key:
            by_key[key] = scored
            continue
        old = by_key[key]
        old_sources = set(str(old.get("source") or "").split("+"))
        new_sources = set(str(scored.get("source") or "").split("+"))
        old["source"] = "+".join(sorted((old_sources | new_sources) - {""}))
        old_themes = set(str(old.get("theme") or "").split("+"))
        new_themes = set(str(scored.get("theme") or "").split("+"))
        old["theme"] = "+".join(sorted((old_themes | new_themes) - {""}))
        if float(scored.get("score") or 0) > float(old.get("score") or 0):
            for field in ["score", "tier", "category_hits", "category_count", "project_landing", "abstract", "venue", "cited_by_count", "quality_reason"]:
                if field in scored:
                    old[field] = scored[field]
    merged = [row for row in by_key.values() if row.get("tier") != "reject_low_relevance"]
    merged.sort(key=lambda r: (float(r.get("score") or 0), int(r.get("year") or 0), int(r.get("cited_by_count") or 0)), reverse=True)
    stats = {
        "dedup_total": len(merged),
        "screened_total": len(merged),
        "rejected_total": 0,
        "tier_counts": dict(Counter(row.get("tier") for row in merged)),
        "year_counts": dict(Counter(str(row.get("year")) for row in merged)),
        "theme_counts": dict(Counter(theme for row in merged for theme in str(row.get("theme") or "").split("+"))),
        "category_counts": dict(Counter(cat for row in merged for cat, hit in (row.get("category_hits") or {}).items() if hit)),
        "source_counts": dict(Counter(src for row in merged for src in str(row.get("source") or "").split("+") if src)),
    }
    return merged, stats


def main() -> None:
    base = load_base_module()
    sim_original = [row for row in read_jsonl(SIM_SCREENED) if is_relevant(row)]
    comp_original = [row for row in read_jsonl(COMP_SCREENED) if is_relevant(row)]
    pack = read_jsonl(MODEL_PACK)
    core = read_jsonl(CORE)
    sim_supplement = read_jsonl(SIM_SUPPLEMENT)

    sim_candidates = pack + core + sim_supplement
    comp_candidates = pack + core
    sim_closed = merge_unique(sim_original, sim_candidates, SIM_TARGET, "simulation_stack_multisource_gap")
    comp_closed = merge_unique(comp_original, comp_candidates, COMP_TARGET, "computation_model_multisource_gap")
    classics = close_classics()
    write_jsonl(SIM_CLOSED, sim_closed)
    write_jsonl(COMP_CLOSED, comp_closed)

    merged, stats = merge_into_base(base, sim_closed + comp_closed)
    old_verify = json.loads(base.VERIFY_JSON.read_text(encoding="utf-8-sig")) if base.VERIFY_JSON.exists() else {}
    meta = {
        "raw_counts": old_verify.get("raw_counts", {}),
        "errors": old_verify.get("errors", []),
        "query_count": old_verify.get("query_count", 0),
        "closure_20260610": {
            "simulation_stack_closed_total": len(sim_closed),
            "computation_model_closed_total": len(comp_closed),
            "classic_theory_closed_total": len(classics),
            "domestic_source_registry": str(CN_VERIFY.relative_to(ROOT)) if CN_VERIFY.exists() else "",
        },
    }
    base.write_outputs(merged, [], stats, meta)

    source_counts = Counter(src for row in sim_closed + comp_closed for src in str(row.get("source") or "").split("+") if src)
    verify = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass"
        if len(sim_closed) >= SIM_TARGET and len(comp_closed) >= COMP_TARGET and len(classics) >= 120 and len(source_counts) >= 2
        else "needs_action",
        "simulation_stack": {
            "original_relevant_after_strict_filter": len(sim_original),
            "closed_total": len(sim_closed),
            "target": SIM_TARGET,
            "classic_total": len(classics),
        },
        "computation_model": {
            "original_relevant_after_strict_filter": len(comp_original),
            "closed_total": len(comp_closed),
            "target": COMP_TARGET,
        },
        "merged_core_input": {
            "screened_total": stats["screened_total"],
            "source_counts": stats["source_counts"],
            "category_counts": stats["category_counts"],
        },
        "source_counts_for_closure": dict(source_counts),
        "domestic_registry_status": json.loads(CN_VERIFY.read_text(encoding="utf-8-sig")).get("status") if CN_VERIFY.exists() else "missing",
        "files": {
            "simulation_stack_closed": str(SIM_CLOSED.relative_to(ROOT)),
            "simulation_stack_classic": str(SIM_CLASSIC.relative_to(ROOT)),
            "simulation_stack_classic_closed": str(SIM_CLASSIC_CLOSED.relative_to(ROOT)),
            "computation_model_closed": str(COMP_CLOSED.relative_to(ROOT)),
            "merged_screened": str(base.SCREENED_JSONL.relative_to(ROOT)),
            "merged_verify": str(base.VERIFY_JSON.relative_to(ROOT)),
        },
        "rule": "用严格过滤从已筛选多源大池补足 Mega 缺口；国内源先以官方接入层安装，待授权后进入真实记录。",
    }
    VERIFY_JSON.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
