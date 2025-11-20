from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.species import Species, CategoryEnum
from app.schemas.species import (
    SpeciesCreate,
    SpeciesUpdate,
    SpeciesResponse,
    SpeciesList
)

router = APIRouter(prefix="/species", tags=["Species"])


@router.get("", response_model=SpeciesList)
def get_species(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = None
):
    """Get paginated list of species with optional filters"""
    query = db.query(Species)

    if category:
        query = query.filter(Species.category == category)
    if region:
        query = query.filter(Species.region == region)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Species.name_ko.ilike(search_term)) |
            (Species.name_en.ilike(search_term)) |
            (Species.name_scientific.ilike(search_term))
        )

    total = query.count()
    pages = (total + size - 1) // size

    items = query.offset((page - 1) * size).limit(size).all()

    return SpeciesList(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/{species_id}", response_model=SpeciesResponse)
def get_species_by_id(species_id: int, db: Session = Depends(get_db)):
    """Get a specific species by ID"""
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species


@router.post("", response_model=SpeciesResponse, status_code=201)
def create_species(species_data: SpeciesCreate, db: Session = Depends(get_db)):
    """Create a new species"""
    species = Species(**species_data.model_dump())
    db.add(species)
    db.commit()
    db.refresh(species)
    return species


@router.put("/{species_id}", response_model=SpeciesResponse)
def update_species(
    species_id: int,
    species_data: SpeciesUpdate,
    db: Session = Depends(get_db)
):
    """Update a species"""
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")

    update_data = species_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(species, field, value)

    db.commit()
    db.refresh(species)
    return species


@router.delete("/{species_id}", status_code=204)
def delete_species(species_id: int, db: Session = Depends(get_db)):
    """Delete a species"""
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")

    db.delete(species)
    db.commit()


@router.get("/region/{region}", response_model=list[SpeciesResponse])
def get_species_by_region(
    region: str,
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """Get all species for a specific region"""
    query = db.query(Species).filter(Species.region == region)

    if category:
        query = query.filter(Species.category == category)

    return query.all()


@router.get("/category/{category}", response_model=list[SpeciesResponse])
def get_species_by_category(
    category: str,
    db: Session = Depends(get_db),
    region: Optional[str] = None
):
    """Get all species for a specific category"""
    query = db.query(Species).filter(Species.category == category)

    if region:
        query = query.filter(Species.region == region)

    return query.all()


@router.get("/stats/summary")
def get_species_stats(db: Session = Depends(get_db)):
    """Get overall species statistics"""
    total = db.query(func.count(Species.id)).scalar()
    by_category = db.query(
        Species.category,
        func.count(Species.id)
    ).group_by(Species.category).all()

    by_region = db.query(
        Species.region,
        func.count(Species.id)
    ).group_by(Species.region).all()

    return {
        "total": total,
        "by_category": {str(cat): count for cat, count in by_category},
        "by_region": {region: count for region, count in by_region}
    }
