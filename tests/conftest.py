import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.product import Product
from app.models.order import Order, OrderItem

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

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Remove the old database file if it exists
    if os.path.exists("test.db"):
        os.remove("test.db")
    
    # Create a new engine
    engine = create_engine("sqlite:///test.db")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        yield
    finally:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        # Remove the database file
        if os.path.exists("test.db"):
            os.remove("test.db") 