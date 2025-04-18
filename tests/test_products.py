import pytest
from sqlalchemy.orm import Session
from app.models.product import Product
from app.crud.product import create_product, get_product, get_products, update_product, delete_product
from app.schemas.product import ProductCreate, ProductUpdate
from pydantic import ValidationError

# Test data
test_product_data = ProductCreate(
    name="Test Product",
    description="Test Description",
    price=99.99,
    stock=100
)

def test_create_product(test_session: Session):
    """Tests product creation"""
    # Create a product
    product = create_product(test_session, test_product_data)
    
    # Check that the product is created
    assert product is not None
    assert product.id is not None
    assert product.name == test_product_data.name
    assert product.description == test_product_data.description
    assert product.price == test_product_data.price
    assert product.stock == test_product_data.stock

def test_get_product(test_session: Session):
    """Tests getting a product by ID"""
    # Create a product
    product = create_product(test_session, test_product_data)
    
    # Get the product by ID
    retrieved_product = get_product(test_session, product.id)
    
    # Check that the correct product is retrieved
    assert retrieved_product is not None
    assert retrieved_product.id == product.id
    assert retrieved_product.name == product.name

def test_get_nonexistent_product(test_session: Session):
    """Tests getting a non-existent product"""
    product = get_product(test_session, 999)
    assert product is None

def test_get_all_products(test_session: Session):
    """Tests getting all products"""
    # Create two products
    create_product(test_session, test_product_data)
    create_product(test_session, ProductCreate(
        name="Another Product",
        description="Another Description",
        price=199.99,
        stock=50
    ))
    
    # Get all products
    products = get_products(test_session)
    
    # Check that all products are retrieved
    assert len(products) == 2

def test_update_product(test_session: Session):
    """Tests updating a product"""
    # Create a product
    product = create_product(test_session, test_product_data)
    
    # Update the product
    update_data = ProductUpdate(
        name="Updated Product",
        description="Updated Description",
        price=149.99,
        stock=75
    )
    updated_product = update_product(test_session, product.id, update_data)
    
    # Check that the product is updated
    assert updated_product is not None
    assert updated_product.id == product.id
    assert updated_product.name == update_data.name
    assert updated_product.description == update_data.description
    assert updated_product.price == update_data.price
    assert updated_product.stock == update_data.stock

def test_delete_product(test_session: Session):
    """Tests product deletion"""
    # Create a product
    product = create_product(test_session, test_product_data)
    
    # Delete the product
    delete_product(test_session, product.id)
    
    # Check that the product is deleted
    deleted_product = get_product(test_session, product.id)
    assert deleted_product is None

def test_create_product_invalid_data(test_session: Session):
    """Tests creating a product with invalid data"""
    # Try to create a product with negative price
    invalid_data = {
        "name": "Invalid Product",
        "description": "Invalid Description",
        "price": -99.99,  # Negative price
        "stock": 100
    }
    
    # Expect Pydantic validation error
    with pytest.raises(ValidationError) as exc_info:
        # Create Pydantic model inside try-except block
        product_create = ProductCreate(**invalid_data)
        create_product(test_session, product_create)
    
    # Check that the error contains the correct message
    assert "Input should be greater than 0" in str(exc_info.value) 