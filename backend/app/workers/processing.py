import traceback
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models import ProcessedResult, RawDataset, Task
from app.services.processor import compute_summary
from app.workers.celery_app import celery_app


@celery_app.task(
    bind=True,
    acks_late=True,
    max_retries=3,
    default_retry_delay=5,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def process_dataset(self, task_id: str):
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return

        if task.status != "NOT_STARTED":
            return

        # Transition to RUNNING
        task.status = "IN_PROGRESS"
        task.started_at = datetime.now(timezone.utc)
        task.attempts = task.attempts + 1
        task.worker_id = self.request.hostname
        db.commit()

        # Read raw data
        raw = db.scalar(select(RawDataset).where(RawDataset.task_id == task_id))
        if raw is None:
            task.status = "FAILED"
            task.error_message = "Raw dataset not found"
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
            return

        # Process
        result = compute_summary(raw.content)

        # Store result
        processed = ProcessedResult(
            task_id=task.task_id,
            record_count=result["record_count"],
            invalid_records=result["invalid_records"],
            average_value=result["average_value"],
            category_summary=result["category_summary"],
        )
        db.add(processed)

        # Transition to COMPLETED
        task.status = "COMPLETED"
        task.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        db.rollback()
        try:
            task = db.get(Task, task_id)
            if task:
                task.status = "FAILED"
                task.error_message = traceback.format_exc()[-500:]
                task.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
    finally:
        db.close()
