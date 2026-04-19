import json
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import ProcessedResult, RawDataset, Task
from app.schemas import (
    DatasetPayload,
    TaskCreate,
    TaskDetail,
    TaskListResponse,
    TaskResult,
    TaskSummary,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=TaskCreate)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raw = await file.read()

    if len(raw) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    try:
        payload_dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON: {exc}",
        )

    try:
        payload = DatasetPayload.model_validate(payload_dict)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    task_id = uuid.uuid4()

    task = Task(
        task_id=task_id,
        dataset_id=payload.dataset_id,
        filename=file.filename or "upload.json",
        status="PENDING",
    )
    db.add(task)

    raw_dataset = RawDataset(
        task_id=task_id,
        content=payload_dict,
    )
    db.add(raw_dataset)

    db.commit()
    db.refresh(task)

    return task


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status_filter: Optional[Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]] = Query(
        default=None, alias="status"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    q = select(Task)
    if status_filter:
        q = q.where(Task.status == status_filter)

    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(Task.created_at.desc()).limit(limit).offset(offset)).all()

    return TaskListResponse(items=list(items), total=total or 0)


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


@router.get("/{task_id}/result", response_model=TaskResult)
def get_task_result(task_id: uuid.UUID, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if task.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is not completed yet (current status: {task.status}).",
        )
    result = db.scalar(select(ProcessedResult).where(ProcessedResult.task_id == task_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result record missing.")
    return TaskResult(
        dataset_id=task.dataset_id,
        record_count=result.record_count,
        category_summary=result.category_summary,
        average_value=float(result.average_value) if result.average_value is not None else None,
        invalid_records=result.invalid_records,
        processed_at=result.processed_at,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if task.status == "RUNNING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a RUNNING task.",
        )

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
