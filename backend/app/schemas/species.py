from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CategoryEnum(str, Enum):
    ANIMAL = "animal"
    PLANT = "plant"
    INSECT = "insect"
    MARINE = "marine"


class ConservationStatusEnum(str, Enum):
    LC = "LC"
    NT = "NT"
    VU = "VU"
    EN = "EN"
    CR = "CR"
    EW = "EW"
    EX = "EX"


class SpeciesBase(BaseModel):
    name_ko: str = Field(..., min_length=1, max_length=255, description="Korean name")
    name_en: Optional[str] = Field(None, max_length=255, description="English name")
    name_scientific: Optional[str] = Field(None, max_length=255, description="Scientific name")
    category: CategoryEnum
    region: str = Field(..., max_length=100)
    description: Optional[str] = None
    habitat: Optional[str] = None
    distribution: Optional[str] = None
    conservation_status: ConservationStatusEnum = ConservationStatusEnum.LC
    is_endangered: bool = False
    population_trend: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class SpeciesCreate(SpeciesBase):
    pass


class SpeciesUpdate(BaseModel):
    name_ko: Optional[str] = Field(None, min_length=1, max_length=255)
    name_en: Optional[str] = Field(None, max_length=255)
    name_scientific: Optional[str] = Field(None, max_length=255)
    category: Optional[CategoryEnum] = None
    region: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    habitat: Optional[str] = None
    distribution: Optional[str] = None
    conservation_status: Optional[ConservationStatusEnum] = None
    is_endangered: Optional[bool] = None
    population_trend: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class SpeciesResponse(SpeciesBase):
    id: int
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
