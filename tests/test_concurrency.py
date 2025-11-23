import pytest
from threading import Thread
from queue import Queue
from fastapi import HTTPException
from sqlalchemy.orm import sessionmaker, Session
from app.crud.order import create_order as create_order_crud
from app.crud.product import create_product as create_product_crud, get_product
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.product import ProductCreate

def test_concurrent_order_creation_prevents_overselling(test_session: Session):
    """
    Tests that two concurrent requests to order the last item in stock
    result in only one successful order.
    """
    # 1. Arrange: Create a product with stock = 1
    product_to_create = ProductCreate(
        name="Concurrent Product",
        description="A product for concurrency testing",
        price=10.0,
        stock=1,
    )
    db_product = create_product_crud(test_session, product_to_create)

    order_to_create = OrderCreate(
        items=[OrderItemCreate(product_id=db_product.id, quantity=1)]
    )

    results_queue = Queue()

    # Create a new session for each thread
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_session.bind)

    # 2. Act: Simulate two concurrent order creations in separate threads
    def order_creation_worker():
        db = SessionLocal()
        try:
            order = create_order_crud(db, order_to_create)
            results_queue.put(order)
        except HTTPException as e:
            results_queue.put(e)
        finally:
            db.close()

    thread1 = Thread(target=order_creation_worker)
    thread2 = Thread(target=order_creation_worker)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    # 3. Assert: Verify that only one order succeeded
    results = [results_queue.get(), results_queue.get()]

    successful_orders = [r for r in results if not isinstance(r, HTTPException)]
    failed_orders = [r for r in results if isinstance(r, HTTPException)]

    assert len(successful_orders) == 1
    assert len(failed_orders) == 1

    # Verify the exception details for the failed order
    failure_exception = failed_orders[0]
    assert failure_exception.status_code == 400
    assert "Not enough stock" in failure_exception.detail

    # Verify the final stock is 0
    test_session.expire(db_product)
    final_product = get_product(test_session, db_product.id)
    assert final_product is not None
    assert final_product.stock == 0
