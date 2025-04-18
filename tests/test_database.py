import os
import pytest
from sqlalchemy import inspect
from app.database import Base, engine

def test_database_creation():
    """Tests database creation and structure"""
    # Check that the database file is created
    assert os.path.exists("test.db")
    
    # Check that the products table exists
    inspector = inspect(engine)
    assert "products" in inspector.get_table_names()
    
    # Check table structure
    columns = inspector.get_columns("products")
    column_names = [col["name"] for col in columns]
    
    # Check for all required columns
    required_columns = ["id", "name", "description", "price", "stock"]
    assert all(col in column_names for col in required_columns) 