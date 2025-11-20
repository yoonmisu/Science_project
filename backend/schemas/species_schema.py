# /schemas/species_schema.py

from datetime import datetime
from pydantic import BaseModel, Field


class SpeciesCreate(BaseModel):
    """클라이언트로부터 종 데이터를 받기 위한 스키마"""
    name_korean: str = Field(..., description="한국어 종 이름")
    name_scientific: str = Field(..., description="학명")
    latitude: float = Field(..., ge=-90, le=90, description="발견 위치의 위도")
    longitude: float = Field(..., ge=-180, le=180, description="발견 위치의 경도")
    description: str | None = Field(None, description="종에 대한 설명")


class SpeciesResponse(BaseModel):
    """DB에서 조회한 종 데이터를 응답하기 위한 스키마"""
    id: int
    name_korean: str
    name_scientific: str
    location: str = Field(..., description="WKT(Well-Known Text) 형식의 위치 정보")
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SpeciesNearbySearch(BaseModel):
    """근접 거리 검색을 위한 쿼리 스키마"""
    latitude: float = Field(..., ge=-90, le=90, description="검색 기준점의 위도")
    longitude: float = Field(..., ge=-180, le=180, description="검색 기준점의 경도")
    radius_meters: int = Field(default=1000, ge=100, description="검색 반경 (미터 단위)")
