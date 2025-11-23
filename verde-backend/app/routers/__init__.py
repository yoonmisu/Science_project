from app.routers.species import router as species_router
from app.routers.search import router as search_router
from app.routers.regions import router as regions_router
from app.routers.endangered import router as endangered_router

__all__ = ["species_router", "search_router", "regions_router", "endangered_router"]
