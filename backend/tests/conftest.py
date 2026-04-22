from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine, get_db
from app.main import app

from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _mock_celery_delay():
    """Prevent real Celery tasks from firing during tests."""
    with patch("app.api.tasks.process_dataset.delay", return_value=MagicMock()) as mock:
        yield mock


@pytest.fixture()
def db():
    """Provide a transactional DB session that rolls back after each test."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session):
    """FastAPI TestClient with the DB dependency overridden."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
