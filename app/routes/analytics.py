from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/employees-by-quarter")
def employees_hired_by_quarter(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            d.department,
            j.job,
            SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 1 AND 3 THEN 1 ELSE 0 END) AS Q1,
            SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 4 AND 6 THEN 1 ELSE 0 END) AS Q2,
            SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 7 AND 9 THEN 1 ELSE 0 END) AS Q3,
            SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 10 AND 12 THEN 1 ELSE 0 END) AS Q4
        FROM hired_employees he
        JOIN departments d ON he.department_id = d.id
        JOIN jobs j ON he.job_id = j.id
        WHERE strftime('%Y', he.datetime) = '2021'
        GROUP BY d.department, j.job
        ORDER BY d.department, j.job
    """)

    results = db.execute(query).fetchall()
    return [
        {
            "department": row.department,
            "job": row.job,
            "Q1": row.Q1,
            "Q2": row.Q2,
            "Q3": row.Q3,
            "Q4": row.Q4,
        }
        for row in results
    ]


@router.get("/departments-above-average")
def departments_above_average_hiring(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            d.id,
            d.department,
            COUNT(he.id) AS hired
        FROM hired_employees he
        JOIN departments d ON he.department_id = d.id
        WHERE strftime('%Y', he.datetime) = '2021'
        GROUP BY d.id, d.department
        HAVING COUNT(he.id) > (
            SELECT CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT department_id)
            FROM hired_employees
            WHERE strftime('%Y', datetime) = '2021'
        )
        ORDER BY hired DESC
    """)

    results = db.execute(query).fetchall()
    return [
        {
            "id": row.id,
            "department": row.department,
            "hired": row.hired,
        }
        for row in results
    ]
