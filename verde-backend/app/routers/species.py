from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import Optional
from datetime import date
import logging

from app.database import get_db
from app.cache import (
    cache_get, cache_set, CacheKeys,
    get_or_set_cache
)
from app.models.species import Species
from app.schemas.species import (
    SpeciesCreate,
    SpeciesUpdate,
    SpeciesResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/species", tags=["Species"])


@router.get("/")
def get_species(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    region: Optional[str] = Query(None, description="지역 필터"),
    country: Optional[str] = Query(None, description="국가 필터"),
    conservation_status: Optional[str] = Query(None, description="보전 상태 필터"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("created_at", description="정렬 기준"),
    sort_order: Optional[str] = Query("desc", description="정렬 순서 (asc/desc)"),
    db: Session = Depends(get_db)
):
    """종 목록 조회 - 필터링, 페이지네이션, 정렬 지원"""
    try:
        query = db.query(Species)

        # 필터링
        if category:
            query = query.filter(Species.category == category)
        if region:
            query = query.filter(Species.region == region)
        if country:
            query = query.filter(Species.country == country)
        if conservation_status:
            query = query.filter(Species.conservation_status == conservation_status)

        # 정렬
        sort_column = getattr(Species, sort_by, Species.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # 전체 개수
        total = query.count()
        pages = (total + limit - 1) // limit

        # 페이지네이션
        items = query.offset((page - 1) * limit).limit(limit).all()

        logger.info(f"Species list fetched: {len(items)} items, page {page}")

        return {
            "success": True,
            "data": {
                "items": [SpeciesResponse.model_validate(item) for item in items],
                "total": total,
                "page": page,
                "pages": pages
            }
        }
    except Exception as e:
        logger.error(f"Error fetching species list: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/random")
def get_random_species(db: Session = Depends(get_db)):
    """랜덤 생물종 반환 - 날짜 기반 시드로 하루에 같은 결과 (24시간 캐싱)"""
    try:
        cache_key = CacheKeys.random_species_key()

        # 캐시 확인
        cached = cache_get(cache_key)
        if cached:
            logger.info("Random species served from cache")
            return cached

        # 날짜 기반 시드로 랜덤 선택
        today_seed = int(date.today().strftime("%Y%m%d"))

        total = db.query(Species).count()
        if total == 0:
            raise HTTPException(status_code=404, detail="등록된 생물종이 없습니다")

        # 시드 기반 인덱스 계산
        index = today_seed % total
        species = db.query(Species).offset(index).first()

        if not species:
            raise HTTPException(status_code=404, detail="생물종을 찾을 수 없습니다")

        result = {
            "success": True,
            "data": SpeciesResponse.model_validate(species).model_dump()
        }

        # 24시간 캐싱
        cache_set(cache_key, result, CacheKeys.RANDOM_SPECIES_TTL)
        logger.info(f"Random species cached: {species.name}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching random species: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/popular")
def get_popular_species(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """인기 생물종 조회 (30분 캐싱)"""
    try:
        cache_key = f"{CacheKeys.POPULAR_SPECIES}:{limit}"

        # 캐시 확인
        cached = cache_get(cache_key)
        if cached:
            logger.info("Popular species served from cache")
            return cached

        # DB에서 조회
        species = db.query(Species).order_by(
            desc(Species.search_count)
        ).limit(limit).all()

        result = {
            "success": True,
            "data": [SpeciesResponse.model_validate(s).model_dump() for s in species]
        }

        # 30분 캐싱
        cache_set(cache_key, result, CacheKeys.POPULAR_SPECIES_TTL)
        logger.info(f"Popular species cached: {len(species)} items")

        return result
    except Exception as e:
        logger.error(f"Error fetching popular species: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/{species_id}")
def get_species_by_id(species_id: int, db: Session = Depends(get_db)):
    """특정 종 조회 - 조회수 자동 증가"""
    try:
        species = db.query(Species).filter(Species.id == species_id).first()

        if not species:
            logger.warning(f"Species not found: {species_id}")
            raise HTTPException(status_code=404, detail="생물종을 찾을 수 없습니다")

        # 조회수 증가
        species.search_count += 1
        db.commit()
        db.refresh(species)

        logger.info(f"Species fetched: {species.name} (id={species_id}), views={species.search_count}")

        return {
            "success": True,
            "data": SpeciesResponse.model_validate(species)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching species {species_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.post("/", status_code=201)
def create_species(species_data: SpeciesCreate, db: Session = Depends(get_db)):
    """새 생물종 추가 (관리자용)"""
    try:
        species = Species(
            name=species_data.name,
            scientific_name=species_data.scientific_name,
            category=species_data.category.value if species_data.category else None,
            region=species_data.region,
            country=species_data.country,
            description=species_data.description,
            characteristics=species_data.characteristics,
            image_url=species_data.image_url,
            conservation_status=species_data.conservation_status.value if species_data.conservation_status else None,
            search_count=0
        )

        db.add(species)
        db.commit()
        db.refresh(species)

        logger.info(f"New species created: {species.name} (id={species.id})")

        return {
            "success": True,
            "data": SpeciesResponse.model_validate(species),
            "message": "생물종이 성공적으로 등록되었습니다"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating species: {str(e)}")
        raise HTTPException(status_code=500, detail="생물종 등록 중 오류가 발생했습니다")


@router.put("/{species_id}")
def update_species(
    species_id: int,
    species_data: SpeciesUpdate,
    db: Session = Depends(get_db)
):
    """종 정보 수정"""
    try:
        species = db.query(Species).filter(Species.id == species_id).first()

        if not species:
            raise HTTPException(status_code=404, detail="생물종을 찾을 수 없습니다")

        update_data = species_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['category', 'conservation_status'] and value:
                value = value.value
            setattr(species, field, value)

        db.commit()
        db.refresh(species)

        logger.info(f"Species updated: {species.name} (id={species_id})")

        return {
            "success": True,
            "data": SpeciesResponse.model_validate(species)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating species {species_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.delete("/{species_id}", status_code=204)
def delete_species(species_id: int, db: Session = Depends(get_db)):
    """종 삭제"""
    try:
        species = db.query(Species).filter(Species.id == species_id).first()

        if not species:
            raise HTTPException(status_code=404, detail="생물종을 찾을 수 없습니다")

        db.delete(species)
        db.commit()

        logger.info(f"Species deleted: id={species_id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting species {species_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")
