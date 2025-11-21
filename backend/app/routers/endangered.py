from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import Optional
import logging
import redis
import json

from app.database import get_db
from app.models.species import Species, ConservationStatusEnum
from app.schemas.species import SpeciesResponse
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/endangered", tags=["Endangered Species"])

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


# Endangered statuses
ENDANGERED_STATUSES = [
    ConservationStatusEnum.ENDANGERED,
    ConservationStatusEnum.VULNERABLE
]


@router.get("")
def get_endangered_species(
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    category: Optional[str] = None,
    country: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get list of endangered species with filters and pagination"""
    try:
        query = db.query(Species).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        )

        if region:
            query = query.filter(Species.region == region)
        if category:
            query = query.filter(Species.category == category)
        if country:
            query = query.filter(Species.country == country)

        total = query.count()
        pages = (total + limit - 1) // limit if total > 0 else 0

        species = query.order_by(
            # Most critical first
            Species.conservation_status,
            desc(Species.search_count)
        ).offset((page - 1) * limit).limit(limit).all()

        logger.info(f"Endangered species retrieved: {len(species)} items")

        return get_api_response(True, {
            "items": species,
            "total": total,
            "page": page,
            "pages": pages
        })

    except Exception as e:
        logger.error(f"Error fetching endangered species: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch endangered species")


@router.get("/most-mentioned")
def get_most_mentioned_endangered(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """Get top 10 most viewed endangered species"""
    try:
        cache_key = f"endangered:most-mentioned:{limit}"

        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info("Most mentioned endangered species served from cache")
                return get_api_response(True, json.loads(cached))

        species = db.query(Species).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).order_by(
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

        if redis_client:
            redis_client.setex(cache_key, 1800, json.dumps(result))

        logger.info(f"Most mentioned endangered species: {len(result)} items")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching most mentioned endangered: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch most mentioned species")


@router.get("/statistics")
def get_endangered_statistics(db: Session = Depends(get_db)):
    """Get comprehensive endangered species statistics"""
    try:
        cache_key = "endangered:statistics"

        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info("Endangered statistics served from cache")
                return get_api_response(True, json.loads(cached))

        # Total endangered
        total_endangered = db.query(func.count(Species.id)).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).scalar()

        # By conservation status
        by_status = db.query(
            Species.conservation_status,
            func.count(Species.id)
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.conservation_status).all()

        # By category
        by_category = db.query(
            Species.category,
            func.count(Species.id)
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.category).all()

        # By country
        by_country = db.query(
            Species.country,
            func.count(Species.id)
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.country).order_by(
            desc(func.count(Species.id))
        ).all()

        # By region
        by_region = db.query(
            Species.region,
            func.count(Species.id)
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.region).order_by(
            desc(func.count(Species.id))
        ).limit(10).all()

        # Total species for percentage calculation
        total_species = db.query(func.count(Species.id)).scalar()
        endangered_percentage = round(
            (total_endangered / total_species * 100) if total_species > 0 else 0, 2
        )

        result = {
            "total_endangered": total_endangered,
            "total_species": total_species,
            "endangered_percentage": endangered_percentage,
            "by_status": {
                str(status.value if hasattr(status, 'value') else status): count
                for status, count in by_status
            },
            "by_category": {
                str(cat.value if hasattr(cat, 'value') else cat): count
                for cat, count in by_category
            },
            "by_country": {
                country: count for country, count in by_country
            },
            "top_regions": [
                {"region": region, "count": count}
                for region, count in by_region
            ]
        }

        if redis_client:
            redis_client.setex(cache_key, 1800, json.dumps(result))

        logger.info("Endangered statistics retrieved")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching endangered statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/by-status/{status}")
def get_species_by_conservation_status(
    status: str,
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get species by specific conservation status"""
    try:
        # Validate status
        valid_statuses = [s.value for s in ConservationStatusEnum]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid options: {valid_statuses}"
            )

        query = db.query(Species).filter(
            Species.conservation_status == status
        )

        if region:
            query = query.filter(Species.region == region)
        if category:
            query = query.filter(Species.category == category)

        total = query.count()
        pages = (total + limit - 1) // limit if total > 0 else 0

        species = query.order_by(
            desc(Species.search_count)
        ).offset((page - 1) * limit).limit(limit).all()

        logger.info(f"Species with status '{status}': {len(species)} items")

        return get_api_response(True, {
            "status": status,
            "items": species,
            "total": total,
            "page": page,
            "pages": pages
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching species by status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch species")


@router.get("/country/{country}/summary")
def get_country_endangered_summary(country: str, db: Session = Depends(get_db)):
    """Get detailed endangered species summary for a specific country"""
    try:
        cache_key = f"endangered:country:{country}"

        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                return get_api_response(True, json.loads(cached))

        endangered = db.query(Species).filter(
            Species.country == country,
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).all()

        # Group by status
        critically = [s for s in endangered if s.conservation_status == ConservationStatusEnum.ENDANGERED]
        vulnerable = [s for s in endangered if s.conservation_status == ConservationStatusEnum.VULNERABLE]

        # Group by category
        by_category = {}
        for s in endangered:
            cat = s.category.value if hasattr(s.category, 'value') else s.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "id": s.id,
                "name": s.name,
                "conservation_status": s.conservation_status.value if hasattr(s.conservation_status, 'value') else s.conservation_status
            })

        result = {
            "country": country,
            "total_endangered": len(endangered),
            "멸종위기": {
                "count": len(critically),
                "species": [
                    {"id": s.id, "name": s.name, "category": s.category.value if hasattr(s.category, 'value') else s.category}
                    for s in critically[:10]  # Top 10
                ]
            },
            "취약": {
                "count": len(vulnerable),
                "species": [
                    {"id": s.id, "name": s.name, "category": s.category.value if hasattr(s.category, 'value') else s.category}
                    for s in vulnerable[:10]  # Top 10
                ]
            },
            "by_category": {
                cat: {"count": len(species), "species": species[:5]}
                for cat, species in by_category.items()
            }
        }

        if redis_client:
            redis_client.setex(cache_key, 1800, json.dumps(result))

        logger.info(f"Endangered summary for country '{country}' retrieved")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching country endangered summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary")


@router.get("/region/{region}/summary")
def get_region_endangered_summary(region: str, db: Session = Depends(get_db)):
    """Get detailed endangered species summary for a specific region"""
    try:
        endangered = db.query(Species).filter(
            Species.region == region,
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).all()

        critically = [s for s in endangered if s.conservation_status == ConservationStatusEnum.ENDANGERED]
        vulnerable = [s for s in endangered if s.conservation_status == ConservationStatusEnum.VULNERABLE]

        result = {
            "region": region,
            "total_endangered": len(endangered),
            "멸종위기": {
                "count": len(critically),
                "species": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "category": s.category.value if hasattr(s.category, 'value') else s.category
                    }
                    for s in critically
                ]
            },
            "취약": {
                "count": len(vulnerable),
                "species": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "category": s.category.value if hasattr(s.category, 'value') else s.category
                    }
                    for s in vulnerable
                ]
            }
        }

        logger.info(f"Endangered summary for region '{region}' retrieved")
        return get_api_response(True, result)

    except Exception as e:
        logger.error(f"Error fetching region endangered summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary")
