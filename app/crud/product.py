import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import OrderItem
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)

# Create a new product in the database
def create_product(db: Session, product: ProductCreate):
    try:
        logger.info(f"Creating new product with data: {product.model_dump()}")
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        logger.info(f"Product created successfully with ID: {db_product.id}")
        return db_product
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")

# Get all products from the database
def get_products(db: Session):
    return db.query(Product).all()

# Get a single product by ID
def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

# Update a product in the database
def update_product(db: Session, product_id: int, product: ProductUpdate):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update only the fields that are provided
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

# Delete a product from the database
def delete_product(db: Session, product_id: int):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    has_order_items = (
        db.query(OrderItem).filter(OrderItem.product_id == product_id).count() > 0
    )
    if has_order_items:
        raise HTTPException(
            status_code=400,
            detail="Product cannot be deleted while associated order items exist",
        )

    db.delete(db_product)
    db.commit()