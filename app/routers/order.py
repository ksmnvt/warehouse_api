from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.order import OrderCreate, OrderRead, OrderStatus, SuccessMessage, OrderItemRead
from app.models.order import OrderStatus
from app.crud.order import create_order, get_orders, get_order, update_order_status, get_order_item, delete_order
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router with prefix and tags
router = APIRouter(prefix="/orders", tags=["Orders"])

# Create new product endpoint
@router.post("/", response_model=SuccessMessage)
def create_order_endpoint(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = create_order(db, order)
    return SuccessMessage(
        message="Order successfully created",
        order=OrderRead.from_orm(db_order)
    )

# Get all orders endpoint
@router.get("/", response_model=list[OrderRead])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = get_orders(db)
    return [OrderRead.from_orm(order) for order in orders]

# Get single order endpoint
@router.get("/{order_id}", response_model=OrderRead)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = get_order(db, order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderRead.from_orm(db_order)

# Update order status endpoint
@router.put("/{order_id}/status", response_model=OrderRead)
def update_order_status_endpoint(
    order_id: int,
    status: OrderStatus = Query(
        ...,
        description="Order status",
        enum=[s.value for s in OrderStatus]
    ),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Updating order {order_id} status to {status}")
        db_order = update_order_status(db, order_id, status)
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        return OrderRead.from_orm(db_order)
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating order status: {str(e)}"
        )

# Get single order item endpoint
@router.get("/items/{item_id}", response_model=OrderItemRead)
def get_order_item_endpoint(item_id: int, db: Session = Depends(get_db)):
    db_item = get_order_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return OrderItemRead.from_orm(db_item)

# Delete order endpoint
@router.delete("/{order_id}", response_model=SuccessMessage)
def delete_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    try:
        if delete_order(db, order_id):
            return SuccessMessage(message=f"Order {order_id} deleted successfully")
        raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        logger.error(f"Error deleting order: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting order: {str(e)}"
        )

