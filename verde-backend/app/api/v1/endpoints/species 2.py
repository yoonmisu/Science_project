from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from app.services.iucn_service import iucn_service

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def get_species(
    country: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1, le=100)
):
    """
    외부 API(IUCN + Wikipedia)를 통해 생물 다양성 데이터를 조회합니다.
    데이터베이스를 사용하지 않습니다.
    """
    if not country:
        return {"data": [], "total": 0, "page": page, "totalPages": 0}

    # IUCN API + Wikipedia API 호출
    species_list = await iucn_service.get_species_by_country(country)
    
    # 카테고리 필터링
    if category and category != "동물":
        species_list = [s for s in species_list if s.get("category") == category]
    
    total = len(species_list)
    
    # 페이지네이션
    start = (page - 1) * limit
    end = start + limit
    paginated_list = species_list[start:end]
    
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    
    return {
        "data": paginated_list,
        "total": total,
        "page": page,
        "totalPages": total_pages
    }
