from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pathlib import Path
try:
    import fastavro
except ImportError:
    fastavro = None

from app.database import get_db
from app.auth import verify_api_key
from app.models import Department, Job, HiredEmployee

router = APIRouter(dependencies=[Depends(verify_api_key)])

BACKUP_DIR = Path(__file__).resolve().parent.parent.parent / "backups"

AVRO_SCHEMAS = {
    "departments": {
        "type": "record",
        "name": "Department",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "department", "type": "string"},
        ],
    },
    "jobs": {
        "type": "record",
        "name": "Job",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "job", "type": "string"},
        ],
    },
    "hired_employees": {
        "type": "record",
        "name": "HiredEmployee",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "name", "type": "string"},
            {"name": "datetime", "type": "string"},
            {"name": "department_id", "type": "int"},
            {"name": "job_id", "type": "int"},
        ],
    },
}

TABLE_MODELS = {
    "departments": Department,
    "jobs": Job,
    "hired_employees": HiredEmployee,
}

TABLE_COLUMNS = {
    "departments": ["id", "department"],
    "jobs": ["id", "job"],
    "hired_employees": ["id", "name", "datetime", "department_id", "job_id"],
}


@router.post("/backup/{table_name}")
def backup_table(table_name: str, db: Session = Depends(get_db)):
    if fastavro is None:
        raise HTTPException(status_code=503, detail="fastavro not installed")
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found. Valid: {list(TABLE_MODELS.keys())}")

    model = TABLE_MODELS[table_name]
    columns = TABLE_COLUMNS[table_name]
    rows = db.query(model).all()

    records = [{col: getattr(row, col) for col in columns} for row in rows]

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    filename = f"{table_name}_{timestamp}.avro"
    filepath = BACKUP_DIR / filename

    schema = fastavro.parse_schema(AVRO_SCHEMAS[table_name])
    with open(filepath, "wb") as f:
        fastavro.writer(f, schema, records)

    return {
        "message": "Backup saved",
        "table": table_name,
        "records": len(records),
        "path": f"backups/{filename}",
    }


@router.post("/restore/{table_name}")
def restore_table(table_name: str, db: Session = Depends(get_db)):
    if fastavro is None:
        raise HTTPException(status_code=503, detail="fastavro not installed")
    if table_name not in TABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found. Valid: {list(TABLE_MODELS.keys())}")

    backup_files = sorted(BACKUP_DIR.glob(f"{table_name}_*.avro"))
    if not backup_files:
        raise HTTPException(status_code=404, detail=f"No backup found for '{table_name}'")

    latest_backup = backup_files[-1]

    with open(latest_backup, "rb") as f:
        reader = fastavro.reader(f)
        records = list(reader)

    model = TABLE_MODELS[table_name]
    db.query(model).delete()

    for record in records:
        db.add(model(**record))

    db.commit()

    return {
        "message": f"Restored {len(records)} records to {table_name}",
        "table": table_name,
        "records": len(records),
        "source": latest_backup.name,
    }
