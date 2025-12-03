from fastapi import APIRouter
from app.api.v1.endpoints import species

api_router = APIRouter()
api_router.include_router(species.router, prefix="/species", tags=["species"])
