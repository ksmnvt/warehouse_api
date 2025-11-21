import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)


# Create a new order with product availability check and stock update
def create_order(db: Session, order: OrderCreate) -> Order:
    try:
        logger.info("Creating new order with data: %s", order.model_dump())

        product_ids = [item.product_id for item in order.items]
        if not product_ids:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")

        # Aggregate quantities per product to avoid duplicate queries
        requested_quantities: dict[int, int] = {}
        for item in order.items:
            requested_quantities[item.product_id] = requested_quantities.get(item.product_id, 0) + item.quantity

        query = db.query(Product).filter(Product.id.in_(product_ids))
        if db.bind and db.bind.dialect.name != "sqlite":
            query = query.with_for_update()

        products = {product.id: product for product in query.all()}

        missing_products = set(product_ids) - set(products.keys())
        if missing_products:
            missing_id = next(iter(missing_products))
            raise HTTPException(status_code=404, detail=f"Product with id {missing_id} not found")

        insufficient_stock = []
        for product_id, quantity in requested_quantities.items():
            product = products[product_id]
            if product.stock < quantity:
                insufficient_stock.append(
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "requested": quantity,
                        "available": product.stock,
                    }
                )

        if insufficient_stock:
            error_lines = [
                f"- {item['product_name']}: requested {item['requested']}, available {item['available']}"
                for item in insufficient_stock
            ]
            raise HTTPException(
                status_code=400,
                detail="Not enough stock for products:\n" + "\n".join(error_lines),
            )

        total_price = 0.0
        order_items: list[OrderItem] = []
        for product_id, quantity in requested_quantities.items():
            product = products[product_id]
            product.stock -= quantity
            total_price += product.price * quantity
            order_items.append(
                OrderItem(
                    product_id=product_id,
                    quantity=quantity,
                )
            )
            logger.info("Product %s added to order. Stock: %s", product.name, product.stock)

        db_order = Order(
            status=OrderStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            items=order_items,
        )

        db.add(db_order)
        db.commit()
        db.refresh(db_order)
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
    return (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .offset(skip)
        .limit(limit)
        .all()
    )

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

