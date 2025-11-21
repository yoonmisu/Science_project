from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
import logging
import redis
import json

from app.database import get_db
from app.models.species import Species, ConservationStatusEnum
from app.models.region_biodiversity import RegionBiodiversity
from app.schemas.region import (
    RegionBiodiversityResponse,
    RegionBiodiversityCreate,
    RegionStats
)
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regions", tags=["Regions"])

# Redis client
try:
    redis_client = redis.from_url(settings.redis_url)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None


def get_api_response(success: bool, data=None, message: str = None):
    """Standard API response format"""
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


@router.get("")
def get_all_regions(db: Session = Depends(get_db)):
    """Get all regions with biodiversity statistics, sorted by species count"""
    try:
        cache_key = "regions:all"

        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info("Regions served from cache")
                return get_api_response(True, json.loads(cached))

        regions = db.query(RegionBiodiversity).order_by(
            desc(RegionBiodiversity.total_species_count)
        ).all()

        result = []
        for region in regions:
            result.append({
                "id": region.id,
                "region_name": region.region_name,
                "country": region.country,
                "latitude": region.latitude,
                "longitude": region.longitude,
                "total_species_count": region.total_species_count,
                "endangered_count": region.endangered_count,
                "plant_count": region.plant_count,
                "animal_count": region.animal_count,
                "insect_count": region.insect_count,
                "marine_count": region.marine_count,
                "last_updated": region.last_updated.isoformat() if region.last_updated else None
            })

        if redis_client:
            redis_client.setex(cache_key, 1800, json.dumps(result))

        logger.info(f"Regions retrieved: {len(result)} items")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching regions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch regions")


@router.get("/list")
def get_region_list(db: Session = Depends(get_db)):
    """Get simple list of available regions"""
    try:
        regions = db.query(
            RegionBiodiversity.region_name,
            RegionBiodiversity.country
        ).all()

        result = [
            {"region_name": r[0], "country": r[1]}
            for r in regions
        ]

        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching region list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch region list")


@router.get("/{region}/species")
def get_region_species(
    region: str,
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get species list for a specific region with optional category filter"""
    try:
        query = db.query(Species).filter(Species.region == region)

        if category:
            query = query.filter(Species.category == category)

        total = query.count()
        pages = (total + limit - 1) // limit if total > 0 else 0

        species = query.order_by(desc(Species.search_count)).offset(
            (page - 1) * limit
        ).limit(limit).all()

        # Get region info
        region_info = db.query(RegionBiodiversity).filter(
            RegionBiodiversity.region_name == region
        ).first()

        logger.info(f"Species for region '{region}': {len(species)} items")

        return get_api_response(True, {
            "region": region,
            "country": region_info.country if region_info else None,
            "items": species,
            "total": total,
            "page": page,
            "pages": pages
        })

    except Exception as e:
        logger.error(f"Error fetching species for region {region}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch region species")


@router.get("/{region}/biodiversity")
def get_region_biodiversity(region: str, db: Session = Depends(get_db)):
    """Get detailed biodiversity statistics for a specific region"""
    try:
        cache_key = f"regions:{region}:biodiversity"

        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return get_api_response(True, json.loads(cached))

        # Get region data
        region_data = db.query(RegionBiodiversity).filter(
            RegionBiodiversity.region_name == region
        ).first()

        if not region_data:
            raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

        # Get additional statistics from species
        species_stats = db.query(
            Species.conservation_status,
            func.count(Species.id)
        ).filter(
            Species.region == region
        ).group_by(Species.conservation_status).all()

        # Most viewed species in region
        top_species = db.query(Species).filter(
            Species.region == region
        ).order_by(desc(Species.search_count)).limit(5).all()

        result = {
            "region_name": region_data.region_name,
            "country": region_data.country,
            "coordinates": {
                "latitude": region_data.latitude,
                "longitude": region_data.longitude
            },
            "species_count": {
                "total": region_data.total_species_count,
                "endangered": region_data.endangered_count,
                "by_category": {
                    "식물": region_data.plant_count,
                    "동물": region_data.animal_count,
                    "곤충": region_data.insect_count,
                    "해양생물": region_data.marine_count
                }
            },
            "by_conservation_status": {
                str(status.value if hasattr(status, 'value') else status): count
                for status, count in species_stats
            },
            "top_species": [
                {
                    "id": s.id,
                    "name": s.name,
                    "category": s.category.value if hasattr(s.category, 'value') else s.category,
                    "search_count": s.search_count
                }
                for s in top_species
            ],
            "last_updated": region_data.last_updated.isoformat() if region_data.last_updated else None
        }

        if redis_client:
            redis_client.setex(cache_key, 1800, json.dumps(result))

        logger.info(f"Biodiversity data for region '{region}' retrieved")
        return get_api_response(True, result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching biodiversity for region {region}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch biodiversity data")


@router.post("", status_code=201)
def create_or_update_region(
    region_data: RegionBiodiversityCreate,
    db: Session = Depends(get_db)
):
    """Create or update region biodiversity data"""
    try:
        existing = db.query(RegionBiodiversity).filter(
            RegionBiodiversity.region_name == region_data.region_name
        ).first()

        if existing:
            for field, value in region_data.model_dump().items():
                setattr(existing, field, value)
            db.commit()
            db.refresh(existing)
            result = existing
            message = "Region updated successfully"
        else:
            region = RegionBiodiversity(**region_data.model_dump())
            db.add(region)
            db.commit()
            db.refresh(region)
            result = region
            message = "Region created successfully"

        # Invalidate cache
        if redis_client:
            redis_client.delete("regions:all")
            redis_client.delete(f"regions:{region_data.region_name}:biodiversity")

        logger.info(f"Region '{region_data.region_name}' saved")
        return get_api_response(True, result, message)

    except Exception as e:
        logger.error(f"Error saving region: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save region")


@router.post("/refresh-stats")
def refresh_all_region_stats(db: Session = Depends(get_db)):
    """Recalculate statistics for all regions from species data"""
    try:
        # Get all unique regions from species
        regions = db.query(Species.region, Species.country).distinct().all()

        updated_count = 0
        for region_name, country in regions:
            species = db.query(Species).filter(Species.region == region_name).all()

            stats = {
                "total_species_count": len(species),
                "plant_count": sum(1 for s in species if s.category.value == "식물"),
                "animal_count": sum(1 for s in species if s.category.value == "동물"),
                "insect_count": sum(1 for s in species if s.category.value == "곤충"),
                "marine_count": sum(1 for s in species if s.category.value == "해양생물"),
                "endangered_count": sum(
                    1 for s in species
                    if s.conservation_status and s.conservation_status.value in ["멸종위기", "취약"]
                )
            }

            region_data = db.query(RegionBiodiversity).filter(
                RegionBiodiversity.region_name == region_name
            ).first()

            if region_data:
                for key, value in stats.items():
                    setattr(region_data, key, value)
            else:
                region_data = RegionBiodiversity(
                    region_name=region_name,
                    country=country,
                    **stats
                )
                db.add(region_data)

            updated_count += 1

        db.commit()

        # Invalidate all region caches
        if redis_client:
            redis_client.delete("regions:all")

        logger.info(f"Region statistics refreshed for {updated_count} regions")
        return get_api_response(True, {"updated_regions": updated_count}, "Statistics refreshed successfully")

    except Exception as e:
        logger.error(f"Error refreshing region stats: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to refresh statistics")
