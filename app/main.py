import logging
from fastapi import FastAPI
from app.routers import product as product_router
from app.routers import order as order_router
from app.database import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(title="Warehouse API")

# Include routers
app.include_router(product_router)
app.include_router(order_router)
