import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import product as product_router
from app.routers import order as order_router
from app.database import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database schema is available when the app starts."""
    Base.metadata.create_all(bind=engine)
    yield
    # No shutdown logic needed


# Initialize FastAPI application
app = FastAPI(title="Warehouse API", lifespan=lifespan)


# Include routers
app.include_router(product_router)
app.include_router(order_router)
