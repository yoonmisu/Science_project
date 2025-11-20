# schemas/map_search_schema.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# 1. 관측 기록 생성 요청 (클라이언트 -> 서버)
class ObservationCreate(BaseModel):
    species_id: int = Field(..., description="관측된 종의 ID")
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")


# 2. 관측 기록 응답 스키마 (서버 -> 클라이언트)
class ObservationResponse(BaseModel):
    id: int
    species_id: int
    latitude: float
    longitude: float
    observed_at: datetime

    class Config:
        from_attributes = True


# 3. 지도 기반 검색 요청 (클라이언트 -> 서버)
class MapSearchRequest(BaseModel):
    min_lat: float = Field(..., description="검색 영역 최소 위도 (Bounding Box)")
    max_lat: float = Field(..., description="검색 영역 최대 위도 (Bounding Box)")
    min_lon: float = Field(..., description="검색 영역 최소 경도 (Bounding Box)")
    max_lon: float = Field(..., description="검색 영역 최대 경도 (Bounding Box)")


# 4. 지도 검색 결과 응답 (서버 -> 클라이언트)
class MapSearchResult(BaseModel):
    species_id: int
    count: int = Field(..., description="해당 영역에서 관측된 횟수")
    scientific_name: str
    common_name: Optional[str]