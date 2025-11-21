from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.models.product import Product
from app.models.order import OrderItem

# Order status enum
class OrderStatus(str, Enum):
    PENDING = "pending"            # Order created but not yet confirmed (e.g., awaiting payment)
    CONFIRMED = "confirmed"        # Order confirmed (payment received or manually approved)
    IN_PROGRESS = "in progress"    # Order is being processed (e.g., packed at the warehouse)
    SHIPPED = "shipped"            # Order has been shipped
    DELIVERED = "delivered"        # Order has been delivered to the customer
    COMPLETED = "completed"        # Order successfully completed (usually confirmed by customer)
    CANCELLED = "cancelled"        # Order was cancelled by the customer or the store
    REFUNDED = "refunded"          # Order was returned and the payment refunded
    FAILED = "failed"              # Error occurred during order placement or payment

# Order item base model
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

# Order item create model
class OrderItemCreate(OrderItemBase):
    pass

# Product info model
class ProductInfo(BaseModel):
    id: int
    name: str
    price: float
    model_config = ConfigDict(from_attributes=True)

# Order item read model
class OrderItemRead(BaseModel):
    item_id: int = Field(alias="id")
    product: ProductInfo
    quantity: int

    @computed_field
    @property
    def total_price(self) -> float:
        return self.product.price * self.quantity

    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    order_total: float = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

# Schema for reading product data
class OrderRead(BaseModel):
    id: int
    created_at: datetime
    status: OrderStatus
    items: List[OrderItemRead] = []
    order_total: float = Field(alias="price")

    model_config = ConfigDict(from_attributes=True)


# Schema for success message response
class SuccessMessage(BaseModel):
    message: str
    order: Optional[OrderRead] = None
