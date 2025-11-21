from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.crud import product as crud
from app.database import get_db
from typing import List

# Initialize router with prefix and tags
router = APIRouter(prefix="/products", tags=["Products"])

# Create new product endpoint
@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, product)

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
@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    return crud.update_product(db, product_id, product)

# Delete product endpoint
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    crud.delete_product(db, product_id)
    return
