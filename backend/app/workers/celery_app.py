from celery import Celery

from app.config import settings

celery_app = Celery(
    "gra_worker",
    broker=settings.BROKER_URL,
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    include=["app.workers.processing"],
)
