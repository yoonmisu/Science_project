from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import species_router, search_router, regions_router, endangered_router, auth_router, upload_router, import_router, biodiversity_router, external_router, map_router, admin_router
from app.routers.frontend import router as frontend_router
from app.services.species_service import SpeciesService
from app.services.scheduler_service import scheduler_service
from app.cache import health_check as redis_health_check, cache_get, cache_set, CacheKeys
from app.logging_config import setup_logging, RequestLoggingMiddleware
from app.api.websocket import manager as ws_manager, periodic_trending_updates
from prometheus_fastapi_instrumentator import Instrumentator

# 구조화된 로깅 설정
setup_logging()
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

    {
        "name": "Upload",
        "description": "이미지 업로드 API. S3/MinIO/로컬 스토리지를 지원합니다.",
    },
    {
        "name": "Import",
        "description": "데이터 임포트 API. CSV/JSON 파일 및 GBIF API를 통한 데이터 임포트를 지원합니다.",
    },
    {
        "name": "Biodiversity",
        "description": "생물 다양성 API. GBIF, iNaturalist, IUCN Red List API를 통합하여 전 세계 생물 데이터를 제공합니다.",
    },
    {
        "name": "External",
        "description": "실시간 외부 데이터 API. GBIF, iNaturalist, IUCN API에서 실시간 데이터를 가져와 캐싱하여 제공합니다.",
    },
    {
        "name": "Map",
        "description": "지도 인터랙션 API. 지오코딩, 공간 검색, 클러스터링, 핫스팟 분석을 제공합니다. PostGIS 기반 공간 쿼리를 지원합니다.",
    },
    {
        "name": "Admin",
        "description": "관리자 API. 통계 대시보드, 데이터 품질 관리, 시스템 모니터링을 제공합니다. 관리자 권한이 필요합니다.",
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

# CORS middleware - 프론트엔드 친화적 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Total-Count",      # 전체 아이템 수
        "X-Page",             # 현재 페이지
        "X-Per-Page",         # 페이지당 아이템 수
        "X-Total-Pages",      # 전체 페이지 수
        "X-Has-Next",         # 다음 페이지 존재 여부
        "X-Has-Prev",         # 이전 페이지 존재 여부
        "X-Cursor",           # 무한 스크롤용 커서
    ]
)

# Include routers with API versioning
API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(species_router, prefix=API_V1_PREFIX)
app.include_router(search_router, prefix=API_V1_PREFIX)
app.include_router(regions_router, prefix=API_V1_PREFIX)
app.include_router(endangered_router, prefix=API_V1_PREFIX)
app.include_router(upload_router, prefix=API_V1_PREFIX)
app.include_router(import_router, prefix=API_V1_PREFIX)
app.include_router(biodiversity_router, prefix=API_V1_PREFIX)
app.include_router(external_router, prefix=API_V1_PREFIX)
app.include_router(map_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)
app.include_router(frontend_router, prefix=API_V1_PREFIX)  # 프론트엔드 친화적 API

# Prometheus 메트릭 설정
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# 애플리케이션 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("Starting Verde API...")
    scheduler_service.start()

    # WebSocket 주기적 업데이트 시작 (백그라운드)
    import asyncio
    asyncio.create_task(periodic_trending_updates())

    logger.info("Verde API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("Shutting down Verde API...")
    scheduler_service.shutdown()
    logger.info("Verde API shutdown complete")


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


# =========================================================================
# WebSocket 엔드포인트
# =========================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 실시간 통신 엔드포인트

    프론트엔드 사용 예시:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
        // 채널 구독
        ws.send(JSON.stringify({
            action: 'subscribe',
            channels: ['trending', 'species_updates']
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data);

        if (data.type === 'trending_update') {
            // 실시간 검색어 순위 업데이트
            updateTrendingList(data.data);
        }
    };
    ```

    지원 채널:
    - trending: 실시간 검색어 순위 (30초마다)
    - species_updates: 새로운 생물종 추가 알림
    - stats: 통계 업데이트
    - notifications: 일반 알림
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    # 채널 구독
                    channels = message.get("channels", [])
                    for channel in channels:
                        await ws_manager.subscribe(websocket, channel)

                elif action == "unsubscribe":
                    # 채널 구독 해제
                    channels = message.get("channels", [])
                    for channel in channels:
                        await ws_manager.unsubscribe(websocket, channel)

                elif action == "ping":
                    # Ping-Pong (연결 유지)
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        ws_manager.disconnect(websocket)


@app.get("/ws/stats")
async def websocket_stats():
    """WebSocket 연결 통계"""
    return {
        "success": True,
        "data": ws_manager.get_stats()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
