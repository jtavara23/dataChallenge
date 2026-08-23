import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def get_api_log_path(table: str) -> Path:
    path = LOG_DIR / "api"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{table}.log"


def get_migration_log_path(table: str, run_id: str) -> Path:
    path = LOG_DIR / "migration" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{table}.log"


def log_invalid_record(
    table: str,
    row_index: int,
    data,
    reasons: list[str],
    source: str = "api",
    run_id: str | None = None,
):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "table": table,
        "row": row_index,
        "data": data,
        "reasons": reasons,
    }

    if source == "migration" and run_id:
        log_path = get_migration_log_path(table, run_id)
    else:
        log_path = get_api_log_path(table)

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
