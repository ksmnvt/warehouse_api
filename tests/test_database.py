import pytest
from sqlalchemy import inspect

def test_database_creation(test_engine):
    """Tests database creation and structure"""
    inspector = inspect(test_engine)
    assert "products" in inspector.get_table_names()
    
    # Check table structure
    columns = inspector.get_columns("products")
    column_names = [col["name"] for col in columns]
    
    # Check for all required columns
    required_columns = ["id", "name", "description", "price", "stock"]
    assert all(col in column_names for col in required_columns) 