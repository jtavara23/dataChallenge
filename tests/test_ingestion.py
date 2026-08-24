from tests.conftest import HEADERS


class TestAuth:
    def test_missing_api_key(self, client):
        resp = client.post("/api/v1/departments", json=[{"id": 1, "department": "Eng"}])
        assert resp.status_code == 401

    def test_invalid_api_key(self, client):
        resp = client.post(
            "/api/v1/departments",
            json=[{"id": 1, "department": "Eng"}],
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401


class TestDepartments:
    def test_insert_valid(self, client):
        resp = client.post(
            "/api/v1/departments",
            json=[{"id": 1, "department": "Engineering"}],
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["inserted"] == 1
        assert data["errors"] == []

    def test_insert_duplicate_id(self, client):
        client.post(
            "/api/v1/departments",
            json=[{"id": 1, "department": "Engineering"}],
            headers=HEADERS,
        )
        resp = client.post(
            "/api/v1/departments",
            json=[{"id": 1, "department": "Marketing"}],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 0
        assert data["errors"][0]["row"] == 1
        assert "already exists" in data["errors"][0]["reasons"][0]

    def test_insert_empty_name(self, client):
        resp = client.post(
            "/api/v1/departments",
            json=[{"id": 1, "department": ""}],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 0
        assert data["errors"][0]["row"] == 1

    def test_batch_partial_success(self, client):
        resp = client.post(
            "/api/v1/departments",
            json=[
                {"id": 1, "department": "Engineering"},
                {"id": 2, "department": ""},
                {"id": 3, "department": "Marketing"},
            ],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 2
        assert len(data["errors"]) == 1
        assert data["errors"][0]["row"] == 2


class TestJobs:
    def test_insert_valid(self, client):
        resp = client.post(
            "/api/v1/jobs",
            json=[{"id": 1, "job": "Software Engineer"}],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 1
        assert data["errors"] == []

    def test_insert_empty_job(self, client):
        resp = client.post(
            "/api/v1/jobs",
            json=[{"id": 1, "job": "  "}],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 0


class TestHiredEmployees:
    def test_insert_valid(self, client):
        client.post("/api/v1/departments", json=[{"id": 1, "department": "Eng"}], headers=HEADERS)
        client.post("/api/v1/jobs", json=[{"id": 1, "job": "Dev"}], headers=HEADERS)

        resp = client.post(
            "/api/v1/hired-employees",
            json=[{
                "id": 1,
                "name": "Alice",
                "datetime": "2021-07-27T16:02:08Z",
                "department_id": 1,
                "job_id": 1,
            }],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 1
        assert data["errors"] == []

    def test_invalid_fk(self, client):
        client.post("/api/v1/departments", json=[{"id": 1, "department": "Eng"}], headers=HEADERS)
        client.post("/api/v1/jobs", json=[{"id": 1, "job": "Dev"}], headers=HEADERS)

        resp = client.post(
            "/api/v1/hired-employees",
            json=[{
                "id": 1,
                "name": "Bob",
                "datetime": "2021-07-27T16:02:08Z",
                "department_id": 999,
                "job_id": 1,
            }],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 0
        assert "department_id 999 not found" in data["errors"][0]["reasons"][0]

    def test_invalid_datetime(self, client):
        client.post("/api/v1/departments", json=[{"id": 1, "department": "Eng"}], headers=HEADERS)
        client.post("/api/v1/jobs", json=[{"id": 1, "job": "Dev"}], headers=HEADERS)

        resp = client.post(
            "/api/v1/hired-employees",
            json=[{
                "id": 1,
                "name": "Charlie",
                "datetime": "not-a-date",
                "department_id": 1,
                "job_id": 1,
            }],
            headers=HEADERS,
        )
        data = resp.json()
        assert data["inserted"] == 0
        assert "ISO 8601" in data["errors"][0]["reasons"][0]

    def test_batch_size_limit(self, client):
        records = [{"id": i, "name": f"User{i}", "datetime": "2021-01-01T00:00:00Z",
                    "department_id": 1, "job_id": 1} for i in range(1001)]
        resp = client.post("/api/v1/hired-employees", json=records, headers=HEADERS)
        assert resp.status_code == 400
        assert "1000" in resp.json()["detail"]
