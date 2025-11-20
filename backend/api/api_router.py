# /api/api_router.py

from fastapi import APIRouter
from .endpoints import species, map_search # 🚨 모든 엔드포인트 임포트

api_router = APIRouter()

api_router.include_router(species.router, prefix="/species", tags=["species"])
api_router.include_router(map_search.router, prefix="/map", tags=["map_search"])