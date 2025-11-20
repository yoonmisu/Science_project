from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.species import Species
from app.models.region_biodiversity import RegionBiodiversity
from app.schemas.region import (
    RegionBiodiversityResponse,
    RegionBiodiversityCreate,
    RegionStats,
    RegionComparison
)

router = APIRouter(prefix="/regions", tags=["Regions"])

# Predefined regions with Korean names
REGIONS = {
    "Korea": "한국",
    "Japan": "일본",
    "USA": "미국",
    "China": "중국",
    "Russia": "러시아"
}


@router.get("", response_model=list[RegionBiodiversityResponse])
def get_all_regions(db: Session = Depends(get_db)):
    """Get biodiversity data for all regions"""
    return db.query(RegionBiodiversity).all()


@router.get("/list")
def get_region_list():
    """Get list of available regions"""
    return [
        {"region": region, "region_ko": ko_name}
        for region, ko_name in REGIONS.items()
    ]


@router.get("/stats", response_model=RegionComparison)
def get_region_comparison(db: Session = Depends(get_db)):
    """Get comparative statistics for all regions"""
    regions_data = db.query(RegionBiodiversity).all()

    if not regions_data:
        # Calculate from species table if no pre-computed data
        return _calculate_region_stats(db)

    region_stats = []
    total_all = 0
    max_biodiversity = ("", 0)
    max_endangered = ("", 0)

    for region in regions_data:
        total_all += region.total_species

        if region.total_species > max_biodiversity[1]:
            max_biodiversity = (region.region, region.total_species)

        endangered_pct = (region.endangered_count / region.total_species * 100) if region.total_species > 0 else 0

        if region.endangered_count > max_endangered[1]:
            max_endangered = (region.region, region.endangered_count)

        region_stats.append(RegionStats(
            region=region.region,
            region_ko=region.region_ko,
            total_species=region.total_species,
            categories={
                "animal": region.animal_count,
                "plant": region.plant_count,
                "insect": region.insect_count,
                "marine": region.marine_count
            },
            endangered_percentage=round(endangered_pct, 2),
            biodiversity_index=region.biodiversity_index
        ))

    return RegionComparison(
        regions=region_stats,
        total_species_all=total_all,
        most_biodiverse=max_biodiversity[0],
        most_endangered=max_endangered[0]
    )


@router.get("/{region}", response_model=RegionBiodiversityResponse)
def get_region(region: str, db: Session = Depends(get_db)):
    """Get biodiversity data for a specific region"""
    region_data = db.query(RegionBiodiversity).filter(
        RegionBiodiversity.region == region
    ).first()

    if not region_data:
        raise HTTPException(status_code=404, detail="Region not found")

    return region_data


@router.get("/{region}/species")
def get_region_species(
    region: str,
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """Get all species for a specific region"""
    query = db.query(Species).filter(Species.region == region)

    if category:
        query = query.filter(Species.category == category)

    species = query.all()

    return {
        "region": region,
        "region_ko": REGIONS.get(region, region),
        "total": len(species),
        "species": species
    }


@router.post("", response_model=RegionBiodiversityResponse, status_code=201)
def create_region(
    region_data: RegionBiodiversityCreate,
    db: Session = Depends(get_db)
):
    """Create or update region biodiversity data"""
    existing = db.query(RegionBiodiversity).filter(
        RegionBiodiversity.region == region_data.region
    ).first()

    if existing:
        for field, value in region_data.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    region = RegionBiodiversity(**region_data.model_dump())
    db.add(region)
    db.commit()
    db.refresh(region)
    return region


@router.post("/refresh-stats")
def refresh_region_stats(db: Session = Depends(get_db)):
    """Recalculate and update region statistics from species data"""
    for region_name, region_ko in REGIONS.items():
        species = db.query(Species).filter(Species.region == region_name).all()

        stats = {
            "total_species": len(species),
            "animal_count": sum(1 for s in species if s.category.value == "animal"),
            "plant_count": sum(1 for s in species if s.category.value == "plant"),
            "insect_count": sum(1 for s in species if s.category.value == "insect"),
            "marine_count": sum(1 for s in species if s.category.value == "marine"),
            "endangered_count": sum(1 for s in species if s.is_endangered),
            "critically_endangered_count": sum(
                1 for s in species
                if hasattr(s.conservation_status, 'value') and s.conservation_status.value == "CR"
            )
        }

        # Update or create
        region_data = db.query(RegionBiodiversity).filter(
            RegionBiodiversity.region == region_name
        ).first()

        if region_data:
            for key, value in stats.items():
                setattr(region_data, key, value)
        else:
            region_data = RegionBiodiversity(
                region=region_name,
                region_ko=region_ko,
                **stats
            )
            db.add(region_data)

    db.commit()
    return {"message": "Region statistics refreshed successfully"}


def _calculate_region_stats(db: Session) -> RegionComparison:
    """Calculate region stats directly from species table"""
    region_stats = []
    total_all = 0
    max_biodiversity = ("", 0)
    max_endangered = ("", 0)

    for region_name, region_ko in REGIONS.items():
        species = db.query(Species).filter(Species.region == region_name).all()
        total = len(species)
        total_all += total

        endangered = sum(1 for s in species if s.is_endangered)

        if total > max_biodiversity[1]:
            max_biodiversity = (region_name, total)
        if endangered > max_endangered[1]:
            max_endangered = (region_name, endangered)

        region_stats.append(RegionStats(
            region=region_name,
            region_ko=region_ko,
            total_species=total,
            categories={
                "animal": sum(1 for s in species if s.category.value == "animal"),
                "plant": sum(1 for s in species if s.category.value == "plant"),
                "insect": sum(1 for s in species if s.category.value == "insect"),
                "marine": sum(1 for s in species if s.category.value == "marine")
            },
            endangered_percentage=round((endangered / total * 100) if total > 0 else 0, 2),
            biodiversity_index=None
        ))

    return RegionComparison(
        regions=region_stats,
        total_species_all=total_all,
        most_biodiverse=max_biodiversity[0],
        most_endangered=max_endangered[0]
    )
