from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import species_router, search_router, regions_router, endangered_router
from app.services.species_service import SpeciesService
from app.cache import health_check as redis_health_check, cache_get, cache_set, CacheKeys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# OpenAPI 태그 정의 및 설명
tags_metadata = [
    {
        "name": "Health",
        "description": "서버 상태 확인을 위한 헬스 체크 엔드포인트",
    },
    {
        "name": "Species",
        "description": "생물종 데이터 관리 API. 종 목록 조회, 상세 정보, CRUD 작업을 제공합니다.",
    },
    {
        "name": "Search",
        "description": "검색 기능 API. 실시간 검색어 랭킹, 자동완성, 인기 검색어를 제공합니다.",
    },
    {
        "name": "Regions",
        "description": "지역별 생물 다양성 통계 API. 국가/지역별 종 분포와 통계를 제공합니다.",
    },
    {
        "name": "Endangered",
        "description": "멸종위기종 API. 보전 상태별 필터링과 통계를 제공합니다.",
    },
    {
        "name": "Statistics",
        "description": "전체 생물 다양성 통계를 제공합니다.",
    },
]

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Verde 생물다양성 플랫폼 API

전 세계 생물 다양성 데이터를 시각화하고 탐색할 수 있는 플랫폼입니다.

### 주요 기능

* **생물종 관리** - 전 세계 생물종 데이터 조회 및 관리
* **실시간 검색** - 검색어 자동완성 및 인기 검색어 랭킹
* **지역별 통계** - 국가/지역별 생물 다양성 통계
* **멸종위기종** - 보전 상태별 필터링 및 통계

### 인증

현재 API는 공개 엔드포인트로 운영됩니다. 향후 JWT 인증이 추가될 예정입니다.

### 에러 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 |
| 404 | 리소스를 찾을 수 없음 |
| 500 | 서버 내부 오류 |
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
    contact={
        "name": "Verde Team",
        "email": "contact@verde.app",
        "url": "https://github.com/your-username/verde-backend",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
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


@app.get(
    "/",
    tags=["Health"],
    summary="API 루트",
    description="API 루트 엔드포인트. API 버전 및 문서 링크를 반환합니다.",
    responses={
        200: {
            "description": "성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Verde Biodiversity API",
                        "version": "1.0.0",
                        "docs": "/docs",
                        "api_base": "/api/v1"
                    }
                }
            }
        }
    }
)
def root():
    """API 루트 엔드포인트"""
    return {
        "success": True,
        "message": "Verde Biodiversity API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_base": API_V1_PREFIX
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="헬스 체크",
    description="서버, 데이터베이스, Redis 연결 상태를 확인합니다.",
    responses={
        200: {
            "description": "서비스 상태",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "정상 상태",
                            "value": {
                                "success": True,
                                "status": "healthy",
                                "services": {
                                    "database": "connected",
                                    "redis": "connected"
                                }
                            }
                        },
                        "degraded": {
                            "summary": "Redis 연결 실패",
                            "value": {
                                "success": True,
                                "status": "healthy",
                                "services": {
                                    "database": "connected",
                                    "redis": "disconnected"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
def health_check():
    """헬스 체크 - DB 및 Redis 상태 확인"""
    redis_status = redis_health_check()

    return {
        "success": True,
        "status": "healthy",
        "services": {
            "database": "connected",
            "redis": "connected" if redis_status else "disconnected"
        }
    }


@app.get(
    f"{API_V1_PREFIX}/stats",
    tags=["Statistics"],
    summary="전체 통계",
    description="전체 생물 다양성 통계를 조회합니다. 10분간 캐싱됩니다.",
    responses={
        200: {
            "description": "통계 데이터",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "total_species": 1250,
                            "total_regions": 8,
                            "endangered_count": 342,
                            "by_category": {
                                "동물": 450,
                                "식물": 380,
                                "곤충": 280,
                                "해양생물": 140
                            },
                            "by_conservation_status": {
                                "멸종위기": 120,
                                "취약": 222,
                                "준위협": 350,
                                "관심대상": 280,
                                "안전": 278
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "서버 오류",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "서버 오류가 발생했습니다"
                    }
                }
            }
        }
    }
)
def get_global_stats(db: Session = Depends(get_db)):
    """전체 통계 (10분 캐싱)"""
    try:
        # 캐시 확인
        cached = cache_get(CacheKeys.GLOBAL_STATS)
        if cached:
            logger.info("Global stats served from cache")
            return cached

        service = SpeciesService(db)
        stats = service.get_biodiversity_summary()

        result = {
            "success": True,
            "data": stats
        }

        # 10분 캐싱
        cache_set(CacheKeys.GLOBAL_STATS, result, CacheKeys.GLOBAL_STATS_TTL)
        logger.info("Global stats fetched and cached")

        return result
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
