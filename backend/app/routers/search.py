from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.models.species import Species
from app.models.search_query import SearchQuery
from app.schemas.search import SearchResponse, SearchResult, PopularSearch
from app.config import get_settings
from app.cache import (
    cache_get, cache_set, cache_delete,
    increment_search_count, get_top_searches,
    get_trending_searches_cache, set_trending_searches_cache
)

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


def get_api_response(success: bool, data=None, message: str = None):
    """Standard API response format"""
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    region: Optional[str] = None


@router.get("/trending")
def get_trending_searches(
    db: Session = Depends(get_db),
    daily: bool = Query(True, description="Get daily trending (True) or all-time (False)")
):
    """Get top 5 trending search queries using Redis Sorted Set"""
    try:
        # Check cache first (5 minutes TTL)
        cached = get_trending_searches_cache()
        if cached:
            logger.info("Trending searches served from cache")
            return get_api_response(True, cached)

        # Get from Redis Sorted Set
        result = get_top_searches(limit=5, daily=daily)

        # If Redis is empty, fall back to database
        if not result:
            since = datetime.utcnow() - timedelta(hours=24)
            trending = db.query(
                SearchQuery.query_text,
                func.sum(SearchQuery.search_count).label("total_count")
            ).filter(
                SearchQuery.last_searched_at >= since
            ).group_by(
                SearchQuery.query_text
            ).order_by(
                desc("total_count")
            ).limit(5).all()

            result = [
                {"query": q, "count": int(c)}
                for q, c in trending
            ]

        # Cache for 5 minutes
        set_trending_searches_cache(result)

        logger.info(f"Trending searches retrieved: {len(result)} items")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching trending searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending searches")


@router.post("")
def search_species(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Perform search and log search query"""
    try:
        query_text = search_request.query.strip()
        if not query_text:
            raise HTTPException(status_code=400, detail="Search query cannot be empty")

        search_term = f"%{query_text}%"

        # Build search query
        query = db.query(Species).filter(
            or_(
                Species.name.ilike(search_term),
                Species.scientific_name.ilike(search_term),
                Species.description.ilike(search_term)
            )
        )

        # Apply filters
        if search_request.category:
            query = query.filter(Species.category == search_request.category)
        if search_request.region:
            query = query.filter(Species.region == search_request.region)

        # Get results
        results = query.order_by(desc(Species.search_count)).limit(50).all()

        # Log search query
        existing_query = db.query(SearchQuery).filter(
            SearchQuery.query_text == query_text,
            SearchQuery.category == search_request.category,
            SearchQuery.region == search_request.region
        ).first()

        if existing_query:
            existing_query.search_count += 1
            existing_query.last_searched_at = datetime.utcnow()
        else:
            new_query = SearchQuery(
                query_text=query_text,
                category=search_request.category,
                region=search_request.region,
                search_count=1
            )
            db.add(new_query)

        db.commit()

        # Increment search count in Redis Sorted Set
        increment_search_count(query_text)

        # Format results
        search_results = [
            SearchResult(
                id=s.id,
                name=s.name,
                scientific_name=s.scientific_name,
                category=s.category.value if hasattr(s.category, 'value') else s.category,
                region=s.region,
                country=s.country,
                conservation_status=s.conservation_status.value if hasattr(s.conservation_status, 'value') else s.conservation_status,
                image_url=s.image_url,
                search_count=s.search_count or 0
            )
            for s in results
        ]

        # Invalidate trending cache
        cache_delete("search:trending")

        logger.info(f"Search performed: '{query_text}' - {len(results)} results")

        return get_api_response(True, {
            "query": query_text,
            "results": [r.model_dump() for r in search_results],
            "total": len(results)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/suggestions")
def get_suggestions(
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1, max_length=100)
):
    """Get autocomplete suggestions for search"""
    try:
        search_term = f"{q}%"

        # Get suggestions from species names
        name_suggestions = db.query(Species.name).filter(
            Species.name.ilike(search_term)
        ).distinct().limit(5).all()

        scientific_suggestions = db.query(Species.scientific_name).filter(
            Species.scientific_name.ilike(search_term),
            Species.scientific_name.isnot(None)
        ).distinct().limit(5).all()

        # Combine and deduplicate
        suggestions = list(set(
            [n[0] for n in name_suggestions if n[0]] +
            [s[0] for s in scientific_suggestions if s[0]]
        ))[:10]

        # Sort by relevance (exact prefix matches first)
        suggestions.sort(key=lambda x: (not x.lower().startswith(q.lower()), len(x)))

        logger.info(f"Suggestions for '{q}': {len(suggestions)} results")
        return get_api_response(True, suggestions)

    except Exception as e:
        logger.error(f"Error fetching suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch suggestions")


@router.get("/popular")
def get_popular_searches(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get most popular search queries of all time"""
    try:
        popular = db.query(
            SearchQuery.query_text,
            func.sum(SearchQuery.search_count).label("total")
        ).group_by(
            SearchQuery.query_text
        ).order_by(
            desc("total")
        ).limit(limit).all()

        result = [
            {"query": q, "count": int(c)}
            for q, c in popular
        ]

        logger.info(f"Popular searches retrieved: {len(result)} items")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching popular searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch popular searches")


@router.get("/history")
def get_search_history(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """Get recent search history"""
    try:
        history = db.query(SearchQuery).order_by(
            desc(SearchQuery.last_searched_at)
        ).limit(limit).all()

        logger.info(f"Search history retrieved: {len(history)} items")
        return get_api_response(True, history)

    except Exception as e:
        logger.error(f"Error fetching search history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch search history")


@router.get("/ranking")
def get_search_ranking(
    limit: int = Query(10, ge=1, le=100),
    daily: bool = Query(False, description="Get daily ranking (True) or all-time (False)")
):
    """Get real-time search ranking from Redis Sorted Set"""
    try:
        result = get_top_searches(limit=limit, daily=daily)

        logger.info(f"Search ranking retrieved: {len(result)} items (daily={daily})")
        return get_api_response(True, {
            "ranking": result,
            "type": "daily" if daily else "all_time",
            "total": len(result)
        })

    except Exception as e:
        logger.error(f"Error fetching search ranking: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ranking")
