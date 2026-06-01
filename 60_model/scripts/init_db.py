from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_DIR = ROOT / "60_model" / "db"
if str(DB_DIR) not in sys.path:
    sys.path.insert(0, str(DB_DIR))

from store import init_db  # noqa: E402


def main() -> None:
    init_db()
    print("status=ok")
    print(f"db={ROOT / '60_model' / 'db' / 'simulation.sqlite3'}")


if __name__ == "__main__":
    main()
