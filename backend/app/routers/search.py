from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional

from app.database import get_db
from app.models.species import Species
from app.models.search_query import SearchQuery
from app.schemas.search import SearchResponse, SearchResult, SearchQueryResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
def search_species(
    request: Request,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1, max_length=500),
    category: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """Search species by name (Korean, English, or Scientific)"""
    search_term = f"%{q}%"

    query = db.query(Species).filter(
        or_(
            Species.name_ko.ilike(search_term),
            Species.name_en.ilike(search_term),
            Species.name_scientific.ilike(search_term)
        )
    )

    if category:
        query = query.filter(Species.category == category)
    if region:
        query = query.filter(Species.region == region)

    results = query.limit(limit).all()

    # Log search query
    search_log = SearchQuery(
        query=q,
        category=category,
        region=region,
        results_count=len(results),
        user_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(search_log)
    db.commit()

    # Convert to SearchResult
    search_results = [
        SearchResult(
            id=species.id,
            name_ko=species.name_ko,
            name_en=species.name_en,
            name_scientific=species.name_scientific,
            category=species.category.value if hasattr(species.category, 'value') else species.category,
            region=species.region,
            is_endangered=species.is_endangered,
            thumbnail_url=species.thumbnail_url
        )
        for species in results
    ]

    # Generate suggestions based on popular searches
    suggestions = _get_search_suggestions(db, q)

    return SearchResponse(
        query=q,
        results=search_results,
        total=len(results),
        suggestions=suggestions
    )


@router.get("/suggestions")
def get_suggestions(
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20)
):
    """Get autocomplete suggestions based on species names"""
    search_term = f"{q}%"

    # Get matching species names
    ko_matches = db.query(Species.name_ko).filter(
        Species.name_ko.ilike(search_term)
    ).limit(limit).all()

    en_matches = db.query(Species.name_en).filter(
        Species.name_en.ilike(search_term)
    ).limit(limit).all()

    suggestions = list(set(
        [name[0] for name in ko_matches if name[0]] +
        [name[0] for name in en_matches if name[0]]
    ))[:limit]

    return {"suggestions": suggestions}


@router.get("/popular", response_model=list[SearchQueryResponse])
def get_popular_searches(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get most popular search queries"""
    popular = db.query(
        SearchQuery.query,
        func.count(SearchQuery.id).label("count")
    ).group_by(SearchQuery.query).order_by(
        func.count(SearchQuery.id).desc()
    ).limit(limit).all()

    return [{"query": q, "count": c} for q, c in popular]


@router.get("/history", response_model=list[SearchQueryResponse])
def get_search_history(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """Get recent search history"""
    history = db.query(SearchQuery).order_by(
        SearchQuery.created_at.desc()
    ).limit(limit).all()

    return history


def _get_search_suggestions(db: Session, query: str) -> list[str]:
    """Generate search suggestions based on similar popular queries"""
    search_term = f"%{query}%"

    similar = db.query(SearchQuery.query).filter(
        SearchQuery.query.ilike(search_term),
        SearchQuery.results_count > 0
    ).group_by(SearchQuery.query).order_by(
        func.count(SearchQuery.id).desc()
    ).limit(5).all()

    return [s[0] for s in similar if s[0] != query]
