from app.routers.species import router as species_router
from app.routers.search import router as search_router
from app.routers.regions import router as regions_router
from app.routers.endangered import router as endangered_router
from app.routers.auth import router as auth_router
from app.routers.upload import router as upload_router
from app.routers.import_data import router as import_router
from app.routers.biodiversity import router as biodiversity_router
from app.routers.external import router as external_router
from app.routers.map import router as map_router

__all__ = [
    "species_router",
    "search_router",
    "regions_router",
    "endangered_router",
    "auth_router",
    "upload_router",
    "import_router",
    "biodiversity_router",
    "external_router",
    "map_router"
]
