import io
import json


# ── Happy path ──


def test_upload_valid_dataset(client, _mock_celery_delay):
    payload = {
        "dataset_id": "ds-test-001",
        "records": [
            {"id": 1, "timestamp": "2024-06-01T10:00:00Z", "value": 10, "category": "A"},
        ],
    }
    resp = client.post(
        "/api/tasks",
        files={"file": ("test.json", io.BytesIO(json.dumps(payload).encode()), "application/json")},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert "task_id" in body
    assert body["status"] == "NOT_STARTED"
    assert "created_at" in body
    _mock_celery_delay.assert_called_once_with(body["task_id"])


def test_upload_multiple_files_sequentially(client):
    payload = {
        "dataset_id": "ds-multi",
        "records": [
            {"id": 1, "timestamp": "2024-01-01T00:00:00Z", "value": 5, "category": "X"},
        ],
    }
    data = json.dumps(payload).encode()

    resp1 = client.post("/api/tasks", files={"file": ("a.json", io.BytesIO(data), "application/json")})
    resp2 = client.post("/api/tasks", files={"file": ("b.json", io.BytesIO(data), "application/json")})

    assert resp1.status_code == 202
    assert resp2.status_code == 202
    assert resp1.json()["task_id"] != resp2.json()["task_id"]


# ── Negative paths ──


def test_upload_invalid_json(client):
    resp = client.post(
        "/api/tasks",
        files={"file": ("bad.json", io.BytesIO(b'{"broken json'), "application/json")},
    )
    assert resp.status_code == 422
    assert "Invalid JSON" in resp.json()["detail"]


def test_upload_missing_dataset_id(client):
    payload = {"records": [{"id": 1, "timestamp": "2024-01-01T00:00:00Z", "value": 1, "category": "A"}]}
    resp = client.post(
        "/api/tasks",
        files={"file": ("no_id.json", io.BytesIO(json.dumps(payload).encode()), "application/json")},
    )
    assert resp.status_code == 422


def test_upload_missing_records(client):
    payload = {"dataset_id": "ds-no-records"}
    resp = client.post(
        "/api/tasks",
        files={"file": ("no_rec.json", io.BytesIO(json.dumps(payload).encode()), "application/json")},
    )
    assert resp.status_code == 422


def test_upload_empty_file(client):
    resp = client.post(
        "/api/tasks",
        files={"file": ("empty.json", io.BytesIO(b""), "application/json")},
    )
    assert resp.status_code == 422


def test_upload_not_json_content(client):
    resp = client.post(
        "/api/tasks",
        files={"file": ("readme.txt", io.BytesIO(b"hello world"), "text/plain")},
    )
    assert resp.status_code == 422


def test_upload_no_file_attached(client):
    resp = client.post("/api/tasks")
    assert resp.status_code == 422
