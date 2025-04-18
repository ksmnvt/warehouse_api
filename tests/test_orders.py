import pytest
from sqlalchemy.orm import Session
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.crud.order import create_order, get_order, get_orders, update_order_status, delete_order
from app.schemas.order import OrderCreate, OrderItemCreate
from datetime import datetime

# Test data
test_product_data = {
    "name": "Test Product",
    "description": "Test Description",
    "price": 99.99,
    "stock": 100
}

test_order_data = OrderCreate(
    items=[
        OrderItemCreate(
            product_id=1,  # Will be set in the test
            quantity=2
        )
    ]
)

def test_create_order(test_session: Session):
    """Tests order creation"""
    # Create a product
    product = Product(**test_product_data)
    test_session.add(product)
    test_session.commit()
    
    # Update product_id in test data
    test_order_data.items[0].product_id = product.id
    
    # Create an order
    order = create_order(test_session, test_order_data)
    
    # Check that the order is created
    assert order is not None
    assert order.id is not None
    assert order.status == OrderStatus.PENDING
    assert len(order.items) == 1
    assert order.items[0].product_id == product.id
    assert order.items[0].quantity == 2

def test_get_order(test_session: Session):
    """Tests getting an order by ID"""
    # Create a product and an order
    product = Product(**test_product_data)
    test_session.add(product)
    test_session.commit()
    
    test_order_data.items[0].product_id = product.id
    order = create_order(test_session, test_order_data)
    
    # Get the order by ID
    retrieved_order = get_order(test_session, order.id)
    
    # Check that the correct order is retrieved
    assert retrieved_order is not None
    assert retrieved_order.id == order.id
    assert retrieved_order.status == order.status
    assert len(retrieved_order.items) == 1
    assert retrieved_order.items[0].product_id == product.id

def test_get_nonexistent_order(test_session: Session):
    """Tests getting a non-existent order"""
    order = get_order(test_session, 999)
    assert order is None

def test_get_all_orders(test_session: Session):
    """Tests getting all orders"""
    # Create a product
    product = Product(**test_product_data)
    test_session.add(product)
    test_session.commit()
    
    # Create two orders
    test_order_data.items[0].product_id = product.id
    create_order(test_session, test_order_data)
    create_order(test_session, test_order_data)
    
    # Get all orders
    orders = get_orders(test_session)
    
    # Check that all orders are retrieved
    assert len(orders) == 2

def test_update_order_status(test_session: Session):
    """Tests updating order status"""
    # Create a product and an order
    product = Product(**test_product_data)
    test_session.add(product)
    test_session.commit()
    
    test_order_data.items[0].product_id = product.id
    order = create_order(test_session, test_order_data)
    
    # Update order status
    updated_order = update_order_status(test_session, order.id, OrderStatus.CONFIRMED)
    
    # Check that the status is updated
    assert updated_order is not None
    assert updated_order.id == order.id
    assert updated_order.status == OrderStatus.CONFIRMED

def test_delete_order(test_session: Session):
    """Tests order deletion"""
    # Create a product and an order
    product = Product(**test_product_data)
    test_session.add(product)
    test_session.commit()
    
    test_order_data.items[0].product_id = product.id
    order = create_order(test_session, test_order_data)
    
    # Delete the order
    delete_order(test_session, order.id)
    
    # Check that the order is deleted
    deleted_order = get_order(test_session, order.id)
    assert deleted_order is None

def test_create_order_insufficient_stock(test_session: Session):
    """Tests creating an order with insufficient stock"""
    # Create a product with low stock
    product = Product(
        name="Test Product",
        description="Test Description",
        price=99.99,
        stock=1
    )
    test_session.add(product)
    test_session.commit()
    
    # Try to create an order with larger quantity
    test_order_data.items[0].product_id = product.id
    test_order_data.items[0].quantity = 10
    
    with pytest.raises(Exception) as exc_info:
        create_order(test_session, test_order_data)
    
    assert "Not enough stock" in str(exc_info.value) 