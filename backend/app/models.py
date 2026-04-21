import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_STARTED", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    worker_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    raw_dataset: Mapped[Optional["RawDataset"]] = relationship(
        "RawDataset", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    processed_result: Mapped[Optional["ProcessedResult"]] = relationship(
        "ProcessedResult", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )


class RawDataset(Base):
    __tablename__ = "raw_datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    task: Mapped["Task"] = relationship("Task", back_populates="raw_dataset")


class ProcessedResult(Base):
    __tablename__ = "processed_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    invalid_records: Mapped[int] = mapped_column(Integer, nullable=False)
    average_value: Mapped[Optional[float]] = mapped_column(Numeric(precision=20, scale=6), nullable=True)
    category_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    task: Mapped["Task"] = relationship("Task", back_populates="processed_result")
