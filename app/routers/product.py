from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, SuccessMessage
from app.crud import product as crud
from app.database import SessionLocal
from typing import List

# Initialize router with prefix and tags
router = APIRouter(prefix="/products", tags=["Products"])

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create new product endpoint
@router.post("/", response_model=SuccessMessage)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.create_product(db, product)
    return SuccessMessage(
        message="Product successfully created",
        product=db_product
    )

# Get all products endpoint
@router.get("/", response_model=List[ProductRead])
def list_products(db: Session = Depends(get_db)):
    return crud.get_products(db)

# Get product by ID endpoint
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# Update product endpoint
@router.put("/{product_id}", response_model=SuccessMessage)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = crud.update_product(db, product_id, product)
    return SuccessMessage(
        message="Product successfully updated",
        product=db_product
    )

# Delete product endpoint
@router.delete("/{product_id}", response_model=SuccessMessage)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    crud.delete_product(db, product_id)
    return SuccessMessage(
        message="Product successfully deleted"
    )
