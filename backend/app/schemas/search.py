from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SearchQueryCreate(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None
    region: Optional[str] = None


class SearchQueryResponse(BaseModel):
    id: int
    query_text: str
    search_count: int
    last_searched_at: datetime
    category: Optional[str]
    region: Optional[str]

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    id: int
    name: str
    scientific_name: Optional[str]
    category: str
    region: str
    country: str
    conservation_status: str
    image_url: Optional[str]
    search_count: int

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
    suggestions: list[str] = []


class PopularSearch(BaseModel):
    query_text: str
    search_count: int
