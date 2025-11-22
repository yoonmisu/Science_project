from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from app.database import get_db
from app.cache import (
    cache_get, cache_set, CacheKeys,
    increment_search_count, get_top_searches
)
from app.models.species import Species
from app.models.search_query import SearchQuery
from app.schemas.species import SpeciesResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    region: Optional[str] = None


@router.get("/trending")
def get_trending_searches(
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None)
):
    """실시간 인기 검색어 Top N - Redis Sorted Set 사용 (5분 캐싱)"""
    try:
        cache_key = f"{CacheKeys.TRENDING_SEARCHES}:{category or 'all'}:{limit}"

        # 캐시 확인
        cached = cache_get(cache_key)
        if cached:
            logger.info("Trending searches served from cache")
            return cached

        # Redis Sorted Set에서 조회
        trending = get_top_searches(limit=limit, category=category)

        result = {
            "success": True,
            "data": trending
        }

        # 5분 캐싱
        cache_set(cache_key, result, CacheKeys.TRENDING_SEARCHES_TTL)
        logger.info(f"Trending searches cached: {len(trending)} items")

        return result
    except Exception as e:
        logger.error(f"Error fetching trending searches: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.post("/")
def search_species(
    search_request: SearchRequest,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """검색 수행 및 검색어 기록 - Redis Sorted Set으로 랭킹 업데이트"""
    try:
        q = search_request.query.strip()
        category = search_request.category
        region = search_request.region

        # 검색 쿼리
        query = db.query(Species).filter(
            or_(
                Species.name.ilike(f"%{q}%"),
                Species.scientific_name.ilike(f"%{q}%"),
                Species.description.ilike(f"%{q}%")
            )
        )

        if category:
            query = query.filter(Species.category == category)
        if region:
            query = query.filter(Species.region == region)

        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()
        pages = (total + limit - 1) // limit

        # Redis Sorted Set에 검색어 카운트 증가
        increment_search_count(q, category)

        # DB에도 검색어 기록 업데이트
        existing_query = db.query(SearchQuery).filter(
            SearchQuery.query_text == q,
            SearchQuery.category == category,
            SearchQuery.region == region
        ).first()

        if existing_query:
            existing_query.search_count += 1
            existing_query.last_searched_at = datetime.utcnow()
        else:
            new_query = SearchQuery(
                query_text=q,
                category=category,
                region=region,
                search_count=1
            )
            db.add(new_query)

        db.commit()

        logger.info(f"Search performed: '{q}' - {total} results")

        return {
            "success": True,
            "data": {
                "items": [SpeciesResponse.model_validate(item).model_dump() for item in items],
                "total": total,
                "page": page,
                "pages": pages,
                "query": q,
                "category": category,
                "region": region
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error performing search: {str(e)}")
        raise HTTPException(status_code=500, detail="검색 중 오류가 발생했습니다")


@router.get("/suggestions")
def get_search_suggestions(
    q: str = Query(..., min_length=1, description="검색어"),
    db: Session = Depends(get_db)
):
    """검색어 자동완성 - 최대 10개"""
    try:
        # 종 이름에서 검색
        species_names = db.query(Species.name).filter(
            Species.name.ilike(f"%{q}%")
        ).distinct().limit(10).all()

        suggestions = [s.name for s in species_names]

        # 이전 검색어에서도 추가
        if len(suggestions) < 10:
            remaining = 10 - len(suggestions)
            past_queries = db.query(SearchQuery.query_text).filter(
                SearchQuery.query_text.ilike(f"%{q}%"),
                ~SearchQuery.query_text.in_(suggestions)
            ).order_by(
                desc(SearchQuery.search_count)
            ).limit(remaining).all()

            suggestions.extend([pq.query_text for pq in past_queries])

        logger.info(f"Suggestions for '{q}': {len(suggestions)} items")

        return {
            "success": True,
            "data": {
                "suggestions": suggestions[:10]
            }
        }
    except Exception as e:
        logger.error(f"Error fetching suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/popular")
def get_popular_searches(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """전체 인기 검색어 - DB 기반"""
    try:
        popular = db.query(
            SearchQuery.query_text,
            SearchQuery.search_count
        ).order_by(
            desc(SearchQuery.search_count)
        ).limit(limit).all()

        return {
            "success": True,
            "data": [
                {"query": p.query_text, "count": p.search_count}
                for p in popular
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching popular searches: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/realtime")
def get_realtime_ranking(
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None)
):
    """실시간 검색어 순위 - Redis Sorted Set 직접 조회"""
    try:
        ranking = get_top_searches(limit=limit, category=category)

        return {
            "success": True,
            "data": ranking
        }
    except Exception as e:
        logger.error(f"Error fetching realtime ranking: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")
