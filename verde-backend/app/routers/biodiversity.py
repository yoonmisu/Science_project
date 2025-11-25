"""
생물 다양성 API 라우터
GBIF, iNaturalist, IUCN API 통합 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.services.gbif_service import gbif_service
from app.services.inaturalist_service import inaturalist_service
from app.services.iucn_service import iucn_service
from app.services.data_collector import data_collector
from app.api.response import APIResponse, ErrorCodes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/biodiversity", tags=["Biodiversity"])


# =========================================================================
# GBIF API 엔드포인트
# =========================================================================
@router.get(
    "/gbif/species/{country_code}",
    summary="국가별 생물종 조회",
    description="GBIF API에서 특정 국가의 생물종 데이터를 가져옵니다."
)
async def get_gbif_species_by_country(
    country_code: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """국가별 생물종 조회 (GBIF)"""
    try:
        species = await gbif_service.fetch_species_by_region(
            country_code.upper(), limit, offset
        )

        return {
            "success": True,
            "data": species,
            "total": len(species),
            "country_code": country_code.upper()
        }

    except Exception as e:
        logger.error(f"GBIF species fetch error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="GBIF 데이터 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/gbif/coordinates",
    summary="좌표 기반 생물종 검색",
    description="위도/경도를 기준으로 주변 생물종을 검색합니다."
)
async def get_gbif_species_by_coordinates(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    radius_km: int = Query(50, ge=1, le=500, description="검색 반경 (km)"),
    limit: int = Query(100, ge=1, le=500)
):
    """좌표 기반 생물종 검색 (GBIF)"""
    try:
        species = await gbif_service.fetch_species_by_coordinates(
            lat, lon, radius_km, limit
        )

        return {
            "success": True,
            "data": species,
            "total": len(species),
            "coordinates": {"lat": lat, "lon": lon},
            "radius_km": radius_km
        }

    except Exception as e:
        logger.error(f"GBIF coordinate search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="좌표 기반 검색 중 오류가 발생했습니다"
        )


@router.get(
    "/gbif/statistics/{country_code}",
    summary="국가별 생물 다양성 통계",
    description="GBIF에서 국가별 생물 다양성 통계를 가져옵니다."
)
async def get_gbif_statistics(country_code: str):
    """국가별 생물 다양성 통계 (GBIF)"""
    try:
        stats = await gbif_service.get_biodiversity_statistics(country_code.upper())

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"GBIF statistics error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="통계 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/gbif/search",
    summary="생물명 검색",
    description="GBIF에서 생물명으로 검색합니다. Fuzzy matching을 지원합니다."
)
async def search_gbif_species(
    name: str = Query(..., min_length=1, description="검색어"),
    fuzzy: bool = Query(True, description="Fuzzy matching 사용"),
    limit: int = Query(20, ge=1, le=100)
):
    """생물명 검색 (GBIF)"""
    try:
        results = await gbif_service.search_species_by_name(name, fuzzy, limit)

        return {
            "success": True,
            "data": results,
            "total": len(results),
            "query": name
        }

    except Exception as e:
        logger.error(f"GBIF search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="검색 중 오류가 발생했습니다"
        )


# =========================================================================
# iNaturalist API 엔드포인트
# =========================================================================
@router.get(
    "/inaturalist/observations/{country_code}",
    summary="국가별 관찰 기록",
    description="iNaturalist에서 특정 국가의 사진이 있는 관찰 기록을 가져옵니다."
)
async def get_inaturalist_observations(
    country_code: str,
    limit: int = Query(100, ge=1, le=200),
    page: int = Query(1, ge=1)
):
    """국가별 관찰 기록 (iNaturalist)"""
    try:
        place_id = inaturalist_service.get_place_id(country_code.upper())
        if not place_id:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 국가 코드: {country_code}"
            )

        observations = await inaturalist_service.fetch_observations_with_photos(
            place_id, limit=limit, page=page
        )

        return {
            "success": True,
            "data": observations,
            "total": len(observations),
            "country_code": country_code.upper(),
            "page": page
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iNaturalist observations error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="관찰 기록 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/inaturalist/popular/{country_code}",
    summary="인기 생물종",
    description="iNaturalist에서 지역별 인기 생물종을 가져옵니다."
)
async def get_inaturalist_popular_species(
    country_code: str,
    limit: int = Query(50, ge=1, le=200),
    iconic_taxa: str = Query(None, description="분류군 필터 (Plantae, Animalia, Insecta 등)")
):
    """인기 생물종 (iNaturalist)"""
    try:
        place_id = inaturalist_service.get_place_id(country_code.upper())
        if not place_id:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 국가 코드: {country_code}"
            )

        species = await inaturalist_service.get_popular_species(
            place_id, limit, iconic_taxa
        )

        return {
            "success": True,
            "data": species,
            "total": len(species),
            "country_code": country_code.upper()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iNaturalist popular species error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="인기 종 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/inaturalist/search",
    summary="이름으로 검색",
    description="iNaturalist에서 한글/영문 이름으로 검색합니다."
)
async def search_inaturalist_species(
    name: str = Query(..., min_length=1, description="검색어"),
    locale: str = Query("ko", description="언어 코드 (ko, en, ja)"),
    limit: int = Query(20, ge=1, le=100)
):
    """이름으로 검색 (iNaturalist)"""
    try:
        results = await inaturalist_service.search_by_common_name(name, locale, limit)

        return {
            "success": True,
            "data": results,
            "total": len(results),
            "query": name
        }

    except Exception as e:
        logger.error(f"iNaturalist search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="검색 중 오류가 발생했습니다"
        )


@router.get(
    "/inaturalist/statistics/{country_code}",
    summary="지역 통계",
    description="iNaturalist에서 지역별 생물 다양성 통계를 가져옵니다."
)
async def get_inaturalist_statistics(country_code: str):
    """지역 통계 (iNaturalist)"""
    try:
        place_id = inaturalist_service.get_place_id(country_code.upper())
        if not place_id:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 국가 코드: {country_code}"
            )

        stats = await inaturalist_service.get_place_statistics(place_id)

        return {
            "success": True,
            "data": stats,
            "country_code": country_code.upper()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"iNaturalist statistics error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="통계 조회 중 오류가 발생했습니다"
        )


# =========================================================================
# IUCN Red List API 엔드포인트
# =========================================================================
@router.get(
    "/iucn/endangered",
    summary="멸종위기종 목록",
    description="IUCN Red List에서 멸종위기종 목록을 가져옵니다."
)
async def get_iucn_endangered_species(
    category: str = Query(None, description="IUCN 카테고리 (CR, EN, VU)")
):
    """멸종위기종 목록 (IUCN)"""
    try:
        species = await iucn_service.fetch_endangered_species(category)

        return {
            "success": True,
            "data": species,
            "total": len(species),
            "category": category
        }

    except Exception as e:
        logger.error(f"IUCN endangered species error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="멸종위기종 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/iucn/species/{scientific_name}",
    summary="종 보전 상태",
    description="특정 종의 상세 보전 정보를 가져옵니다."
)
async def get_iucn_species_status(scientific_name: str):
    """종 보전 상태 (IUCN)"""
    try:
        status = await iucn_service.get_species_conservation_status(scientific_name)

        if not status:
            raise HTTPException(
                status_code=404,
                detail="종을 찾을 수 없습니다"
            )

        return {
            "success": True,
            "data": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IUCN species status error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="보전 상태 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/iucn/assessment/{country_code}",
    summary="국가별 평가",
    description="국가별 멸종위기종 평가 통계를 가져옵니다."
)
async def get_iucn_regional_assessment(country_code: str):
    """국가별 평가 (IUCN)"""
    try:
        assessment = await iucn_service.get_regional_assessment(country_code.upper())

        return {
            "success": True,
            "data": assessment
        }

    except Exception as e:
        logger.error(f"IUCN regional assessment error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="국가별 평가 조회 중 오류가 발생했습니다"
        )


# =========================================================================
# 데이터 수집 엔드포인트 (관리자용)
# =========================================================================
@router.post(
    "/collect/country/{country_code}",
    summary="국가별 데이터 수집",
    description="특정 국가의 생물종 데이터를 수집하여 DB에 저장합니다. 관리자 권한이 필요합니다."
)
async def collect_country_data(
    country_code: str,
    limit: int = Query(500, ge=1, le=2000),
    current_user: User = Depends(get_current_admin_user)
):
    """국가별 데이터 수집 (관리자)"""
    try:
        # 국가 정보 찾기
        country_info = None
        for c in [
            {"code": "KR", "name": "Korea", "region": "아시아"},
            {"code": "US", "name": "USA", "region": "북미"},
            {"code": "CN", "name": "China", "region": "아시아"},
            {"code": "JP", "name": "Japan", "region": "아시아"},
            {"code": "GB", "name": "United Kingdom", "region": "유럽"},
            {"code": "AU", "name": "Australia", "region": "오세아니아"}
        ]:
            if c["code"] == country_code.upper():
                country_info = c
                break

        if not country_info:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 국가 코드: {country_code}"
            )

        result = await data_collector.collect_species_by_country(
            country_info["code"],
            country_info["name"],
            country_info["region"],
            limit
        )

        logger.info(f"Data collection by {current_user.username} for {country_code}")

        return {
            "success": True,
            "data": result,
            "message": f"{country_info['name']} 데이터 수집이 완료되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data collection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="데이터 수집 중 오류가 발생했습니다"
        )


@router.post(
    "/collect/all",
    summary="전체 데이터 수집",
    description="모든 대상 국가의 데이터를 수집합니다. 관리자 권한이 필요합니다."
)
async def collect_all_data(
    limit_per_country: int = Query(500, ge=1, le=2000),
    current_user: User = Depends(get_current_admin_user)
):
    """전체 데이터 수집 (관리자)"""
    try:
        result = await data_collector.collect_all_countries(limit_per_country)

        logger.info(f"Full data collection by {current_user.username}")

        return {
            "success": True,
            "data": result,
            "message": "전체 데이터 수집이 완료되었습니다"
        }

    except Exception as e:
        logger.error(f"Full data collection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="데이터 수집 중 오류가 발생했습니다"
        )


@router.post(
    "/update/endangered",
    summary="멸종위기종 업데이트",
    description="멸종위기종 보전 상태를 업데이트합니다. 관리자 권한이 필요합니다."
)
async def update_endangered_status(
    country_code: str = Query(None, description="특정 국가만 업데이트"),
    current_user: User = Depends(get_current_admin_user)
):
    """멸종위기종 업데이트 (관리자)"""
    try:
        result = await data_collector.update_endangered_species(country_code)

        logger.info(f"Endangered update by {current_user.username}")

        return {
            "success": True,
            "data": result,
            "message": "멸종위기종 업데이트가 완료되었습니다"
        }

    except Exception as e:
        logger.error(f"Endangered update error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="멸종위기종 업데이트 중 오류가 발생했습니다"
        )


@router.post(
    "/update/statistics",
    summary="통계 업데이트",
    description="지역별 생물 다양성 통계를 재계산합니다. 관리자 권한이 필요합니다."
)
async def update_statistics(
    current_user: User = Depends(get_current_admin_user)
):
    """통계 업데이트 (관리자)"""
    try:
        result = await data_collector.update_region_statistics()

        logger.info(f"Statistics update by {current_user.username}")

        return {
            "success": True,
            "data": result,
            "message": "통계 업데이트가 완료되었습니다"
        }

    except Exception as e:
        logger.error(f"Statistics update error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="통계 업데이트 중 오류가 발생했습니다"
        )
