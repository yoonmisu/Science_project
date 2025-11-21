from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import Optional
import logging
from datetime import datetime, date

from app.database import get_db
from app.models.species import Species, CategoryEnum, ConservationStatusEnum
from app.schemas.species import (
    SpeciesCreate,
    SpeciesUpdate,
    SpeciesResponse,
    SpeciesList
)
from app.config import get_settings
from app.cache import (
    cache_get, cache_set, cache_delete, cache_clear_pattern,
    get_random_species_cache, set_random_species_cache,
    get_popular_species_cache, set_popular_species_cache,
    invalidate_species_cache
)

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/species", tags=["Species"])


def get_api_response(success: bool, data=None, message: str = None):
    """Standard API response format"""
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


@router.get("")
def get_species(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
    conservation_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(name|scientific_name|search_count|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = None
):
    """Get paginated list of species with filters and sorting"""
    try:
        query = db.query(Species)

        # Apply filters
        if category:
            query = query.filter(Species.category == category)
        if region:
            query = query.filter(Species.region == region)
        if country:
            query = query.filter(Species.country == country)
        if conservation_status:
            query = query.filter(Species.conservation_status == conservation_status)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Species.name.ilike(search_term)) |
                (Species.scientific_name.ilike(search_term))
            )

        # Get total count
        total = query.count()
        pages = (total + limit - 1) // limit if total > 0 else 0

        # Apply sorting
        sort_column = getattr(Species, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        items = query.offset((page - 1) * limit).limit(limit).all()

        logger.info(f"Species list retrieved: {len(items)} items, page {page}/{pages}")

        return get_api_response(True, {
            "items": items,
            "total": total,
            "page": page,
            "pages": pages,
            "limit": limit
        })

    except Exception as e:
        logger.error(f"Error fetching species list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch species list")


@router.get("/random")
def get_random_species(db: Session = Depends(get_db)):
    """Get random species of the day (same result for entire day)"""
    try:
        # Create date-based cache key
        today = date.today().isoformat()

        # Try to get from cache
        cached = get_random_species_cache(today)
        if cached:
            logger.info("Random species served from cache")
            return get_api_response(True, cached)

        # Get random species using date as seed
        seed = int(today.replace("-", ""))

        # Get total count
        total = db.query(func.count(Species.id)).scalar()
        if total == 0:
            raise HTTPException(status_code=404, detail="No species found")

        # Calculate deterministic "random" index based on date
        random_index = seed % total

        species = db.query(Species).offset(random_index).first()

        if not species:
            raise HTTPException(status_code=404, detail="Species not found")

        # Prepare response data
        species_data = {
            "id": species.id,
            "name": species.name,
            "scientific_name": species.scientific_name,
            "category": species.category.value if hasattr(species.category, 'value') else species.category,
            "region": species.region,
            "country": species.country,
            "description": species.description,
            "characteristics": species.characteristics,
            "conservation_status": species.conservation_status.value if hasattr(species.conservation_status, 'value') else species.conservation_status,
            "image_url": species.image_url,
            "search_count": species.search_count
        }

        # Cache for 24 hours
        set_random_species_cache(today, species_data)

        logger.info(f"Random species of the day: {species.name}")
        return get_api_response(True, species_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random species: {e}")
        raise HTTPException(status_code=500, detail="Failed to get random species")


@router.get("/{species_id}")
def get_species_by_id(species_id: int, db: Session = Depends(get_db)):
    """Get specific species by ID and increment view count"""
    try:
        species = db.query(Species).filter(Species.id == species_id).first()

        if not species:
            logger.warning(f"Species not found: {species_id}")
            raise HTTPException(status_code=404, detail="Species not found")

        # Increment search count
        species.search_count = (species.search_count or 0) + 1
        db.commit()
        db.refresh(species)

        logger.info(f"Species retrieved: {species.name} (views: {species.search_count})")
        return get_api_response(True, species)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching species {species_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch species")


@router.post("", status_code=201)
def create_species(species_data: SpeciesCreate, db: Session = Depends(get_db)):
    """Create a new species (admin only)"""
    try:
        # Check for duplicate
        existing = db.query(Species).filter(
            Species.name == species_data.name,
            Species.country == species_data.country
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Species '{species_data.name}' already exists in {species_data.country}"
            )

        species = Species(**species_data.model_dump())
        db.add(species)
        db.commit()
        db.refresh(species)

        logger.info(f"New species created: {species.name} (ID: {species.id})")
        return get_api_response(True, species, "Species created successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating species: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create species")


@router.put("/{species_id}")
def update_species(
    species_id: int,
    species_data: SpeciesUpdate,
    db: Session = Depends(get_db)
):
    """Update a species"""
    try:
        species = db.query(Species).filter(Species.id == species_id).first()

        if not species:
            raise HTTPException(status_code=404, detail="Species not found")

        update_data = species_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(species, field, value)

        db.commit()
        db.refresh(species)

        logger.info(f"Species updated: {species.name} (ID: {species_id})")
        return get_api_response(True, species, "Species updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating species {species_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update species")


@router.delete("/{species_id}", status_code=204)
def delete_species(species_id: int, db: Session = Depends(get_db)):
    """Delete a species"""
    try:
        species = db.query(Species).filter(Species.id == species_id).first()

        if not species:
            raise HTTPException(status_code=404, detail="Species not found")

        name = species.name
        db.delete(species)
        db.commit()

        logger.info(f"Species deleted: {name} (ID: {species_id})")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting species {species_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete species")


@router.get("/stats/summary")
def get_species_stats(db: Session = Depends(get_db)):
    """Get overall species statistics"""
    try:
        cache_key = "species:stats:summary"

        cached = cache_get(cache_key)
        if cached:
            return get_api_response(True, cached)

        total = db.query(func.count(Species.id)).scalar()

        by_category = db.query(
            Species.category,
            func.count(Species.id)
        ).group_by(Species.category).all()

        by_country = db.query(
            Species.country,
            func.count(Species.id)
        ).group_by(Species.country).all()

        by_status = db.query(
            Species.conservation_status,
            func.count(Species.id)
        ).group_by(Species.conservation_status).all()

        stats = {
            "total": total,
            "by_category": {str(cat.value if hasattr(cat, 'value') else cat): count for cat, count in by_category},
            "by_country": {country: count for country, count in by_country},
            "by_conservation_status": {str(status.value if hasattr(status, 'value') else status): count for status, count in by_status}
        }

        cache_set(cache_key, stats, ttl=1800)

        logger.info("Species statistics retrieved")
        return get_api_response(True, stats)

    except Exception as e:
        logger.error(f"Error fetching species stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/popular/list")
def get_popular_species(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get most popular species by search count (cached for 30 minutes)"""
    try:
        # Try cache first
        cached = get_popular_species_cache()
        if cached and len(cached) >= limit:
            logger.info("Popular species served from cache")
            return get_api_response(True, cached[:limit])

        # Query from database
        species = db.query(Species).order_by(
            desc(Species.search_count)
        ).limit(limit).all()

        result = []
        for s in species:
            result.append({
                "id": s.id,
                "name": s.name,
                "scientific_name": s.scientific_name,
                "category": s.category.value if hasattr(s.category, 'value') else s.category,
                "region": s.region,
                "country": s.country,
                "conservation_status": s.conservation_status.value if hasattr(s.conservation_status, 'value') else s.conservation_status,
                "image_url": s.image_url,
                "search_count": s.search_count or 0
            })

        # Cache for 30 minutes
        set_popular_species_cache(result)

        logger.info(f"Popular species retrieved: {len(result)} items")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching popular species: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch popular species")
