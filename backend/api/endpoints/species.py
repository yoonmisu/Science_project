# /api/endpoints/species.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db_session
from cruds import species_crud as crud
from schemas.species_schema import SpeciesCreate, SpeciesResponse, SpeciesNearbySearch

router = APIRouter()


@router.post("/", response_model=SpeciesResponse, status_code=status.HTTP_201_CREATED)
async def create_species(
    species_data: SpeciesCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """새로운 종을 생성합니다."""
    result = await crud.create_species(session, species_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="종 생성에 실패했습니다."
        )
    return result


@router.get("/nearby", response_model=list[SpeciesResponse])
async def search_species_nearby(
    latitude: float = Query(..., ge=-90, le=90, description="검색 기준점의 위도"),
    longitude: float = Query(..., ge=-180, le=180, description="검색 기준점의 경도"),
    radius_meters: int = Query(default=1000, ge=100, description="검색 반경 (미터 단위)"),
    session: AsyncSession = Depends(get_db_session)
):
    """지정된 위치 반경 내의 종을 검색합니다."""
    search_params = SpeciesNearbySearch(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters
    )
    result = await crud.get_species_nearby(session, search_params)
    return result


@router.get("/", response_model=list[SpeciesResponse])
async def read_species_list(
    session: AsyncSession = Depends(get_db_session)
):
    """모든 종 목록을 조회합니다."""
    db_species = await crud.get_all_species(session)
    return db_species
