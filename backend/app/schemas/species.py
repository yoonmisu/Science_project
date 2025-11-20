from pydantic import BaseModel, Field
from typing import Optional
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
    category: CategoryEnum
    region: str = Field(..., max_length=100, description="지역")
    country: str = Field(..., max_length=100, description="국가")
    description: Optional[str] = None
    characteristics: Optional[list[str]] = None
    conservation_status: ConservationStatusEnum = ConservationStatusEnum.SAFE
    image_url: Optional[str] = Field(None, max_length=500)


class SpeciesCreate(SpeciesBase):
    pass


class SpeciesUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    scientific_name: Optional[str] = Field(None, max_length=200)
    category: Optional[CategoryEnum] = None
    region: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    characteristics: Optional[list[str]] = None
    conservation_status: Optional[ConservationStatusEnum] = None
    image_url: Optional[str] = Field(None, max_length=500)


class SpeciesResponse(SpeciesBase):
    id: int
    search_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SpeciesList(BaseModel):
    items: list[SpeciesResponse]
    total: int
    page: int
    size: int
    pages: int
