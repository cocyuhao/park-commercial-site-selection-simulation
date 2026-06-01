from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
OUT_DIR = ROOT / "50_external_gis" / "amap_smoke_tests"
OUT_FILE = OUT_DIR / "amap_smoke_test_latest.json"


def load_local_env(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
    if "AMAP_API_KEY" in os.environ and "AMAP_WEB_SERVICE_KEY" not in os.environ:
        os.environ["AMAP_WEB_SERVICE_KEY"] = os.environ["AMAP_API_KEY"]


def main() -> None:
    load_local_env()
    key = os.environ.get("AMAP_WEB_SERVICE_KEY")
    payload = {
        "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endpoint": "v5/place/text",
        "status": "started",
        "query_summary": {
            "keywords": "奥林匹克森林公园",
            "region": "北京",
            "city_limit": "true",
            "page_size": "1",
        },
    }
    if not key:
        payload.update({"status": "error", "error_type": "MissingKey", "error_message": "AMAP_WEB_SERVICE_KEY is not set."})
    else:
        try:
            response = requests.get(
                "https://restapi.amap.com/v5/place/text",
                params={
                    "key": key,
                    "keywords": "奥林匹克森林公园",
                    "region": "北京",
                    "city_limit": "true",
                    "page_size": "1",
                    "page_num": "1",
                    "show_fields": "business",
                },
                timeout=30,
                headers={"User-Agent": "park-simulation-amap-smoke-test/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            pois = data.get("pois") if isinstance(data, dict) else []
            if isinstance(pois, dict):
                pois_count = len(pois.get("poi", [])) if isinstance(pois.get("poi"), list) else 1
            elif isinstance(pois, list):
                pois_count = len(pois)
            else:
                pois_count = 0
            payload.update(
                {
                    "status": "ok" if str(data.get("status")) == "1" else "api_error",
                    "amap_status": str(data.get("status", "")),
                    "amap_info": str(data.get("info", "")),
                    "result_count": pois_count,
                    "notes": "Real Amap API call succeeded if status is ok. Key is not stored.",
                }
            )
        except Exception as exc:
            payload.update(
                {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "notes": "No key is stored in this report.",
                }
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={payload['status']}")
    print(f"wrote={OUT_FILE}")
    if payload["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
