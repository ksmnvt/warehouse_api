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

from app.database import Base
from app.utils.dependencies import get_db
from app.main import app
from app.models.product import Product
from app.models.order import Order, OrderItem
from fastapi.testclient import TestClient
import json

# Global list to store report data
report_data = []

# Custom TestClient for reporting
class ReportingTestClient(TestClient):
    def request(self, method, url, **kwargs):
        response = super().request(method, url, **kwargs)

        response_body = ""
        try:
            response_body = response.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            response_body = response.text

        report_data.append(
            {
                "request": {
                    "method": method,
                    "url": url,
                    "params": kwargs.get("params"),
                    "json": kwargs.get("json"),
                },
                "response": {"status_code": response.status_code, "body": response_body},
            }
        )
        return response

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
    with ReportingTestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def pytest_sessionfinish(session):
    """
    Hook to generate a report after the test session finishes.
    """
    if not report_data:
        return

    report_path = ROOT_DIR / "test_report.txt"
    with open(report_path, "w") as f:
        for record in report_data:
            req = record["request"]
            res = record["response"]

            f.write("=" * 80 + "\n")
            f.write(f"Request: {req['method']} {req['url']}\n")
            if req["params"]:
                f.write(f"Params: {json.dumps(req['params'], indent=2)}\n")
            if req["json"]:
                f.write(f"Body: {json.dumps(req['json'], indent=2)}\n")

            f.write("-" * 80 + "\n")
            f.write(f"Response: {res['status_code']}\n")
            if res["body"]:
                if isinstance(res["body"], dict) or isinstance(res["body"], list):
                    f.write(f"Body: {json.dumps(res['body'], indent=2)}\n")
                else:
                    f.write(f"Body: {res['body']}\n")
            f.write("=" * 80 + "\n\n")

    # Clear the report data for the next run
    report_data.clear()
