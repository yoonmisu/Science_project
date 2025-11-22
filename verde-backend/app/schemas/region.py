from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RegionBiodiversityBase(BaseModel):
    region_name: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_species_count: int = 0
    endangered_count: int = 0
    plant_count: int = 0
    animal_count: int = 0
    insect_count: int = 0
    marine_count: int = 0


class RegionBiodiversityCreate(RegionBiodiversityBase):
    pass


class RegionBiodiversityUpdate(BaseModel):
    region_name: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_species_count: Optional[int] = None
    endangered_count: Optional[int] = None
    plant_count: Optional[int] = None
    animal_count: Optional[int] = None
    insect_count: Optional[int] = None
    marine_count: Optional[int] = None


class RegionBiodiversityResponse(RegionBiodiversityBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class RegionListResponse(BaseModel):
    items: List[RegionBiodiversityResponse]
    total: int


class RegionSummary(BaseModel):
    region_name: str
    country: str
    total_species_count: int
    endangered_count: int
    categories: dict
