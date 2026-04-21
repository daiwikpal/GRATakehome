from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, tasks

app = FastAPI(
    title="Data Processing System",
    description="Async dataset processing via Celery + RabbitMQ",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api")
app.include_router(health.router, prefix="/api")
