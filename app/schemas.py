from pydantic import BaseModel, field_validator
from datetime import datetime as dt
from typing import Optional


class DepartmentCreate(BaseModel):
    id: int
    department: str

    @field_validator("department")
    @classmethod
    def department_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("department is required")
        return v.strip()


class JobCreate(BaseModel):
    id: int
    job: str

    @field_validator("job")
    @classmethod
    def job_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("job is required")
        return v.strip()


class HiredEmployeeCreate(BaseModel):
    id: int
    name: str
    datetime: str
    department_id: int
    job_id: int

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("name is required")
        return v.strip()

    @field_validator("datetime")
    @classmethod
    def datetime_is_iso(cls, v):
        if not v or not v.strip():
            raise ValueError("datetime is required")
        try:
            dt.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise ValueError("datetime must be in ISO 8601 format (e.g. 2021-07-27T16:02:08Z)")
        return v.strip()


class RowError(BaseModel):
    row: int
    reasons: list[str]


class BatchResponse(BaseModel):
    inserted: int
    errors: list[RowError]
