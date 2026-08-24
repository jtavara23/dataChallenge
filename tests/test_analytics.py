from tests.conftest import HEADERS


def _seed_data(client):
    client.post("/api/v1/departments", json=[
        {"id": 1, "department": "Engineering"},
        {"id": 2, "department": "Marketing"},
    ], headers=HEADERS)
    client.post("/api/v1/jobs", json=[
        {"id": 1, "job": "Developer"},
        {"id": 2, "job": "Designer"},
    ], headers=HEADERS)
    client.post("/api/v1/hired-employees", json=[
        {"id": 1, "name": "Alice", "datetime": "2021-02-15T10:00:00Z", "department_id": 1, "job_id": 1},
        {"id": 2, "name": "Bob", "datetime": "2021-05-20T10:00:00Z", "department_id": 1, "job_id": 1},
        {"id": 3, "name": "Charlie", "datetime": "2021-08-10T10:00:00Z", "department_id": 1, "job_id": 2},
        {"id": 4, "name": "Diana", "datetime": "2021-11-01T10:00:00Z", "department_id": 2, "job_id": 2},
        {"id": 5, "name": "Eve", "datetime": "2022-03-01T10:00:00Z", "department_id": 1, "job_id": 1},
    ], headers=HEADERS)


class TestEmployeesByQuarter:
    def test_returns_2021_only(self, client):
        _seed_data(client)
        resp = client.get("/api/v1/analytics/employees-by-quarter", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        total_hires = sum(r["Q1"] + r["Q2"] + r["Q3"] + r["Q4"] for r in data)
        assert total_hires == 4

    def test_quarter_assignment(self, client):
        _seed_data(client)
        resp = client.get("/api/v1/analytics/employees-by-quarter", headers=HEADERS)
        data = resp.json()
        eng_dev = next(r for r in data if r["department"] == "Engineering" and r["job"] == "Developer")
        assert eng_dev["Q1"] == 1
        assert eng_dev["Q2"] == 1
        assert eng_dev["Q3"] == 0
        assert eng_dev["Q4"] == 0

    def test_ordered_alphabetically(self, client):
        _seed_data(client)
        resp = client.get("/api/v1/analytics/employees-by-quarter", headers=HEADERS)
        data = resp.json()
        departments = [r["department"] for r in data]
        assert departments == sorted(departments)

    def test_empty_db_returns_empty_list(self, client):
        resp = client.get("/api/v1/analytics/employees-by-quarter", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []


class TestDepartmentsAboveAverage:
    def test_above_average_only(self, client):
        _seed_data(client)
        resp = client.get("/api/v1/analytics/departments-above-average", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["department"] == "Engineering"
        assert data[0]["hired"] == 3

    def test_ordered_by_hired_desc(self, client):
        _seed_data(client)
        resp = client.get("/api/v1/analytics/departments-above-average", headers=HEADERS)
        data = resp.json()
        hired_counts = [r["hired"] for r in data]
        assert hired_counts == sorted(hired_counts, reverse=True)

    def test_empty_db_returns_empty_list(self, client):
        resp = client.get("/api/v1/analytics/departments-above-average", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []
