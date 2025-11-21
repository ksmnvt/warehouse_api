import logging
from fastapi import FastAPI
from app.routers import product as product_router
from app.routers import order as order_router
from app.database import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(title="Warehouse API")


@app.on_event("startup")
def on_startup():
    """Ensure database schema is available when the app starts."""
    Base.metadata.create_all(bind=engine)


# Include routers
app.include_router(product_router)
app.include_router(order_router)
