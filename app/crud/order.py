import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import update as sqlalchemy_update

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)


# Create a new order with product availability check and stock update
def create_order(db: Session, order: OrderCreate) -> Order:
    try:
        logger.info("Creating new order with data: %s", order.model_dump())

        if not order.items:
            raise HTTPException(
                status_code=400, detail="Order must contain at least one item"
            )

        # Aggregate quantities to handle multiple items of the same product
        requested_quantities: dict[int, int] = {}
        for item in order.items:
            requested_quantities[item.product_id] = (
                requested_quantities.get(item.product_id, 0) + item.quantity
            )

        product_ids = list(requested_quantities.keys())
        products = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
        }

        # Verify that all products exist
        if len(products) != len(product_ids):
            missing_ids = set(product_ids) - set(products.keys())
            raise HTTPException(
                status_code=404, detail=f"Product with id {next(iter(missing_ids))} not found"
            )

        order_items: list[OrderItem] = []
        for product_id, quantity in requested_quantities.items():
            product = products[product_id]

            # Atomic update to prevent race conditions
            update_stmt = (
                sqlalchemy_update(Product)
                .where(Product.id == product_id)
                .where(Product.stock >= quantity)
                .values(stock=Product.stock - quantity)
            )

            result = db.execute(update_stmt)

            if result.rowcount == 0:
                # The update failed, meaning stock was insufficient
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for product: {product.name}",
                )

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price,
                )
            )
            logger.info("Product %s added to order. Stock updated.", product.name)

        db_order = Order(
            status=OrderStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            items=order_items,
        )

        db.add(db_order)
        db.commit()
        # db.refresh(db_order)  # Removed to prevent "Could not refresh instance" error in threaded tests
        logger.info("Order created successfully with ID: %s", db_order.id)
        return db_order
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error("Error creating order: %s", str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


# Get paginated list of all orders
def get_orders(db: Session, skip: int = 0, limit: int = 100) -> list[Order]:   
    return db.query(Order).offset(skip).limit(limit).all()

# Get single order with related items and products
def get_order(db: Session, order_id: int) -> Order | None:  
    return db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(Order.id == order_id).first()

# Update order status and handle errors
def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Order | None:
    try:
        db_order = get_order(db, order_id)
        if db_order:
            logger.info(f"Current order status: {db_order.status}, new status: {status}")
            # Update status and commit changes
            db_order.status = status
            db.commit()
            db.refresh(db_order)
            logger.info(f"Order status updated successfully to {db_order.status}")
        return db_order
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")

 # Get single order item by ID
def get_order_item(db: Session, item_id: int) -> OrderItem | None:
    return db.query(OrderItem).filter(OrderItem.id == item_id).first()

# Delete order and handle errors
def delete_order(db: Session, order_id: int) -> bool:
    try:
        db_order = get_order(db, order_id)
        if not db_order:
            return False
            
        db.delete(db_order)
        db.commit()
        logger.info(f"Order {order_id} deleted successfully")
        return True
    except Exception as e:
        logger.error(f"Error deleting order: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")
