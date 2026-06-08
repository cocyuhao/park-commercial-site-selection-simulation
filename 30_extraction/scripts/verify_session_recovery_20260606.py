from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "session_recovery_20260606.json"
OUT_MD = ROOT / "40_quality_evidence" / "session_recovery_20260606.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def enabled_plugins() -> list[str]:
    config = ROOT.parent.parent / ".codex" / "config.toml"
    if not config.exists():
        config = Path.home() / ".codex" / "config.toml"
    if not config.exists():
        return []
    text = config.read_text(encoding="utf-8-sig", errors="replace")
    return re.findall(r'^\[plugins\."([^"]+)"\]', text, flags=re.MULTILINE)


def skill_count() -> int:
    roots = [Path.home() / ".codex" / "skills", Path.home() / ".agents" / "skills"]
    count = 0
    for root in roots:
        if root.exists():
            count += sum(1 for path in root.iterdir() if path.is_dir())
    return count


def path_state(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
    }


def main() -> None:
    plugins = enabled_plugins()
    plugin_counts = Counter(plugin.split("@", 1)[-1] if "@" in plugin else plugin for plugin in plugins)
    ui_skill = Path.home() / ".codex" / "skills" / "ui-ux-pro-max" / "SKILL.md"
    qa_package = ROOT / "90_p6_expert_dashboard" / "qa" / "package.json"
    qa_lock = ROOT / "90_p6_expert_dashboard" / "qa" / "package-lock.json"
    deepseek = read_json(ROOT / "40_quality_evidence" / "verify_deepseek_api_report.json")
    pdf_tables = read_json(ROOT / "40_quality_evidence" / "verify_pdf_tables_report.json")
    amap = read_json(ROOT / "50_external_gis" / "amap_smoke_tests" / "amap_smoke_test_latest.json")
    mainline = read_json(ROOT / "40_quality_evidence" / "codex_mainline_context_20260604.json")

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, evidence: Any) -> None:
        checks.append({"name": name, "status": "pass" if passed else "fail", "evidence": evidence})

    add("plugins_enabled", len(plugins) >= 50, {"count": len(plugins), "marketplaces": dict(plugin_counts)})
    add("ui_ux_pro_max_available", ui_skill.exists() and ui_skill.stat().st_size > 1000, path_state(ui_skill))
    add("skill_inventory_available", skill_count() >= 100, {"count": skill_count()})
    add("qa_node_stack_available", qa_package.exists() and qa_lock.exists(), [path_state(qa_package), path_state(qa_lock)])
    add("deepseek_api_pass", deepseek.get("overall_verdict") == "PASS", deepseek.get("summary", {}))
    add("pdf_table_gate_pass", pdf_tables.get("overall_verdict") == "PASS", pdf_tables.get("summary", {}))
    add("amap_smoke_pass", amap.get("status") == "ok" and amap.get("amap_status") == "1", amap)
    missing_files = mainline.get("missing_files", [])
    missing_count = len(missing_files) if isinstance(missing_files, list) else int(missing_files or 0)
    add("mainline_context_pass", missing_count == 0, {"missing_count": missing_count, "context_bytes": path_state(ROOT / "40_quality_evidence" / "codex_mainline_context_20260604.json")})

    result = {
        "generated_at": "2026-06-06",
        "purpose": "post-shutdown capability recovery for the simulation design mainline",
        "checks": checks,
        "summary": dict(Counter(check["status"] for check in checks)),
        "notes": [
            "Chrome DevTools MCP was reconnected in the current session after clearing the isolated chrome-devtools-mcp profile.",
            "Playwright, axe, and Lighthouse are project QA dependencies under 90_p6_expert_dashboard/qa.",
            "ui-ux-pro-max is not listed in the current skill menu, but its SKILL.md remains installed and is treated as a manual routing capability for UI decisions.",
        ],
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 关机后能力恢复证据",
        "",
        f"- 生成日期：{result['generated_at']}",
        f"- 通过项：{result['summary'].get('pass', 0)}",
        f"- 失败项：{result['summary'].get('fail', 0)}",
        "",
        "## 检查明细",
        "",
    ]
    for check in checks:
        lines.append(f"- `{check['status']}` {check['name']}: {check['evidence']}")
    lines.extend(["", "## 说明", ""])
    lines.extend(f"- {note}" for note in result["notes"])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    failures = [check for check in checks if check["status"] == "fail"]
    print(f"checks={len(checks)} failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
