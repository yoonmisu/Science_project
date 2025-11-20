# /api/endpoints/map_search.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db_session

router = APIRouter()


@router.get("/search")
async def search_map_data(
        latitude: float,
        longitude: float,
        radius: int = 1000,
        session: AsyncSession = Depends(get_db_session)
):
    """
    특정 위/경도 주변의 데이터(PostGIS 쿼리)를 검색합니다.
    """
    # 실제 구현 시, cruds/observation_crud.py 등을 사용하여 PostGIS 쿼리를 실행합니다.

    return {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "message": "Map search endpoint is active."
    }