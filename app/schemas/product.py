from pydantic import BaseModel, Field
from typing import Optional

# Base product schema with common fields
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

# Schema for creating a new product
class ProductCreate(ProductBase):
    pass

# Schema for reading product data
class ProductRead(ProductBase):
    id: int

    class Config:
        # Enable ORM mode for SQLAlchemy models
        from_attributes = True

# Schema for updating a product with optional fields
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)

# Schema for success message response
class SuccessMessage(BaseModel):
    message: str
    product: Optional[ProductRead] = None
