from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RegionBiodiversityBase(BaseModel):
    region: str
    region_ko: Optional[str] = None
    total_species: int = 0
    animal_count: int = 0
    plant_count: int = 0
    insect_count: int = 0
    marine_count: int = 0
    endangered_count: int = 0
    critically_endangered_count: int = 0
    biodiversity_index: Optional[float] = None
    endemic_species_count: int = 0
    area_km2: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RegionBiodiversityCreate(RegionBiodiversityBase):
    pass


class RegionBiodiversityResponse(RegionBiodiversityBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class RegionStats(BaseModel):
    region: str
    region_ko: Optional[str]
    total_species: int
    categories: dict[str, int]
    endangered_percentage: float
    biodiversity_index: Optional[float]


class RegionComparison(BaseModel):
    regions: list[RegionStats]
    total_species_all: int
    most_biodiverse: str
    most_endangered: str
