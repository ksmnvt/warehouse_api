from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.database import Base

# Product model representing the products table in the database
class Product(Base):
    __tablename__ = "products"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    # Product name
    name = Column(String, nullable=False)
    # Product description
    description = Column(String, nullable=False)
    # Product price
    price = Column(Float, nullable=False)
    # Available stock quantity
    stock = Column(Integer, nullable=False)
    
    # Relationship with order items
    order_items = relationship("OrderItem", back_populates="product")
