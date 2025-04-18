from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate
from app.models.product import Product
import logging
from datetime import datetime

# Configure logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

 # Create a new order with product availability check and stock update
def create_order(db: Session, order: OrderCreate) -> Order:   
    try:
        logger.info(f"Creating new order with data: {order.dict()}")
        
        # Initialize variables for order processing
        total_price = 0
        order_items = []
        insufficient_stock = []
        
        # First pass: validate all products and check stock
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
            
            if product.stock < item.quantity:
                insufficient_stock.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "requested": item.quantity,
                    "available": product.stock
                })
        
        # Return error if any product has insufficient stock
        if insufficient_stock:
            error_message = "Not enough stock for products:\n"
            for item in insufficient_stock:
                error_message += f"- {item['product_name']}: requested {item['requested']}, available {item['available']}\n"
            raise HTTPException(status_code=400, detail=error_message)
        
        # Second pass: create order items and update stock
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            
            # Update product stock and calculate total price
            product.stock -= item.quantity
            total_price += product.price * item.quantity
            
            # Create order item
            db_item = OrderItem(
                product_id=item.product_id,
                quantity=item.quantity
            )
            order_items.append(db_item)
            logger.info(f"Product {product.name} added to order. Stock: {product.stock}")

        # Create and save the order
        db_order = Order(
            status=OrderStatus.PENDING,
            price=total_price,
            created_at=datetime.utcnow(),
            items=order_items
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        logger.info(f"Order created successfully with ID: {db_order.id}")
        return db_order
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
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

