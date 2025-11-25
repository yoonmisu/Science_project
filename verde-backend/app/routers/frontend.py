"""
프론트엔드 친화적인 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from typing import Optional
from datetime import datetime, date
import logging

from app.database import get_db
from app.models.species import Species
from app.models.region_biodiversity import RegionBiodiversity
from app.models.search_query import SearchQuery
from app.schemas.species import SpeciesResponse
from app.api.response import APIResponse, ErrorCodes
from app.utils.heatmap import calculate_country_heatmap_data, get_heatmap_legend
from app.cache import cache_get, cache_set, CacheKeys, get_top_searches

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/frontend", tags=["Frontend"])


# =========================================================================
# 1. 초기 로드용 통합 데이터
# =========================================================================
@router.get(
    "/init/app-data",
    summary="앱 초기 데이터",
    description="""
    프론트엔드 초기 로드 시 필요한 모든 데이터를 한 번에 제공합니다.

    포함 데이터:
    - 오늘의 추천 생물종
    - 실시간 인기 검색어 Top 5
    - 전체 통계 (종 수, 멸종위기종 수, 지원 국가 수)
    - 히트맵 범례

    이점:
    - 페이지 로드 시 한 번만 호출
    - 여러 API 호출을 하나로 통합
    - 로딩 시간 단축 (1 request vs 4+ requests)
    """
)
async def get_app_init_data(db: Session = Depends(get_db)):
    """앱 초기 데이터 - 여러 API를 하나로 통합"""
    try:
        # 캐시 확인 (5분)
        cache_key = "frontend:init:app-data"
        cached = cache_get(cache_key)
        if cached:
            logger.info("App init data served from cache")
            return cached

        # 1. 오늘의 추천 생물종 (날짜 기반 시드)
        today_seed = int(date.today().strftime("%Y%m%d"))
        total = db.query(Species).count()
        if total > 0:
            index = today_seed % total
            featured_species = db.query(Species).offset(index).first()
            featured = SpeciesResponse.model_validate(featured_species).model_dump() if featured_species else None
        else:
            featured = None

        # 2. 실시간 인기 검색어
        trending = get_top_searches(limit=5) or []

        # 3. 전체 통계
        total_species = db.query(Species).count()
        endangered_count = db.query(Species).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).count()
        countries_covered = db.query(
            func.count(func.distinct(Species.country))
        ).scalar() or 0

        # 4. 카테고리별 통계
        by_category = db.query(
            Species.category,
            func.count(Species.id).label("count")
        ).group_by(Species.category).all()

        # 5. 히트맵 범례
        legend = get_heatmap_legend()

        result = APIResponse.success(
            data={
                "featured_today": featured,
                "trending_searches": trending,
                "statistics": {
                    "total_species": total_species,
                    "total_endangered": endangered_count,
                    "countries_covered": countries_covered,
                    "by_category": {cat.category: cat.count for cat in by_category if cat.category}
                },
                "heatmap_legend": legend,
                "loaded_at": datetime.utcnow().isoformat() + "Z"
            },
            source="database",
            metadata={"purpose": "initial_load"}
        )

        # 5분 캐싱
        cache_set(cache_key, result, 300)
        logger.info("App init data cached")

        return result

    except Exception as e:
        logger.error(f"Error fetching app init data: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="초기 데이터를 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"error": str(e)}
        )


# =========================================================================
# 2. 검색 자동완성 최적화
# =========================================================================
@router.get(
    "/search/autocomplete",
    summary="검색 자동완성",
    description="""
    검색어 자동완성 추천을 제공합니다.

    특징:
    - 빠른 응답 속도 (Redis 캐싱 10분)
    - 하이라이팅 정보 포함
    - 썸네일 이미지 포함
    - 카테고리 아이콘 정보

    사용 예시:
    - 사용자가 "산" 입력 → ["산호랑나비", "산개구리", "산양"]
    - 사용자가 "pan" 입력 → ["Panthera tigris (호랑이)", "Panda (판다)"]
    """
)
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=50, description="검색어"),
    limit: int = Query(10, ge=1, le=20, description="결과 수"),
    db: Session = Depends(get_db)
):
    """검색 자동완성 - Redis 캐싱"""
    try:
        # 캐시 확인
        cache_key = f"search:autocomplete:{q}:{limit}"
        cached = cache_get(cache_key)
        if cached:
            logger.info(f"Autocomplete served from cache: {q}")
            return cached

        # DB 검색 (이름 또는 학명)
        species = db.query(Species).filter(
            or_(
                Species.name.ilike(f"{q}%"),
                Species.scientific_name.ilike(f"{q}%"),
                Species.name.ilike(f"%{q}%"),
                Species.scientific_name.ilike(f"%{q}%")
            )
        ).order_by(
            desc(Species.search_count)  # 인기순
        ).limit(limit).all()

        # 결과 포맷팅
        suggestions = []
        for s in species:
            # 매칭 텍스트 하이라이팅
            name_match = q.lower() in s.name.lower() if s.name else False
            sci_match = q.lower() in s.scientific_name.lower() if s.scientific_name else False

            suggestion = {
                "id": s.id,
                "name": s.name,
                "scientific_name": s.scientific_name,
                "category": s.category,
                "conservation_status": s.conservation_status,
                "thumbnail": s.image_url,
                "match_type": "name" if name_match else "scientific_name",
                "search_count": s.search_count
            }
            suggestions.append(suggestion)

        result = APIResponse.success(
            data={
                "query": q,
                "suggestions": suggestions,
                "count": len(suggestions)
            },
            source="database"
        )

        # 10분 캐싱
        cache_set(cache_key, result, 600)
        logger.info(f"Autocomplete results cached: {q} - {len(suggestions)} items")

        return result

    except Exception as e:
        logger.error(f"Error in autocomplete: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="자동완성 조회 중 오류가 발생했습니다",
            status_code=500,
            details={"query": q, "error": str(e)}
        )


# =========================================================================
# 3. 지도용 경량화 데이터
# =========================================================================
@router.get(
    "/map/countries/simple",
    summary="지도용 경량 데이터",
    description="""
    지도 렌더링에 필요한 최소한의 데이터만 제공합니다.

    포함 데이터:
    - 국가 코드, 이름
    - 멸종위기종 수
    - 히트맵 색상 코드
    - 강도 (0.0 ~ 1.0)

    제외 데이터:
    - GeoJSON 좌표 (프론트엔드에서 별도 로드)
    - 상세 통계 (별도 API 사용)

    캐싱: 1시간
    """
)
async def get_countries_simple(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    db: Session = Depends(get_db)
):
    """지도용 경량 데이터 - GeoJSON 제외"""
    try:
        # 캐시 확인
        cache_key = f"map:countries:simple:{category or 'all'}"
        cached = cache_get(cache_key)
        if cached:
            logger.info("Map countries served from cache")
            return cached

        # 지역 통계 조회
        regions = db.query(RegionBiodiversity).all()

        if not regions:
            return APIResponse.success(
                data={
                    "countries": [],
                    "legend": get_heatmap_legend(),
                    "last_updated": None
                },
                source="database"
            )

        # 히트맵 데이터 생성
        region_stats = [
            {
                "country": r.country,
                "endangered_count": r.endangered_count,
                "total_species_count": r.total_species_count,
                "country_code": r.country[:2].upper()  # 간단한 코드 추출
            }
            for r in regions
        ]

        heatmap_data = calculate_country_heatmap_data(region_stats)

        # 경량화된 데이터
        countries = []
        for hm in heatmap_data:
            countries.append({
                "code": hm.get("country_code", hm["country"][:2].upper()),
                "name": hm["country"],
                "count": hm["endangered_count"],
                "intensity": hm["intensity"],
                "color": hm["color_code"],
                "label": hm["label"]
            })

        result = APIResponse.success(
            data={
                "countries": countries,
                "legend": get_heatmap_legend(),
                "last_updated": max(r.updated_at for r in regions if r.updated_at) if regions else None
            },
            source="database",
            cache_info={"ttl": 3600}
        )

        # 1시간 캐싱
        cache_set(cache_key, result, 3600)
        logger.info("Map countries cached")

        return result

    except Exception as e:
        logger.error(f"Error fetching map countries: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="지도 데이터를 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"error": str(e)}
        )


# =========================================================================
# 4. 무한 스크롤용 커서 기반 페이지네이션
# =========================================================================
@router.get(
    "/species/infinite",
    summary="무한 스크롤용 목록",
    description="""
    무한 스크롤에 최적화된 커서 기반 페이지네이션입니다.

    사용법:
    1. 첫 로드: GET /frontend/species/infinite?limit=20
    2. 다음 로드: GET /frontend/species/infinite?cursor=20&limit=20
    3. 또 다음: GET /frontend/species/infinite?cursor=40&limit=20

    장점:
    - 오프셋 기반보다 빠름
    - 데이터 중복/누락 없음
    - 대용량 데이터에 적합
    """
)
async def get_species_infinite(
    response: Response,
    cursor: Optional[int] = Query(None, description="마지막 species ID"),
    limit: int = Query(20, ge=1, le=100, description="가져올 개수"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    status: Optional[str] = Query(None, description="보전 상태 필터"),
    db: Session = Depends(get_db)
):
    """무한 스크롤용 커서 기반 페이지네이션"""
    try:
        query = db.query(Species)

        # 커서 기반 필터링
        if cursor:
            query = query.filter(Species.id > cursor)

        # 추가 필터
        if category:
            query = query.filter(Species.category == category)
        if status:
            query = query.filter(Species.conservation_status == status)

        # limit + 1개 조회 (has_next 판단용)
        species = query.order_by(Species.id).limit(limit + 1).all()

        has_next = len(species) > limit
        if has_next:
            species = species[:-1]  # 마지막 하나 제거

        next_cursor = species[-1].id if species and has_next else None

        # Response 헤더 추가
        if has_next and next_cursor:
            response.headers["X-Cursor"] = str(next_cursor)
            response.headers["X-Has-Next"] = "true"
        else:
            response.headers["X-Has-Next"] = "false"

        logger.info(f"Infinite scroll: cursor={cursor}, returned {len(species)} items")

        return APIResponse.success(
            data={
                "items": [SpeciesResponse.model_validate(s).model_dump() for s in species],
                "next_cursor": next_cursor,
                "has_next": has_next,
                "count": len(species)
            },
            source="database",
            metadata={
                "cursor_type": "id",
                "filters": {
                    "category": category,
                    "status": status
                }
            }
        )

    except Exception as e:
        logger.error(f"Error in infinite scroll: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="데이터를 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"cursor": cursor, "error": str(e)}
        )


# =========================================================================
# 5. 빠른 통계 조회
# =========================================================================
@router.get(
    "/stats/quick",
    summary="빠른 통계",
    description="""
    대시보드용 핵심 통계만 빠르게 제공합니다.

    포함:
    - 전체 종 수
    - 멸종위기종 수
    - 오늘 추가된 종 수
    - 카테고리별 집계 (4개)

    캐싱: 5분
    """
)
async def get_quick_stats(db: Session = Depends(get_db)):
    """대시보드용 빠른 통계"""
    try:
        cache_key = "frontend:stats:quick"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # 핵심 통계만 조회
        total = db.query(func.count(Species.id)).scalar()
        endangered = db.query(func.count(Species.id)).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).scalar()

        # 오늘 추가된 종
        today = datetime.utcnow().date()
        added_today = db.query(func.count(Species.id)).filter(
            func.date(Species.created_at) == today
        ).scalar()

        # 카테고리별
        by_category = db.query(
            Species.category,
            func.count(Species.id)
        ).group_by(Species.category).all()

        result = APIResponse.success(
            data={
                "total_species": total or 0,
                "endangered_species": endangered or 0,
                "added_today": added_today or 0,
                "by_category": {cat: count for cat, count in by_category if cat}
            },
            source="database"
        )

        cache_set(cache_key, result, 300)  # 5분
        return result

    except Exception as e:
        logger.error(f"Error fetching quick stats: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="통계를 가져오는 중 오류가 발생했습니다",
            status_code=500
        )
