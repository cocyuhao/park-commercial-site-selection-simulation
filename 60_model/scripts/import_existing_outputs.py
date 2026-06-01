from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_DIR = ROOT / "60_model" / "db"
if str(DB_DIR) not in sys.path:
    sys.path.insert(0, str(DB_DIR))

from store import import_existing_outputs  # noqa: E402


def main() -> None:
    counts = import_existing_outputs()
    print("status=ok")
    for name, count in counts.items():
        print(f"{name}={count}")


if __name__ == "__main__":
    main()
