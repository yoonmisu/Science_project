from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.species import Species, ConservationStatusEnum
from app.schemas.species import SpeciesResponse

router = APIRouter(prefix="/endangered", tags=["Endangered Species"])


@router.get("", response_model=list[SpeciesResponse])
def get_endangered_species(
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """Get list of endangered species with optional filters"""
    query = db.query(Species).filter(Species.is_endangered == True)

    if region:
        query = query.filter(Species.region == region)
    if category:
        query = query.filter(Species.category == category)
    if status:
        query = query.filter(Species.conservation_status == status)

    return query.limit(limit).all()


@router.get("/critical", response_model=list[SpeciesResponse])
def get_critically_endangered(
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    category: Optional[str] = None
):
    """Get critically endangered species (CR status)"""
    query = db.query(Species).filter(
        Species.conservation_status == ConservationStatusEnum.CR
    )

    if region:
        query = query.filter(Species.region == region)
    if category:
        query = query.filter(Species.category == category)

    return query.all()


@router.get("/stats")
def get_endangered_stats(db: Session = Depends(get_db)):
    """Get statistics about endangered species"""
    total_endangered = db.query(func.count(Species.id)).filter(
        Species.is_endangered == True
    ).scalar()

    by_status = db.query(
        Species.conservation_status,
        func.count(Species.id)
    ).filter(
        Species.is_endangered == True
    ).group_by(Species.conservation_status).all()

    by_region = db.query(
        Species.region,
        func.count(Species.id)
    ).filter(
        Species.is_endangered == True
    ).group_by(Species.region).all()

    by_category = db.query(
        Species.category,
        func.count(Species.id)
    ).filter(
        Species.is_endangered == True
    ).group_by(Species.category).all()

    return {
        "total_endangered": total_endangered,
        "by_status": {
            str(status): count for status, count in by_status
        },
        "by_region": {
            region: count for region, count in by_region
        },
        "by_category": {
            str(cat): count for cat, count in by_category
        }
    }


@router.get("/by-status/{status}", response_model=list[SpeciesResponse])
def get_species_by_conservation_status(
    status: str,
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    category: Optional[str] = None
):
    """Get species by specific conservation status"""
    try:
        conservation_status = ConservationStatusEnum(status)
    except ValueError:
        valid_statuses = [s.value for s in ConservationStatusEnum]
        return {"error": f"Invalid status. Valid options: {valid_statuses}"}

    query = db.query(Species).filter(
        Species.conservation_status == conservation_status
    )

    if region:
        query = query.filter(Species.region == region)
    if category:
        query = query.filter(Species.category == category)

    return query.all()


@router.get("/trends")
def get_population_trends(
    db: Session = Depends(get_db),
    region: Optional[str] = None
):
    """Get population trends for endangered species"""
    query = db.query(
        Species.population_trend,
        func.count(Species.id)
    ).filter(
        Species.is_endangered == True
    )

    if region:
        query = query.filter(Species.region == region)

    trends = query.group_by(Species.population_trend).all()

    return {
        "trends": {
            trend or "unknown": count for trend, count in trends
        }
    }


@router.get("/region/{region}/summary")
def get_region_endangered_summary(region: str, db: Session = Depends(get_db)):
    """Get detailed endangered species summary for a specific region"""
    endangered = db.query(Species).filter(
        Species.region == region,
        Species.is_endangered == True
    ).all()

    critical = [s for s in endangered if s.conservation_status == ConservationStatusEnum.CR]
    endangered_status = [s for s in endangered if s.conservation_status == ConservationStatusEnum.EN]
    vulnerable = [s for s in endangered if s.conservation_status == ConservationStatusEnum.VU]

    return {
        "region": region,
        "total_endangered": len(endangered),
        "critically_endangered": {
            "count": len(critical),
            "species": [{"id": s.id, "name_ko": s.name_ko, "category": s.category.value} for s in critical]
        },
        "endangered": {
            "count": len(endangered_status),
            "species": [{"id": s.id, "name_ko": s.name_ko, "category": s.category.value} for s in endangered_status]
        },
        "vulnerable": {
            "count": len(vulnerable),
            "species": [{"id": s.id, "name_ko": s.name_ko, "category": s.category.value} for s in vulnerable]
        }
    }
