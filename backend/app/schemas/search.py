from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SearchQueryCreate(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = None
    region: Optional[str] = None


class SearchQueryResponse(BaseModel):
    id: int
    query: str
    category: Optional[str]
    region: Optional[str]
    results_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    id: int
    name_ko: str
    name_en: Optional[str]
    name_scientific: Optional[str]
    category: str
    region: str
    is_endangered: bool
    thumbnail_url: Optional[str]
    relevance_score: Optional[float] = None

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
    suggestions: list[str] = []
