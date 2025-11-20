from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RegionBiodiversityBase(BaseModel):
    region_name: str
    country: str
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
    region_name: Optional[str] = None
    country: Optional[str] = None
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


class RegionStats(BaseModel):
    region_name: str
    country: str
    total_species_count: int
    categories: dict[str, int]
    endangered_percentage: float


class RegionComparison(BaseModel):
    regions: list[RegionStats]
    total_species_all: int
    most_biodiverse: str
    most_endangered: str
