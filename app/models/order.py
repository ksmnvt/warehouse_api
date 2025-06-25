from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class OrderStatus(enum.Enum):
    PENDING = "pending"            # Order created but not yet confirmed (e.g., awaiting payment)
    CONFIRMED = "confirmed"        # Order confirmed (payment received or manually approved)
    IN_PROGRESS = "in progress"    # Order is being processed (e.g., packed at the warehouse)
    SHIPPED = "shipped"            # Order has been shipped
    DELIVERED = "delivered"        # Order has been delivered to the customer
    COMPLETED = "completed"        # Order successfully completed (usually confirmed by customer)
    CANCELLED = "cancelled"        # Order was cancelled by the customer or the store
    REFUNDED = "refunded"          # Order was returned and the payment refunded
    FAILED = "failed"              # Error occurred during order placement or payment

# Order model representing the orders table in the database
class Order(Base):
    __tablename__ = "orders"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING, server_default=OrderStatus.PENDING.value)
    
    price = Column(Float, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

