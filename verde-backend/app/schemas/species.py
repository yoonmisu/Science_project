from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CategoryEnum(str, Enum):
    PLANT = "식물"
    ANIMAL = "동물"
    INSECT = "곤충"
    MARINE = "해양생물"


class ConservationStatusEnum(str, Enum):
    ENDANGERED = "멸종위기"
    VULNERABLE = "취약"
    NEAR_THREATENED = "준위협"
    LEAST_CONCERN = "관심대상"
    SAFE = "안전"


class SpeciesBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="한글명")
    scientific_name: Optional[str] = Field(None, max_length=200, description="학명")
    category: CategoryEnum = Field(..., description="카테고리")
    region: str = Field(..., max_length=100, description="지역")
    country: str = Field(..., max_length=100, description="국가")
    description: Optional[str] = Field(None, description="설명")
    characteristics: Optional[List[str]] = Field(None, description="특징 리스트")
    image_url: Optional[str] = Field(None, max_length=500)
    conservation_status: Optional[ConservationStatusEnum] = Field(None, description="보전 상태")


class SpeciesCreate(SpeciesBase):
    pass


class SpeciesUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    scientific_name: Optional[str] = Field(None, max_length=200)
    category: Optional[CategoryEnum] = None
    region: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    characteristics: Optional[List[str]] = None
    image_url: Optional[str] = Field(None, max_length=500)
    conservation_status: Optional[ConservationStatusEnum] = None


class SpeciesResponse(SpeciesBase):
    id: int
    search_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SpeciesListResponse(BaseModel):
    items: List[SpeciesResponse]
    total: int
    page: int
    size: int
    pages: int
