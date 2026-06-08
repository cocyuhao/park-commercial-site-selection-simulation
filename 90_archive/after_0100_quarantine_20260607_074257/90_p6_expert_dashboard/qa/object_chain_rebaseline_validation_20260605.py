from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "90_p6_expert_dashboard"
OUT_JSON = ROOT / "40_quality_evidence" / "object_chain_rebaseline_validation_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "object_chain_rebaseline_validation_20260605.md"

sys.path.insert(0, str(APP_DIR))
import app  # noqa: E402


REQUIRED_KEYS = {
    "project_scope",
    "source_material",
    "persona_state",
    "behavior_program",
    "choice_probability",
    "feature_derivative_scene",
    "spatial_context",
    "validation_target",
    "node_progress",
    "ai_session",
    "report_draft",
}

FORBIDDEN_VISIBLE_WORDS = {
    "debug",
    "raw",
    "payload",
    "smoke test",
    "api contract",
    "ConnectError",
    "traceback",
    "external_preview_only",
}


def check(name: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence}


def main() -> None:
    client = TestClient(app.app)
    response = client.get("/api/object-chain")
    payload = response.json()
    items = payload.get("items") or []
    keys = {str(item.get("object_key")) for item in items}
    visible_text = "\n".join(
        " ".join(
            str(item.get(field) or "")
            for field in ["label", "status_label", "next_action", "action_label"]
        )
        for item in items
    )
    checks = [
        check("http_200", response.status_code == 200, response.status_code),
        check("required_object_keys", REQUIRED_KEYS.issubset(keys), sorted(REQUIRED_KEYS - keys)),
        check("summary_matches_items", payload.get("summary", {}).get("total_items") == len(items), payload.get("summary")),
        check(
            "has_state_behavior_choice_validation_chain",
            all(key in keys for key in ["persona_state", "behavior_program", "choice_probability", "feature_derivative_scene", "validation_target"]),
            sorted(keys),
        ),
        check(
            "feature_scene_exposes_income_control",
            any(
                item.get("object_key") == "feature_derivative_scene"
                and "收入" in str(item.get("next_action") or "")
                and int(item.get("count") or 0) >= 1000
                for item in items
            ),
            [item for item in items if item.get("object_key") == "feature_derivative_scene"],
        ),
        check(
            "has_blocked_or_draft_truth",
            any(item.get("readiness") in {"blocked", "draft", "needs_input"} for item in items),
            [item.get("readiness") for item in items],
        ),
        check(
            "visible_text_has_no_backend_words",
            not any(word in visible_text for word in FORBIDDEN_VISIBLE_WORDS),
            [word for word in FORBIDDEN_VISIBLE_WORDS if word in visible_text],
        ),
        check(
            "source_points_to_direction_reset",
            payload.get("source") == "evidence_based_direction_reset_20260605",
            payload.get("source"),
        ),
    ]
    status = "pass" if all(item["passed"] for item in checks) else "fail"
    report = {
        "validator": "object_chain_rebaseline_validation_20260605.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "check_count": len(checks),
        "failure_count": sum(1 for item in checks if not item["passed"]),
        "object_count": len(items),
        "object_keys": sorted(keys),
        "summary": payload.get("summary"),
        "checks": checks,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(
        "\n".join(
            [
                "# 对象链路复位验证（2026-06-05）",
                "",
                f"- status: `{status}`",
                f"- object_count: `{len(items)}`",
                f"- summary: `{json.dumps(payload.get('summary'), ensure_ascii=False)}`",
                "",
                "## 检查",
                *[
                    f"- {'PASS' if item['passed'] else 'FAIL'} `{item['name']}`: {json.dumps(item['evidence'], ensure_ascii=False)}"
                    for item in checks
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"status={status}")
    print(f"wrote={OUT_JSON.relative_to(ROOT)}")
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
