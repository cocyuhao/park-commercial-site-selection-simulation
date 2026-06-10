from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "90_p6_expert_dashboard"
OUT = ROOT / "40_quality_evidence" / "simulation_object_pool_api_validation_20260604.json"
sys.path.insert(0, str(DASHBOARD))

from app import app  # noqa: E402


def main() -> None:
    client = TestClient(app)
    report: dict[str, object] = {}

    listing = client.get("/api/simulation/objects")
    report["list_status"] = listing.status_code
    listing.raise_for_status()
    initial = listing.json()
    report["initial_count"] = initial["count"]
    report["type_counts"] = initial["type_counts"]
    report["summary"] = initial["summary"]

    created = client.post(
        "/api/simulation/objects",
        json={
            "object_type": "choice_probability",
            "title": "临时验证：亲子补给选择候选",
            "linked_id": "QA-CHOICE-OBJECT",
            "summary": "用于验证对象池新增、编辑、采用、锁定、删除链路，不进入业务结论。",
            "missing_inputs": ["真实客流", "转化率"],
            "specific_advice": ["样本口径复核后再进入仿真参数。"],
        },
    )
    report["create_status"] = created.status_code
    created.raise_for_status()
    created_row = created.json()
    object_id = created_row["object_id"]
    report["created_id"] = object_id

    updated = client.patch(
        f"/api/simulation/objects/{object_id}",
        json={
            "action": "update",
            "summary": "已编辑：把补水选择候选改为可复核对象。",
            "specific_advice": ["先补真实客流，再决定是否采用为仿真输入。"],
        },
    )
    report["update_status"] = updated.status_code
    updated.raise_for_status()
    report["updated_summary"] = updated.json()["summary"]

    used = client.patch(f"/api/simulation/objects/{object_id}", json={"action": "use"})
    report["use_status"] = used.status_code
    used.raise_for_status()
    report["adoption_after_use"] = used.json()["adoption_status"]

    locked = client.patch(f"/api/simulation/objects/{object_id}", json={"action": "lock"})
    report["lock_status"] = locked.status_code
    locked.raise_for_status()
    report["locked"] = locked.json()["user_locked"]

    blocked_delete = client.delete(f"/api/simulation/objects/{object_id}")
    report["delete_locked_status"] = blocked_delete.status_code
    report["delete_locked_detail"] = blocked_delete.json().get("detail")

    unlocked = client.patch(f"/api/simulation/objects/{object_id}", json={"action": "unlock"})
    report["unlock_status"] = unlocked.status_code
    unlocked.raise_for_status()

    deleted = client.delete(f"/api/simulation/objects/{object_id}")
    report["delete_status"] = deleted.status_code
    deleted.raise_for_status()
    report["delete_payload"] = deleted.json()

    final_listing = client.get("/api/simulation/objects")
    final_listing.raise_for_status()
    report["final_count"] = final_listing.json()["count"]

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT} final_count={report['final_count']}")


if __name__ == "__main__":
    main()
