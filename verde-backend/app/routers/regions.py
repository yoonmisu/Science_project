from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
import logging

from app.database import get_db
from app.models.species import Species
from app.models.region_biodiversity import RegionBiodiversity
from app.schemas.region import RegionBiodiversityResponse, RegionBiodiversityCreate
from app.schemas.species import SpeciesResponse
from app.api.response import APIResponse, ErrorCodes
from app.utils.heatmap import calculate_country_heatmap_data, get_heatmap_legend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regions", tags=["Regions"])


@router.get("/")
def get_all_regions(db: Session = Depends(get_db)):
    """
    전체 지역 목록 및 통계 - 히트맵 데이터 포함

    Returns:
        - items: 지역 목록 (멸종위기종 수 기준 정렬)
        - heatmap: 히트맵 색상 데이터 (녹색 계열)
        - legend: 히트맵 범례
    """
    try:
        regions = db.query(RegionBiodiversity).order_by(
            desc(RegionBiodiversity.endangered_count)
        ).all()

        logger.info(f"Regions list fetched: {len(regions)} items")

        # 지역 데이터를 히트맵 형식으로 변환
        region_stats = [
            {
                "region_name": r.region_name,
                "country": r.country,
                "endangered_count": r.endangered_count,
                "total_species_count": r.total_species_count
            }
            for r in regions
        ]

        # 히트맵 데이터 계산 (녹색 계열)
        heatmap_data = calculate_country_heatmap_data(region_stats)

        return APIResponse.success(
            data={
                "items": [RegionBiodiversityResponse.model_validate(r) for r in regions],
                "total": len(regions),
                "heatmap": heatmap_data,
                "legend": get_heatmap_legend()
            },
            source="database"
        )
    except Exception as e:
        logger.error(f"Error fetching regions: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="지역 목록을 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"error": str(e)}
        )


@router.get("/{region}/species")
def get_region_species(
    region: str,
    category: Optional[str] = Query(None, description="카테고리 필터"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """특정 지역의 생물종 목록 (페이지네이션)"""
    try:
        query = db.query(Species).filter(Species.region == region)

        if category:
            query = query.filter(Species.category == category)

        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()

        logger.info(f"Region species fetched: {region} - {total} items")

        return APIResponse.paginated(
            items=[SpeciesResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            limit=limit,
            source="database",
            additional_data={
                "region": region,
                "category": category
            }
        )
    except Exception as e:
        logger.error(f"Error fetching region species: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="지역 생물종 목록을 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"region": region, "error": str(e)}
        )


@router.get("/{region}/biodiversity")
def get_region_biodiversity(region: str, db: Session = Depends(get_db)):
    """지역별 생물 다양성 상세 통계"""
    try:
        # RegionBiodiversity 테이블에서 조회
        region_data = db.query(RegionBiodiversity).filter(
            RegionBiodiversity.region_name == region
        ).first()

        if not region_data:
            # 테이블에 없으면 Species에서 직접 계산
            total = db.query(Species).filter(Species.region == region).count()

            if total == 0:
                raise HTTPException(status_code=404, detail="지역을 찾을 수 없습니다")

            # 카테고리별 집계
            by_category = db.query(
                Species.category,
                func.count(Species.id).label("count")
            ).filter(
                Species.region == region
            ).group_by(Species.category).all()

            # 보전상태별 집계
            by_status = db.query(
                Species.conservation_status,
                func.count(Species.id).label("count")
            ).filter(
                Species.region == region,
                Species.conservation_status.isnot(None)
            ).group_by(Species.conservation_status).all()

            # 멸종위기종 수 (멸종위기, 취약)
            endangered = db.query(Species).filter(
                Species.region == region,
                Species.conservation_status.in_(["멸종위기", "취약"])
            ).count()

            category_stats = {c.category: c.count for c in by_category}

            result = {
                "success": True,
                "data": {
                    "region_name": region,
                    "total_species_count": total,
                    "endangered_count": endangered,
                    "plant_count": category_stats.get("식물", 0),
                    "animal_count": category_stats.get("동물", 0),
                    "insect_count": category_stats.get("곤충", 0),
                    "marine_count": category_stats.get("해양생물", 0),
                    "by_conservation_status": {s.conservation_status: s.count for s in by_status}
                }
            }
        else:
            # 보전상태별 추가 통계
            by_status = db.query(
                Species.conservation_status,
                func.count(Species.id).label("count")
            ).filter(
                Species.region == region,
                Species.conservation_status.isnot(None)
            ).group_by(Species.conservation_status).all()

            result = {
                "success": True,
                "data": {
                    **RegionBiodiversityResponse.model_validate(region_data).model_dump(),
                    "by_conservation_status": {s.conservation_status: s.count for s in by_status}
                }
            }

        logger.info(f"Region biodiversity fetched: {region}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching region biodiversity: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.post("/", status_code=201)
def create_region_biodiversity(
    region_data: RegionBiodiversityCreate,
    db: Session = Depends(get_db)
):
    """지역 생물다양성 정보 등록"""
    try:
        existing = db.query(RegionBiodiversity).filter(
            RegionBiodiversity.region_name == region_data.region_name
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="이미 등록된 지역입니다")

        region = RegionBiodiversity(**region_data.model_dump())
        db.add(region)
        db.commit()
        db.refresh(region)

        logger.info(f"Region created: {region.region_name}")

        return {
            "success": True,
            "data": RegionBiodiversityResponse.model_validate(region),
            "message": "지역 정보가 성공적으로 등록되었습니다"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating region: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/{region}/categories/{category}")
def get_region_category_species(
    region: str,
    category: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """지역 및 카테고리별 종 목록"""
    try:
        query = db.query(Species).filter(
            Species.region == region,
            Species.category == category
        )

        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()
        pages = (total + limit - 1) // limit

        return {
            "success": True,
            "data": {
                "region": region,
                "category": category,
                "items": [SpeciesResponse.model_validate(item) for item in items],
                "total": total,
                "page": page,
                "pages": pages
            }
        }
    except Exception as e:
        logger.error(f"Error fetching region category species: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")
