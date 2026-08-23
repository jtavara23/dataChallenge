import pytest
from pydantic import ValidationError
from app.schemas import HiredEmployeeCreate, DepartmentCreate, JobCreate


class TestISODatetimeValidation:
    def test_valid_iso_datetime(self):
        emp = HiredEmployeeCreate(
            id=1, name="John", datetime="2021-07-27T16:02:08Z",
            department_id=1, job_id=1
        )
        assert emp.datetime == "2021-07-27T16:02:08Z"

    def test_valid_iso_datetime_with_offset(self):
        emp = HiredEmployeeCreate(
            id=1, name="John", datetime="2021-07-27T16:02:08+00:00",
            department_id=1, job_id=1
        )
        assert emp.datetime == "2021-07-27T16:02:08+00:00"

    def test_invalid_datetime_format(self):
        with pytest.raises(ValidationError) as exc_info:
            HiredEmployeeCreate(
                id=1, name="John", datetime="not-a-date",
                department_id=1, job_id=1
            )
        assert "ISO 8601" in str(exc_info.value)

    def test_empty_datetime(self):
        with pytest.raises(ValidationError):
            HiredEmployeeCreate(
                id=1, name="John", datetime="",
                department_id=1, job_id=1
            )

    def test_invalid_month(self):
        with pytest.raises(ValidationError):
            HiredEmployeeCreate(
                id=1, name="John", datetime="2021-13-01T00:00:00Z",
                department_id=1, job_id=1
            )


class TestRequiredFields:
    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            HiredEmployeeCreate(
                id=1, name="", datetime="2021-07-27T16:02:08Z",
                department_id=1, job_id=1
            )
        assert "name is required" in str(exc_info.value)

    def test_empty_department_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            DepartmentCreate(id=1, department="")
        assert "department is required" in str(exc_info.value)

    def test_empty_job_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            JobCreate(id=1, job="")
        assert "job is required" in str(exc_info.value)

    def test_valid_department(self):
        dept = DepartmentCreate(id=1, department="Engineering")
        assert dept.department == "Engineering"

    def test_valid_job(self):
        job = JobCreate(id=1, job="Software Engineer")
        assert job.job == "Software Engineer"
