import time
from datetime import datetime
from typing import Any, Optional


def _is_valid_record(record: dict) -> bool:
    required = ("id", "timestamp", "value", "category")
    for key in required:
        if key not in record:
            return False

    try:
        float(record["value"])
    except (TypeError, ValueError):
        return False

    try:
        datetime.fromisoformat(str(record["timestamp"]).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False

    return True


def compute_summary(dataset: dict) -> dict:
    """Pure function. Given a parsed dataset, return the result payload."""
    records = dataset.get("records", [])
    record_count = len(records)

    valid_records = [r for r in records if _is_valid_record(r)]
    invalid_records = record_count - len(valid_records)

    values = [float(r["value"]) for r in valid_records]
    average_value: Optional[float] = sum(values) / len(values) if values else None

    category_summary: dict[str, int] = {}
    for r in valid_records:
        cat = str(r["category"])
        category_summary[cat] = category_summary.get(cat, 0) + 1

    # Simulate long-running computation
    time.sleep(15)

    return {
        "record_count": record_count,
        "invalid_records": invalid_records,
        "average_value": average_value,
        "category_summary": category_summary,
    }
