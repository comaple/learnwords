import os
import pytest

# Ensure tests use the local sqlite test DB
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal


@pytest.fixture(scope='function')
def db_session():
    """Provide a fresh DB session for each test."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope='module')
def client():
    """Provide a shared FastAPI test client for all tests in a module."""
    return TestClient(app)
