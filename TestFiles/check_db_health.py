from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
paths = [ROOT / "60_model" / "db" / "simulation.sqlite3"]
if "--all-backups" in sys.argv:
    paths.extend(
        sorted(
            (ROOT / "TestFiles" / "reports").glob("state_backup_*/60_model/db/simulation.sqlite3"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    )

results = []
for path in paths:
    try:
        started = time.perf_counter()
        connection = sqlite3.connect(path)
        def stop_if_slow() -> int:
            return 1 if time.perf_counter() - started > 5 else 0

        connection.set_progress_handler(stop_if_slow, 1000)
        integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
        connection.close()
    except Exception as exc:
        integrity = f"{type(exc).__name__}: {exc}"
    results.append({"path": str(path), "size": path.stat().st_size if path.exists() else 0, "integrity": integrity})

print(json.dumps(results, ensure_ascii=False, indent=2))
