from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, computed_field

from app.models.order import OrderStatus

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
    price: float

    @computed_field
    @property
    def total_price(self) -> float:
        return self.price * self.quantity

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


# Schema for reading product data
class OrderRead(BaseModel):
    id: int
    created_at: datetime
    status: OrderStatus
    items: List[OrderItemRead] = Field(default_factory=list)

    @computed_field
    @property
    def order_total(self) -> float:
        return sum(item.total_price for item in self.items)

    model_config = ConfigDict(from_attributes=True)


# Schema for success message response
class SuccessMessage(BaseModel):
    message: str
    order: Optional[OrderRead] = None
