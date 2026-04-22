from unittest.mock import patch

from app.services.processor import compute_summary


def _make_record(id=1, timestamp="2024-06-01T10:00:00Z", value=10, category="A", **overrides):
    rec = {"id": id, "timestamp": timestamp, "value": value, "category": category}
    rec.update(overrides)
    return rec


def _run(dataset):
    with patch("app.services.processor.time.sleep"):
        return compute_summary(dataset)


# ── Happy path ──


def test_all_valid_records():
    dataset = {
        "records": [
            _make_record(id=1, value=10, category="A"),
            _make_record(id=2, value=20, category="B"),
            _make_record(id=3, value=30, category="A"),
        ]
    }
    result = _run(dataset)
    assert result["record_count"] == 3
    assert result["invalid_records"] == 0
    assert result["average_value"] == 20.0
    assert result["category_summary"] == {"A": 2, "B": 1}


def test_mixed_valid_and_invalid():
    dataset = {
        "records": [
            _make_record(id=1, value=10, category="A"),
            _make_record(id=2, value=20, category="B"),
            _make_record(id=3, value=60, category="A"),
            {"id": 4, "timestamp": "bad-timestamp", "value": 40, "category": "C"},
            {"timestamp": "2024-06-05T14:00:00Z", "value": 25, "category": "B"},  # missing id
        ]
    }
    result = _run(dataset)
    assert result["record_count"] == 5
    assert result["invalid_records"] == 2
    assert result["average_value"] == 30.0
    assert result["category_summary"] == {"A": 2, "B": 1}


def test_single_record():
    dataset = {"records": [_make_record(id=1, value=42, category="X")]}
    result = _run(dataset)
    assert result["record_count"] == 1
    assert result["invalid_records"] == 0
    assert result["average_value"] == 42.0
    assert result["category_summary"] == {"X": 1}


# ── Negative / edge paths ──


def test_all_invalid_records():
    dataset = {
        "records": [
            {"id": 1, "timestamp": "not-a-date", "value": 10, "category": "A"},
            {"id": 2, "timestamp": "2024-01-01T00:00:00Z", "value": "abc", "category": "B"},
            {"timestamp": "2024-01-01T00:00:00Z", "value": 30, "category": "C"},  # missing id
        ]
    }
    result = _run(dataset)
    assert result["record_count"] == 3
    assert result["invalid_records"] == 3
    assert result["average_value"] is None
    assert result["category_summary"] == {}


def test_empty_records_list():
    result = _run({"records": []})
    assert result["record_count"] == 0
    assert result["invalid_records"] == 0
    assert result["average_value"] is None
    assert result["category_summary"] == {}


def test_missing_records_key():
    result = _run({"dataset_id": "ds-no-records"})
    assert result["record_count"] == 0
    assert result["invalid_records"] == 0
    assert result["average_value"] is None


def test_record_missing_id():
    dataset = {"records": [{"timestamp": "2024-01-01T00:00:00Z", "value": 10, "category": "A"}]}
    result = _run(dataset)
    assert result["invalid_records"] == 1


def test_record_missing_timestamp():
    dataset = {"records": [{"id": 1, "value": 10, "category": "A"}]}
    result = _run(dataset)
    assert result["invalid_records"] == 1


def test_record_bad_timestamp():
    dataset = {"records": [{"id": 1, "timestamp": "not-a-date", "value": 10, "category": "A"}]}
    result = _run(dataset)
    assert result["invalid_records"] == 1


def test_record_non_numeric_value():
    dataset = {"records": [{"id": 1, "timestamp": "2024-01-01T00:00:00Z", "value": "abc", "category": "A"}]}
    result = _run(dataset)
    assert result["invalid_records"] == 1


def test_record_missing_value():
    dataset = {"records": [{"id": 1, "timestamp": "2024-01-01T00:00:00Z", "category": "A"}]}
    result = _run(dataset)
    assert result["invalid_records"] == 1
