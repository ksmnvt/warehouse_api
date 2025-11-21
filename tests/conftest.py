import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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

class ReportingTestClient(TestClient):
    def request(self, method, url, **kwargs):
        report = {
            "endpoint": f"{method} {url}",
            "request": kwargs.get("json"),
        }

        response = super().request(method, url, **kwargs)

        report["response"] = {
            "status_code": response.status_code,
            "body": response.json() if response.content else None
        }
        report_data.append(report)
        return response

@pytest.fixture(scope="function")
def client(test_session):
    def override_get_db():
        try:
            yield test_session
        finally:
            test_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with ReportingTestClient(app) as c:
        yield c

def pytest_sessionfinish(session):
    with open("test_report.txt", "w") as f:
        for i, report in enumerate(report_data):
            f.write(f"Test {i+1}\n")
            f.write("="*20 + "\n")
            f.write(f"Endpoint: {report['endpoint']}\n")
            f.write(f"Request: {json.dumps(report['request'], indent=2)}\n")
            f.write(f"Response:\n")
            f.write(f"  Status Code: {report['response']['status_code']}\n")
            f.write(f"  Body: {json.dumps(report['response']['body'], indent=2)}\n")
            f.write("\n")
