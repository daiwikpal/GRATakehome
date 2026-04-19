from fastapi import FastAPI

from app.api import health, tasks

app = FastAPI(
    title="Data Processing System",
    description="Async dataset processing via Celery + RabbitMQ",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(tasks.router, prefix="/api")
app.include_router(health.router, prefix="/api")
