"""
Historical Data Migration Script
Loads CSV files into the SQLite database with validation.
Invalid records are logged to logs/invalid_records.log.

Usage:
    cd data-challenge
    source .venv/bin/activate
    python -m scripts.load_csv
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.database import Base
from app.models import Department, Job, HiredEmployee

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "invalid_records.log"


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    if LOG_FILE.exists():
        LOG_FILE.unlink()


def log_invalid(table: str, row_num: int, raw_data: list, reasons: list[str]):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "table": table,
        "row": row_num,
        "data": raw_data,
        "reasons": reasons,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def validate_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def load_departments(session):
    filepath = DATA_DIR / "departments.csv"
    loaded, skipped = 0, 0
    existing_ids = {d.id for d in session.query(Department.id).all()}

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            reasons = []

            if len(row) < 2:
                reasons.append("insufficient columns")
            else:
                id_val, dept_name = row[0], row[1]
                if not id_val.strip():
                    reasons.append("id is required")
                if not dept_name.strip():
                    reasons.append("department is required")

            if reasons:
                log_invalid("departments", row_num, row, reasons)
                skipped += 1
                continue

            if int(id_val) in existing_ids:
                continue

            session.add(Department(id=int(id_val), department=dept_name.strip()))
            loaded += 1

    session.commit()
    print(f"  departments: {loaded} inserted, {skipped} skipped")


def load_jobs(session):
    filepath = DATA_DIR / "jobs.csv"
    loaded, skipped = 0, 0
    existing_ids = {j.id for j in session.query(Job.id).all()}

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            reasons = []

            if len(row) < 2:
                reasons.append("insufficient columns")
            else:
                id_val, job_name = row[0], row[1]
                if not id_val.strip():
                    reasons.append("id is required")
                if not job_name.strip():
                    reasons.append("job is required")

            if reasons:
                log_invalid("jobs", row_num, row, reasons)
                skipped += 1
                continue

            if int(id_val) in existing_ids:
                continue

            session.add(Job(id=int(id_val), job=job_name.strip()))
            loaded += 1

    session.commit()
    print(f"  jobs: {loaded} inserted, {skipped} skipped")


def load_hired_employees(session):
    filepath = DATA_DIR / "hired_employees.csv"
    loaded, skipped = 0, 0

    existing_ids = {e.id for e in session.query(HiredEmployee.id).all()}
    valid_dept_ids = {d.id for d in session.query(Department.id).all()}
    valid_job_ids = {j.id for j in session.query(Job.id).all()}

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            reasons = []

            if len(row) < 5:
                reasons.append("insufficient columns")
                log_invalid("hired_employees", row_num, row, reasons)
                skipped += 1
                continue

            id_val, name, dt_val, dept_id, job_id = row

            if not id_val.strip():
                reasons.append("id is required")
            if not name.strip():
                reasons.append("name is required")
            if not dt_val.strip():
                reasons.append("datetime is required")
            elif not validate_iso_datetime(dt_val.strip()):
                reasons.append("datetime must be in ISO 8601 format")
            if not dept_id.strip():
                reasons.append("department_id is required")
            elif int(dept_id) not in valid_dept_ids:
                reasons.append(f"department_id {dept_id} not found in departments")
            if not job_id.strip():
                reasons.append("job_id is required")
            elif int(job_id) not in valid_job_ids:
                reasons.append(f"job_id {job_id} not found in jobs")

            if reasons:
                log_invalid("hired_employees", row_num, row, reasons)
                skipped += 1
                continue

            if int(id_val) in existing_ids:
                continue

            session.add(HiredEmployee(
                id=int(id_val),
                name=name.strip(),
                datetime=dt_val.strip(),
                department_id=int(dept_id),
                job_id=int(job_id),
            ))
            loaded += 1

    session.commit()
    print(f"  hired_employees: {loaded} inserted, {skipped} skipped")


def main():
    print("Starting historical data migration...")

    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    setup_logging()

    try:
        load_departments(session)
        load_jobs(session)
        load_hired_employees(session)
        print(f"\nDone. Invalid records logged to: {LOG_FILE}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
