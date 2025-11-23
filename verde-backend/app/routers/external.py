"""
실시간 외부 데이터 API 라우터
GBIF, iNaturalist, IUCN API에서 실시간 데이터를 가져와 제공
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.models.species import Species
from app.models.region_biodiversity import RegionBiodiversity
from app.services.gbif_service import gbif_service
from app.services.inaturalist_service import inaturalist_service
from app.services.iucn_service import iucn_service
from app.services.data_collector import data_collector
from app.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external", tags=["External Data"])


# =========================================================================
# 1. 실시간 국가별 생물종
# =========================================================================
@router.get(
    "/species/region/{country_code}",
    summary="실시간 국가별 생물종",
    description="GBIF에서 실시간으로 해당 국가의 생물종 데이터를 가져옵니다. 1시간 캐싱됩니다.",
    responses={
        200: {
            "description": "성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "species": [
                                {
                                    "name": "호랑이",
                                    "scientific_name": "Panthera tigris",
                                    "category": "동물",
                                    "country": "Korea"
                                }
                            ],
                            "total": 100,
                            "country_code": "KR",
                            "cached": False
                        }
                    }
                }
            }
        }
    }
)
async def get_realtime_species_by_region(
    country_code: str,
    limit: int = Query(100, ge=1, le=500, description="결과 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    category: Optional[str] = Query(None, description="카테고리 필터 (식물, 동물, 곤충, 해양생물)")
):
    """실시간 국가별 생물종 조회 (1시간 캐싱)"""
    try:
        # 캐시 키 생성
        cache_key = f"external:species:region:{country_code}:{limit}:{offset}:{category or 'all'}"

        # 캐시 확인
        cached = cache_get(cache_key)
        if cached:
            cached["data"]["cached"] = True
            logger.info(f"Cache hit for {country_code}")
            return cached

        # GBIF에서 실시간 데이터 조회
        species_list = await gbif_service.fetch_species_by_region(
            country_code.upper(), limit, offset
        )

        # 카테고리 필터링
        if category:
            species_list = [s for s in species_list if s.get("category") == category]

        result = {
            "success": True,
            "data": {
                "species": species_list,
                "total": len(species_list),
                "country_code": country_code.upper(),
                "limit": limit,
                "offset": offset,
                "cached": False
            }
        }

        # 1시간 캐싱
        cache_set(cache_key, result, 3600)
        logger.info(f"Fetched {len(species_list)} species for {country_code}")

        return result

    except Exception as e:
        logger.error(f"External species fetch error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="실시간 데이터 조회 중 오류가 발생했습니다"
        )


# =========================================================================
# 2. 위치 기반 주변 생물종 (통합)
# =========================================================================
@router.get(
    "/species/nearby",
    summary="주변 생물종 검색",
    description="위도/경도를 기준으로 주변 생물종을 검색합니다. iNaturalist와 GBIF 데이터를 통합합니다.",
    responses={
        200: {
            "description": "성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "species": [],
                            "total": 50,
                            "sources": {
                                "gbif": 30,
                                "inaturalist": 20
                            },
                            "coordinates": {"lat": 37.5665, "lon": 126.9780},
                            "radius_km": 50
                        }
                    }
                }
            }
        }
    }
)
async def get_nearby_species(
    lat: float = Query(..., ge=-90, le=90, description="위도"),
    lon: float = Query(..., ge=-180, le=180, description="경도"),
    radius: int = Query(50, ge=1, le=500, description="검색 반경 (km)"),
    limit: int = Query(100, ge=1, le=500, description="결과 수")
):
    """위치 기반 주변 생물종 통합 검색"""
    try:
        # 캐시 키
        cache_key = f"external:species:nearby:{lat:.4f}:{lon:.4f}:{radius}:{limit}"

        # 캐시 확인
        cached = cache_get(cache_key)
        if cached:
            cached["data"]["cached"] = True
            return cached

        # GBIF에서 검색
        gbif_species = await gbif_service.fetch_species_by_coordinates(
            lat, lon, radius, limit // 2
        )

        # iNaturalist에서 검색
        inat_observations = await inaturalist_service.fetch_observations_by_coordinates(
            lat, lon, radius, limit // 2
        )

        # iNaturalist 관찰 데이터를 종 데이터로 변환
        inat_species = []
        seen_names = set()
        for obs in inat_observations:
            taxon = obs.get("taxon", {})
            name = taxon.get("scientific_name")
            if name and name not in seen_names:
                seen_names.add(name)
                inat_species.append({
                    "name": taxon.get("name"),
                    "scientific_name": name,
                    "category": _map_iconic_taxa_to_category(taxon.get("iconic_taxon")),
                    "latitude": obs.get("latitude"),
                    "longitude": obs.get("longitude"),
                    "photos": obs.get("photos", []),
                    "source": "inaturalist",
                    "observation_id": obs.get("observation_id")
                })

        # GBIF 데이터에 source 추가
        for sp in gbif_species:
            sp["source"] = "gbif"

        # 통합 (중복 제거)
        combined = []
        seen = set()

        for sp in gbif_species + inat_species:
            key = sp.get("scientific_name") or sp.get("name")
            if key and key not in seen:
                seen.add(key)
                combined.append(sp)

        result = {
            "success": True,
            "data": {
                "species": combined[:limit],
                "total": len(combined),
                "sources": {
                    "gbif": len(gbif_species),
                    "inaturalist": len(inat_species)
                },
                "coordinates": {"lat": lat, "lon": lon},
                "radius_km": radius,
                "cached": False
            }
        }

        # 30분 캐싱
        cache_set(cache_key, result, 1800)
        logger.info(f"Nearby search at ({lat}, {lon}): {len(combined)} species")

        return result

    except Exception as e:
        logger.error(f"Nearby species search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="주변 생물종 검색 중 오류가 발생했습니다"
        )


# =========================================================================
# 3. 전 세계 멸종위기종
# =========================================================================
@router.get(
    "/endangered/global",
    summary="전 세계 멸종위기종",
    description="IUCN Red List에서 전 세계 멸종위기종 실시간 데이터를 가져옵니다.",
    responses={
        200: {
            "description": "성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "species": [],
                            "total": 100,
                            "by_category": {
                                "CR": 30,
                                "EN": 40,
                                "VU": 30
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_global_endangered_species(
    category: Optional[str] = Query(
        None,
        description="IUCN 카테고리 (CR: 위급, EN: 위기, VU: 취약)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="결과 수")
):
    """전 세계 멸종위기종 실시간 조회"""
    try:
        # 캐시 키
        cache_key = f"external:endangered:global:{category or 'all'}:{limit}"

        # 캐시 확인 (2시간)
        cached = cache_get(cache_key)
        if cached:
            cached["data"]["cached"] = True
            return cached

        # IUCN에서 데이터 조회
        if category:
            species_list = await iucn_service.fetch_endangered_species(category.upper())
        else:
            # 모든 멸종위기종 (CR, EN, VU)
            species_list = await iucn_service.fetch_endangered_species()

        # 제한 적용
        species_list = species_list[:limit]

        # 카테고리별 통계
        category_counts = {}
        for sp in species_list:
            cat = sp.get("category_code", "NE")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        result = {
            "success": True,
            "data": {
                "species": species_list,
                "total": len(species_list),
                "by_category": category_counts,
                "category_filter": category,
                "cached": False
            }
        }

        # 2시간 캐싱
        cache_set(cache_key, result, 7200)
        logger.info(f"Global endangered species: {len(species_list)}")

        return result

    except Exception as e:
        logger.error(f"Global endangered fetch error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="멸종위기종 데이터 조회 중 오류가 발생했습니다"
        )


# =========================================================================
# 4. 데이터 동기화 (관리자용)
# =========================================================================
class SyncRequest(BaseModel):
    country_codes: List[str] = ["KR"]
    categories: Optional[List[str]] = None
    limit: int = 1000

    class Config:
        json_schema_extra = {
            "example": {
                "country_codes": ["KR", "US", "JP"],
                "categories": ["동물", "식물"],
                "limit": 1000
            }
        }


@router.post(
    "/sync/species",
    summary="외부 데이터 동기화",
    description="외부 API 데이터를 로컬 DB로 동기화합니다. 관리자 권한이 필요합니다."
)
async def sync_species_data(
    request: SyncRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """외부 데이터를 로컬 DB로 동기화 (관리자)"""
    try:
        results = []
        total_imported = 0
        total_updated = 0
        total_skipped = 0

        # 국가 정보 매핑
        country_map = {
            "KR": ("Korea", "아시아"),
            "US": ("USA", "북미"),
            "CN": ("China", "아시아"),
            "JP": ("Japan", "아시아"),
            "GB": ("United Kingdom", "유럽"),
            "DE": ("Germany", "유럽"),
            "FR": ("France", "유럽"),
            "AU": ("Australia", "오세아니아"),
            "BR": ("Brazil", "남미"),
            "IN": ("India", "아시아")
        }

        for code in request.country_codes:
            code = code.upper()
            if code not in country_map:
                results.append({
                    "country_code": code,
                    "error": "지원하지 않는 국가 코드"
                })
                continue

            country_name, region = country_map[code]

            try:
                result = await data_collector.collect_species_by_country(
                    code, country_name, region, request.limit
                )

                total_imported += result.get("imported", 0)
                total_updated += result.get("updated", 0)
                total_skipped += result.get("skipped", 0)

                results.append({
                    "country_code": code,
                    "country_name": country_name,
                    "imported": result.get("imported", 0),
                    "updated": result.get("updated", 0),
                    "skipped": result.get("skipped", 0)
                })

            except Exception as e:
                results.append({
                    "country_code": code,
                    "error": str(e)
                })

        logger.info(f"Sync completed by {current_user.username}: {total_imported} imported, {total_updated} updated")

        return {
            "success": True,
            "data": {
                "results": results,
                "summary": {
                    "total_imported": total_imported,
                    "total_updated": total_updated,
                    "total_skipped": total_skipped,
                    "countries_processed": len(request.country_codes)
                }
            },
            "message": f"{total_imported}개 종이 임포트되었습니다"
        }

    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="데이터 동기화 중 오류가 발생했습니다"
        )


# =========================================================================
# 5. 생물 다양성 히트맵
# =========================================================================
@router.get(
    "/map/heatmap",
    summary="생물 다양성 히트맵",
    description="지역별 종 밀도를 GeoJSON 형식으로 반환합니다."
)
async def get_biodiversity_heatmap(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="카테고리 필터")
):
    """생물 다양성 히트맵 데이터 (GeoJSON)"""
    try:
        # 캐시 키
        cache_key = f"external:map:heatmap:{category or 'all'}"

        # 캐시 확인 (10분)
        cached = cache_get(cache_key)
        if cached:
            return cached

        # 지역별 데이터 조회
        regions = db.query(RegionBiodiversity).all()

        # GeoJSON Feature Collection 생성
        features = []

        for region in regions:
            # 카테고리별 필터링
            if category:
                if category == "식물":
                    count = region.plant_count
                elif category == "동물":
                    count = region.animal_count
                elif category == "곤충":
                    count = region.insect_count
                elif category == "해양생물":
                    count = region.marine_count
                else:
                    count = region.total_species_count
            else:
                count = region.total_species_count

            # 좌표가 있는 경우만 추가
            if region.latitude and region.longitude:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [region.longitude, region.latitude]
                    },
                    "properties": {
                        "region_name": region.region_name,
                        "country": region.country,
                        "species_count": count,
                        "endangered_count": region.endangered_count,
                        "density": _calculate_density(count),
                        "details": {
                            "total": region.total_species_count,
                            "plants": region.plant_count,
                            "animals": region.animal_count,
                            "insects": region.insect_count,
                            "marine": region.marine_count
                        }
                    }
                }
                features.append(feature)

        # 종 분포 데이터도 추가 (좌표가 있는 종)
        species_query = db.query(
            Species.region,
            Species.country,
            func.count(Species.id).label('count'),
            func.avg(func.cast(Species.characteristics['latitude'].astext, db.bind.dialect.name == 'postgresql' and 'FLOAT' or None)).label('avg_lat'),
            func.avg(func.cast(Species.characteristics['longitude'].astext, db.bind.dialect.name == 'postgresql' and 'FLOAT' or None)).label('avg_lon')
        )

        if category:
            species_query = species_query.filter(Species.category == category)

        species_groups = species_query.group_by(
            Species.region, Species.country
        ).all()

        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_regions": len(features),
                "category_filter": category,
                "generated_at": "now"
            }
        }

        # 10분 캐싱
        result = {"success": True, "data": geojson}
        cache_set(cache_key, result, 600)

        return result

    except Exception as e:
        logger.error(f"Heatmap generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="히트맵 데이터 생성 중 오류가 발생했습니다"
        )


# =========================================================================
# 유틸리티 함수
# =========================================================================
def _map_iconic_taxa_to_category(iconic_taxa: str) -> str:
    """iNaturalist iconic_taxa를 카테고리로 매핑"""
    if not iconic_taxa:
        return "기타"

    mapping = {
        "Plantae": "식물",
        "Animalia": "동물",
        "Mammalia": "동물",
        "Aves": "동물",
        "Reptilia": "동물",
        "Amphibia": "동물",
        "Insecta": "곤충",
        "Arachnida": "곤충",
        "Actinopterygii": "해양생물",
        "Mollusca": "해양생물"
    }

    return mapping.get(iconic_taxa, "기타")


def _calculate_density(count: int) -> str:
    """종 수에 따른 밀도 등급 계산"""
    if count >= 1000:
        return "very_high"
    elif count >= 500:
        return "high"
    elif count >= 100:
        return "medium"
    elif count >= 10:
        return "low"
    else:
        return "very_low"
