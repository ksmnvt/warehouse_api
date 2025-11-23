import pytest
from threading import Thread
from queue import Queue
from fastapi import HTTPException
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.crud.order import create_order as create_order_crud
from app.crud.product import create_product as create_product_crud, get_product
from app.database import Base
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.product import ProductCreate

@pytest.fixture(scope="function")
def concurrent_test_engine():
    """
    Create a fresh in-memory SQLite engine that uses a single connection
    across all threads.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout = 5000")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

def test_concurrent_order_creation_prevents_overselling(concurrent_test_engine: Engine):
    """
    Tests that two concurrent requests to order the last item in stock
    result in only one successful order.
    """
    engine = concurrent_test_engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 1. Arrange: Create a product with stock = 1 in a dedicated session
    db_setup = SessionLocal()
    product_id = None
    try:
        product_to_create = ProductCreate(
            name="Concurrent Product",
            description="A product for concurrency testing",
            price=10.0,
            stock=1,
        )
        db_product = create_product_crud(db_setup, product_to_create)
        product_id = db_product.id
        db_setup.commit()
    finally:
        db_setup.close()

    order_to_create = OrderCreate(
        items=[OrderItemCreate(product_id=product_id, quantity=1)]
    )

    results_queue = Queue()

    # 2. Act: Simulate two concurrent order creations, each in its own session
    def order_creation_worker():
        db_worker = SessionLocal()
        try:
            order = create_order_crud(db_worker, order_to_create)
            results_queue.put(order)
        except HTTPException as e:
            results_queue.put(e)
        finally:
            db_worker.close()

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

    failure_exception = failed_orders[0]
    assert failure_exception.status_code == 400
    assert "Not enough stock" in failure_exception.detail

    # Verify the final stock is 0 in a new session to get the latest data
    db_verify = SessionLocal()
    try:
        final_product = get_product(db_verify, product_id)
        assert final_product is not None
        assert final_product.stock == 0
    finally:
        db_verify.close()
