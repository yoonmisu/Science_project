from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.database import engine, Base
from app.routers import species, search, regions, endangered
from app.cache import init_cache, health_check as cache_health_check

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Verde API...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Initialize Redis cache
    if init_cache():
        logger.info("Redis cache connected")
    else:
        logger.warning("Redis cache not available - running without cache")

    yield

    # Shutdown
    logger.info("Shutting down Verde API...")


app = FastAPI(
    title="Verde Biodiversity API",
    description="API for Verde biodiversity data visualization platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(species.router, prefix=settings.api_v1_prefix)
app.include_router(search.router, prefix=settings.api_v1_prefix)
app.include_router(regions.router, prefix=settings.api_v1_prefix)
app.include_router(endangered.router, prefix=settings.api_v1_prefix)


@app.get("/")
def root():
    return {
        "message": "Verde Biodiversity API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for API and services"""
    cache_status = cache_health_check()

    return {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "cache": cache_status
        }
    }


@app.get("/health/cache")
def cache_health():
    """Detailed cache health check"""
    return cache_health_check()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug
    )
