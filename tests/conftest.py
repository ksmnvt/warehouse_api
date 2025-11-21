import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import Base, get_db
from app.main import app
from app.models.product import Product
from app.models.order import Order, OrderItem
from fastapi.testclient import TestClient
import json

# Global list to store report data
report_data = []

# Use in-memory database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create a test engine
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

# Create a test session
@pytest.fixture(scope="function")
def test_session(test_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        # Clear all tables after each test
        session.query(OrderItem).delete()
        session.query(Order).delete()
        session.query(Product).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(test_session):
    def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
