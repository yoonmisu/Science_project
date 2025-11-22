from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class SearchQueryBase(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=100)


class SearchQueryCreate(SearchQueryBase):
    pass


class SearchQueryResponse(SearchQueryBase):
    id: int
    search_count: int
    last_searched_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, description="식물, 동물, 곤충, 해양생물")
    region: Optional[str] = Field(None, description="지역")
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class SearchResponse(BaseModel):
    items: List[Any]
    total: int
    query: str
    category: Optional[str]
    region: Optional[str]


class PopularSearchResponse(BaseModel):
    query_text: str
    search_count: int


class SearchSuggestionResponse(BaseModel):
    suggestions: List[str]
