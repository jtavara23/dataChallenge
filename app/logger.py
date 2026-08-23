import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "invalid_records.log"


def log_invalid_record(table: str, row_index: int, data: dict, reasons: list[str]):
    LOG_DIR.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "table": table,
        "row": row_index,
        "data": data,
        "reasons": reasons,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
