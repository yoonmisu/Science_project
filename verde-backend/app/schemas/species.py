from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SpeciesBase(BaseModel):
    name: str
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    category: str
    country: str
    image: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    population: Optional[str] = None
    threats: Optional[List[str]] = None

class SpeciesResponse(SpeciesBase):
    id: int
    mentions: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class SpeciesListResponse(BaseModel):
    data: List[SpeciesResponse]
    total: int
    page: int
    totalPages: int

class SpeciesSearchResponse(BaseModel):
    data: List[SpeciesResponse]
    total: int
    page: int
    totalPages: int
    query: str
