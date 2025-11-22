from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import species_router, search_router, regions_router, endangered_router
from app.services.species_service import SpeciesService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Verde 생물다양성 플랫폼 API - 지역별 생물 다양성 데이터를 제공합니다.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API versioning
API_V1_PREFIX = "/api/v1"

app.include_router(species_router, prefix=API_V1_PREFIX)
app.include_router(search_router, prefix=API_V1_PREFIX)
app.include_router(regions_router, prefix=API_V1_PREFIX)
app.include_router(endangered_router, prefix=API_V1_PREFIX)


@app.get("/", tags=["Health"])
def root():
    """API 루트 엔드포인트"""
    return {
        "success": True,
        "message": "Verde Biodiversity API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_base": API_V1_PREFIX
    }


@app.get("/health", tags=["Health"])
def health_check():
    """헬스 체크"""
    return {
        "success": True,
        "status": "healthy"
    }


@app.get(f"{API_V1_PREFIX}/stats", tags=["Statistics"])
def get_global_stats(db: Session = Depends(get_db)):
    """전체 통계"""
    try:
        service = SpeciesService(db)
        stats = service.get_biodiversity_summary()

        logger.info("Global stats fetched")

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error fetching global stats: {str(e)}")
        return {
            "success": False,
            "error": "서버 오류가 발생했습니다"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
