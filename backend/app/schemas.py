import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class DatasetRecord(BaseModel):
    id: Any
    timestamp: Any
    value: Any
    category: Any


class DatasetPayload(BaseModel):
    dataset_id: str
    records: list[dict[str, Any]]


class TaskCreate(BaseModel):
    task_id: uuid.UUID
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskSummary(BaseModel):
    task_id: uuid.UUID
    dataset_id: str
    filename: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TaskDetail(TaskSummary):
    error_message: Optional[str] = None
    attempts: int = 0
    worker_id: Optional[str] = None


class TaskListResponse(BaseModel):
    items: list[TaskSummary]
    total: int


class TaskResult(BaseModel):
    dataset_id: str
    record_count: int
    category_summary: dict[str, int]
    average_value: Optional[float]
    invalid_records: int
    processed_at: datetime

    model_config = {"from_attributes": True}
