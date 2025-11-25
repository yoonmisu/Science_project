from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
import logging

from app.database import get_db
from app.models.species import Species
from app.schemas.species import SpeciesResponse
from app.api.response import APIResponse, ErrorCodes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/endangered", tags=["Endangered Species"])

# 멸종위기 상태 목록
ENDANGERED_STATUSES = ["멸종위기", "취약"]


@router.get("/")
def get_endangered_species(
    region: Optional[str] = Query(None, description="지역 필터"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """멸종위기종 전체 목록 (페이지네이션)"""
    try:
        query = db.query(Species).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        )

        if region:
            query = query.filter(Species.region == region)
        if category:
            query = query.filter(Species.category == category)

        total = query.count()
        items = query.order_by(desc(Species.search_count)).offset(
            (page - 1) * limit
        ).limit(limit).all()

        logger.info(f"Endangered species fetched: {total} items")

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
        logger.error(f"Error fetching endangered species: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="멸종위기종 목록을 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"error": str(e)}
        )


@router.get("/most-mentioned")
def get_most_mentioned_endangered(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """가장 많이 조회된 멸종위기종 Top 10"""
    try:
        species = db.query(Species).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).order_by(
            desc(Species.search_count)
        ).limit(limit).all()

        logger.info(f"Most mentioned endangered species: {len(species)} items")

        return {
            "success": True,
            "data": [
                {
                    "id": s.id,
                    "name": s.name,
                    "scientific_name": s.scientific_name,
                    "category": s.category,
                    "region": s.region,
                    "conservation_status": s.conservation_status,
                    "search_count": s.search_count,
                    "image_url": s.image_url
                }
                for s in species
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching most mentioned: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/statistics")
def get_endangered_statistics(db: Session = Depends(get_db)):
    """멸종위기종 통계 - 카테고리별, 지역별 집계 (히트맵 포함)"""
    try:
        from app.utils.heatmap import calculate_country_heatmap_data, get_heatmap_legend

        # 전체 멸종위기종 수
        total = db.query(Species).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).count()

        # 카테고리별 통계
        by_category = db.query(
            Species.category,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.category).all()

        # 지역별 통계
        by_region = db.query(
            Species.region,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.region).order_by(
            desc("count")
        ).all()

        # 보전상태별 통계
        by_status = db.query(
            Species.conservation_status,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.conservation_status).all()

        # 국가별 통계 (히트맵용)
        by_country = db.query(
            Species.country,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        ).group_by(Species.country).order_by(
            desc("count")
        ).all()

        # 히트맵 데이터 계산 (녹색 계열)
        country_stats = [
            {"country": c.country, "endangered_count": c.count}
            for c in by_country
        ]
        heatmap_data = calculate_country_heatmap_data(country_stats)

        logger.info("Endangered statistics fetched")

        return APIResponse.success(
            data={
                "total_endangered": total,
                "by_category": {c.category: c.count for c in by_category},
                "by_region": [
                    {"region": r.region, "count": r.count}
                    for r in by_region
                ],
                "by_conservation_status": {s.conservation_status: s.count for s in by_status},
                "by_country": [
                    {"country": c.country, "count": c.count}
                    for c in by_country
                ],
                "heatmap": heatmap_data,
                "legend": get_heatmap_legend()
            },
            source="database"
        )
    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        return APIResponse.error(
            code=ErrorCodes.DATABASE_ERROR,
            message="통계 데이터를 가져오는 중 오류가 발생했습니다",
            status_code=500,
            details={"error": str(e)}
        )


@router.get("/critical")
def get_critical_species(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """멸종위기 상태의 종 조회"""
    try:
        species = db.query(Species).filter(
            Species.conservation_status == "멸종위기"
        ).order_by(
            desc(Species.search_count)
        ).limit(limit).all()

        return {
            "success": True,
            "data": [SpeciesResponse.model_validate(s) for s in species]
        }
    except Exception as e:
        logger.error(f"Error fetching critical species: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")


@router.get("/region/{region}")
def get_region_endangered(
    region: str,
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """지역별 멸종위기종 목록 및 요약"""
    try:
        query = db.query(Species).filter(
            Species.region == region,
            Species.conservation_status.in_(ENDANGERED_STATUSES)
        )

        if category:
            query = query.filter(Species.category == category)

        species = query.all()

        # 카테고리별 집계
        by_category = {}
        by_status = {}

        for s in species:
            # 카테고리별
            if s.category not in by_category:
                by_category[s.category] = []
            by_category[s.category].append({
                "id": s.id,
                "name": s.name,
                "conservation_status": s.conservation_status
            })

            # 보전상태별
            if s.conservation_status not in by_status:
                by_status[s.conservation_status] = 0
            by_status[s.conservation_status] += 1

        return {
            "success": True,
            "data": {
                "region": region,
                "total_endangered": len(species),
                "by_category": by_category,
                "by_conservation_status": by_status
            }
        }
    except Exception as e:
        logger.error(f"Error fetching region endangered: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")
