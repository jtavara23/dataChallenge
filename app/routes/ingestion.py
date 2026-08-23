from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import verify_api_key
from app.models import Department, Job, HiredEmployee
from app.schemas import (
    DepartmentCreate,
    JobCreate,
    HiredEmployeeCreate,
    BatchResponse,
    RowError,
)
from app.logger import log_invalid_record
from pydantic import ValidationError
from datetime import datetime

router = APIRouter(dependencies=[Depends(verify_api_key)])

MAX_BATCH_SIZE = 1000


@router.post("/departments", response_model=BatchResponse)
def ingest_departments(records: list[dict], db: Session = Depends(get_db)):
    if len(records) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Batch size exceeds {MAX_BATCH_SIZE}")

    inserted = 0
    errors = []

    for i, raw in enumerate(records):
        try:
            row = DepartmentCreate(**raw)
        except ValidationError as e:
            reasons = [err["msg"] for err in e.errors()]
            log_invalid_record("departments", i, raw, reasons)
            errors.append(RowError(row=i, reasons=reasons))
            continue

        existing = db.query(Department).filter_by(id=row.id).first()
        if existing:
            errors.append(RowError(row=i, reasons=[f"id {row.id} already exists"]))
            continue

        db.add(Department(id=row.id, department=row.department))
        inserted += 1

    db.commit()
    return BatchResponse(inserted=inserted, errors=errors)


@router.post("/jobs", response_model=BatchResponse)
def ingest_jobs(records: list[dict], db: Session = Depends(get_db)):
    if len(records) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Batch size exceeds {MAX_BATCH_SIZE}")

    inserted = 0
    errors = []

    for i, raw in enumerate(records):
        try:
            row = JobCreate(**raw)
        except ValidationError as e:
            reasons = [err["msg"] for err in e.errors()]
            log_invalid_record("jobs", i, raw, reasons)
            errors.append(RowError(row=i, reasons=reasons))
            continue

        existing = db.query(Job).filter_by(id=row.id).first()
        if existing:
            errors.append(RowError(row=i, reasons=[f"id {row.id} already exists"]))
            continue

        db.add(Job(id=row.id, job=row.job))
        inserted += 1

    db.commit()
    return BatchResponse(inserted=inserted, errors=errors)


@router.post("/hired-employees", response_model=BatchResponse)
def ingest_hired_employees(records: list[dict], db: Session = Depends(get_db)):
    if len(records) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Batch size exceeds {MAX_BATCH_SIZE}")

    valid_dept_ids = {d.id for d in db.query(Department.id).all()}
    valid_job_ids = {j.id for j in db.query(Job.id).all()}

    inserted = 0
    errors = []

    for i, raw in enumerate(records):
        try:
            row = HiredEmployeeCreate(**raw)
        except ValidationError as e:
            reasons = [err["msg"] for err in e.errors()]
            log_invalid_record("hired_employees", i, raw, reasons)
            errors.append(RowError(row=i, reasons=reasons))
            continue

        row_errors = []
        if row.department_id not in valid_dept_ids:
            row_errors.append(f"department_id {row.department_id} not found in departments")
        if row.job_id not in valid_job_ids:
            row_errors.append(f"job_id {row.job_id} not found in jobs")

        if row_errors:
            log_invalid_record("hired_employees", i, raw, row_errors)
            errors.append(RowError(row=i, reasons=row_errors))
            continue

        existing = db.query(HiredEmployee).filter_by(id=row.id).first()
        if existing:
            errors.append(RowError(row=i, reasons=[f"id {row.id} already exists"]))
            continue

        db.add(HiredEmployee(
            id=row.id,
            name=row.name,
            datetime=row.datetime,
            department_id=row.department_id,
            job_id=row.job_id,
        ))
        inserted += 1

    db.commit()
    return BatchResponse(inserted=inserted, errors=errors)
