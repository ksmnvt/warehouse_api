import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.order import (
    create_order,
    delete_order,
    get_order,
    get_order_item,
    get_orders,
    update_order_status,
)
from app.utils.dependencies import get_db
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderItemRead, OrderRead

logger = logging.getLogger(__name__)

# Initialize router with prefix and tags
router = APIRouter(prefix="/orders", tags=["Orders"])

# Create new order endpoint
@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(order: OrderCreate, db: Session = Depends(get_db)):
    return create_order(db, order)

# Get all orders endpoint
@router.get("/", response_model=list[OrderRead])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_orders(db, skip=skip, limit=limit)

# Get single order endpoint
@router.get("/{order_id}", response_model=OrderRead)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = get_order(db, order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

# Update order status endpoint
@router.put("/{order_id}/status", response_model=OrderRead)
def update_order_status_endpoint(
    order_id: int,
    status_value: OrderStatus = Query(
        ...,
        description="Order status",
        enum=[s.value for s in OrderStatus]
    ),
    db: Session = Depends(get_db)
):
    db_order = update_order_status(db, order_id, status_value)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

# Get single order item endpoint
@router.get("/items/{item_id}", response_model=OrderItemRead)
def get_order_item_endpoint(item_id: int, db: Session = Depends(get_db)):
    db_item = get_order_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return db_item

# Delete order endpoint
@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    if not delete_order(db, order_id):
        raise HTTPException(status_code=404, detail="Order not found")
    return

