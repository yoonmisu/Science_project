"""
지도 인터랙션 및 공간 쿼리 API
PostGIS 기반 공간 검색 및 지오코딩 서비스
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_AsGeoJSON
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.species import Species
from app.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/map",
    tags=["Map"],
    responses={404: {"description": "Not found"}}
)


# Pydantic 스키마
class BoundingBox(BaseModel):
    north: float = Field(..., description="북쪽 경계 (위도)")
    south: float = Field(..., description="남쪽 경계 (위도)")
    east: float = Field(..., description="동쪽 경계 (경도)")
    west: float = Field(..., description="서쪽 경계 (경도)")


class CoordinatePoint(BaseModel):
    lat: float
    lon: float


class SpeciesMapFeature(BaseModel):
    id: int
    name: str
    scientific_name: Optional[str]
    category: str
    latitude: float
    longitude: float


class HotspotFeature(BaseModel):
    latitude: float
    longitude: float
    species_count: int
    density: float


class GeocodeResult(BaseModel):
    lat: float
    lon: float
    display_name: str
    type: str
    importance: float


# 지오코딩 엔드포인트
@router.get(
    "/geocode/forward",
    summary="지명 → 좌표 변환",
    description="지명을 입력하여 위도/경도 좌표를 검색합니다.",
    response_model=GeocodeResult
)
async def forward_geocode(
    place: str = Query(..., description="검색할 지명"),
    country: Optional[str] = Query(None, description="국가 코드 (ISO 3166-1 alpha-2)")
):
    """지명으로 좌표 검색"""
    from app.services.geocoding_service import geocoding_service

    result = await geocoding_service.get_coordinates(place, country)

    if not result:
        raise HTTPException(status_code=404, detail=f"'{place}'에 대한 결과를 찾을 수 없습니다")

    return GeocodeResult(
        lat=result["lat"],
        lon=result["lon"],
        display_name=result["display_name"],
        type=result["type"],
        importance=result["importance"]
    )


@router.get(
    "/geocode/reverse",
    summary="좌표 → 지명 변환",
    description="위도/경도 좌표로 지명을 검색합니다."
)
async def reverse_geocode(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    zoom: int = Query(18, ge=3, le=18, description="상세 수준 (3=국가, 10=도시, 18=건물)")
):
    """좌표로 지명 검색"""
    from app.services.geocoding_service import geocoding_service

    result = await geocoding_service.reverse_geocode(lat, lon, zoom)

    if not result:
        raise HTTPException(status_code=404, detail="해당 좌표에 대한 지명을 찾을 수 없습니다")

    return {
        "success": True,
        "data": result
    }


@router.get(
    "/geocode/search",
    summary="장소 검색",
    description="자동완성을 위한 장소 검색"
)
async def search_places(
    query: str = Query(..., min_length=2, description="검색어"),
    limit: int = Query(5, ge=1, le=10),
    country: Optional[str] = Query(None, description="국가 코드 필터")
):
    """장소 검색 (자동완성용)"""
    from app.services.geocoding_service import geocoding_service

    results = await geocoding_service.search_places(query, limit, country)

    return {
        "success": True,
        "data": results,
        "count": len(results)
    }


@router.get(
    "/geocode/country/{country_code}/bounds",
    summary="국가 경계 조회",
    description="국가의 경계 박스(bounding box)를 조회합니다."
)
async def get_country_bounds(country_code: str):
    """국가 경계 박스 조회"""
    from app.services.geocoding_service import geocoding_service

    bounds = await geocoding_service.get_country_bounds(country_code)

    if not bounds:
        raise HTTPException(status_code=404, detail=f"국가 코드 '{country_code}'를 찾을 수 없습니다")

    return {
        "success": True,
        "data": bounds
    }


# 공간 쿼리 엔드포인트
@router.get(
    "/species/bounds",
    summary="영역 내 생물종 조회",
    description="지정된 경계 박스(bounding box) 내의 모든 생물종을 GeoJSON 형식으로 반환합니다."
)
async def get_species_in_bounds(
    north: float = Query(..., description="북쪽 경계 (위도)"),
    south: float = Query(..., description="남쪽 경계 (위도)"),
    east: float = Query(..., description="동쪽 경계 (경도)"),
    west: float = Query(..., description="서쪽 경계 (경도)"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """지도 영역 내의 모든 생물종 반환 (GeoJSON)"""
    try:
        # 캐시 키 생성
        cache_key = f"map:bounds:{north}:{south}:{east}:{west}:{category or 'all'}:{limit}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # PostGIS를 사용한 공간 쿼리
        query = db.query(Species).filter(
            Species.latitude.isnot(None),
            Species.longitude.isnot(None),
            Species.latitude >= south,
            Species.latitude <= north,
            Species.longitude >= west,
            Species.longitude <= east
        )

        if category:
            query = query.filter(Species.category == category)

        species_list = query.limit(limit).all()

        # GeoJSON FeatureCollection 생성
        features = []
        for species in species_list:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [species.longitude, species.latitude]
                },
                "properties": {
                    "id": species.id,
                    "name": species.name,
                    "scientific_name": species.scientific_name,
                    "category": species.category,
                    "conservation_status": species.conservation_status,
                    "country": species.country,
                    "region": species.region
                }
            }
            features.append(feature)

        result = {
            "success": True,
            "type": "FeatureCollection",
            "features": features,
            "count": len(features),
            "bounds": {
                "north": north,
                "south": south,
                "east": east,
                "west": west
            }
        }

        # 5분 캐싱
        cache_set(cache_key, result, 300)

        return result

    except Exception as e:
        logger.error(f"Error fetching species in bounds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/biodiversity/hotspots",
    summary="생물 다양성 핫스팟",
    description="생물 다양성이 높은 지역(핫스팟)을 클러스터링하여 반환합니다."
)
async def get_biodiversity_hotspots(
    grid_size: float = Query(1.0, description="그리드 크기 (도 단위)"),
    min_species: int = Query(5, ge=1, description="최소 종 수"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    country: Optional[str] = Query(None, description="국가 필터"),
    db: Session = Depends(get_db)
):
    """생물 다양성 핫스팟 (클러스터링)"""
    try:
        # 캐시 키 생성
        cache_key = f"map:hotspots:{grid_size}:{min_species}:{category or 'all'}:{country or 'all'}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # 그리드 기반 클러스터링 쿼리
        # 위도/경도를 그리드 크기로 반올림하여 클러스터 생성
        grid_lat = func.floor(Species.latitude / grid_size) * grid_size + (grid_size / 2)
        grid_lon = func.floor(Species.longitude / grid_size) * grid_size + (grid_size / 2)

        query = db.query(
            grid_lat.label('center_lat'),
            grid_lon.label('center_lon'),
            func.count(Species.id).label('species_count'),
            func.count(func.distinct(Species.category)).label('category_count')
        ).filter(
            Species.latitude.isnot(None),
            Species.longitude.isnot(None)
        )

        if category:
            query = query.filter(Species.category == category)

        if country:
            query = query.filter(Species.country == country)

        query = query.group_by(grid_lat, grid_lon).having(
            func.count(Species.id) >= min_species
        ).order_by(func.count(Species.id).desc())

        hotspots = query.all()

        # 전체 종 수 계산 (밀도 계산용)
        total_species = db.query(func.count(Species.id)).filter(
            Species.latitude.isnot(None)
        ).scalar() or 1

        # GeoJSON 생성
        features = []
        for hotspot in hotspots:
            density = hotspot.species_count / total_species
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [hotspot.center_lon, hotspot.center_lat]
                },
                "properties": {
                    "species_count": hotspot.species_count,
                    "category_count": hotspot.category_count,
                    "density": round(density * 100, 2),
                    "grid_size": grid_size
                }
            }
            features.append(feature)

        result = {
            "success": True,
            "type": "FeatureCollection",
            "features": features,
            "count": len(features),
            "total_species": total_species,
            "grid_size": grid_size
        }

        # 10분 캐싱
        cache_set(cache_key, result, 600)

        return result

    except Exception as e:
        logger.error(f"Error fetching hotspots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/species/{species_id}/distribution",
    summary="종 분포 데이터",
    description="특정 종의 분포 지도 데이터를 반환합니다. 같은 종의 다른 관측 기록을 포함합니다."
)
async def get_species_distribution(
    species_id: int,
    db: Session = Depends(get_db)
):
    """특정 종의 분포 지도 데이터"""
    try:
        # 종 정보 조회
        species = db.query(Species).filter(Species.id == species_id).first()

        if not species:
            raise HTTPException(status_code=404, detail="종을 찾을 수 없습니다")

        # 같은 학명을 가진 모든 기록 조회 (분포 데이터)
        if species.scientific_name:
            distribution_query = db.query(Species).filter(
                Species.scientific_name == species.scientific_name,
                Species.latitude.isnot(None),
                Species.longitude.isnot(None)
            )
        else:
            # 학명이 없으면 같은 이름의 기록 조회
            distribution_query = db.query(Species).filter(
                Species.name == species.name,
                Species.latitude.isnot(None),
                Species.longitude.isnot(None)
            )

        distribution_records = distribution_query.all()

        # 좌표 배열 생성 (히트맵용)
        coordinates = []
        countries = set()

        for record in distribution_records:
            coordinates.append({
                "lat": record.latitude,
                "lon": record.longitude,
                "country": record.country,
                "region": record.region
            })
            countries.add(record.country)

        # GeoJSON 생성
        features = []
        for record in distribution_records:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [record.longitude, record.latitude]
                },
                "properties": {
                    "id": record.id,
                    "country": record.country,
                    "region": record.region
                }
            }
            features.append(feature)

        return {
            "success": True,
            "species": {
                "id": species.id,
                "name": species.name,
                "scientific_name": species.scientific_name,
                "category": species.category,
                "conservation_status": species.conservation_status
            },
            "distribution": {
                "type": "FeatureCollection",
                "features": features
            },
            "coordinates": coordinates,  # 히트맵용
            "summary": {
                "total_records": len(distribution_records),
                "countries": list(countries),
                "country_count": len(countries)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching species distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/species/nearby",
    summary="주변 생물종 조회",
    description="특정 좌표 주변의 생물종을 PostGIS ST_DWithin으로 검색합니다."
)
async def get_nearby_species(
    lat: float = Query(..., description="위도"),
    lon: float = Query(..., description="경도"),
    radius: float = Query(10.0, description="반경 (km)"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """주변 생물종 조회 (PostGIS)"""
    try:
        # 캐시 키 생성
        cache_key = f"map:nearby:{lat}:{lon}:{radius}:{category or 'all'}:{limit}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # PostGIS ST_DWithin을 사용한 반경 검색
        # 반경을 미터로 변환 (km * 1000)
        radius_meters = radius * 1000

        # 기준점 생성
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

        # location 컬럼이 있는 경우 PostGIS 함수 사용
        query = db.query(
            Species,
            func.ST_Distance(
                Species.location,
                func.ST_GeogFromText(f'POINT({lon} {lat})')
            ).label('distance')
        ).filter(
            Species.location.isnot(None),
            func.ST_DWithin(
                Species.location,
                func.ST_GeogFromText(f'POINT({lon} {lat})'),
                radius_meters
            )
        )

        if category:
            query = query.filter(Species.category == category)

        # 거리순 정렬
        results = query.order_by('distance').limit(limit).all()

        # GeoJSON 생성
        features = []
        for species, distance in results:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [species.longitude, species.latitude]
                },
                "properties": {
                    "id": species.id,
                    "name": species.name,
                    "scientific_name": species.scientific_name,
                    "category": species.category,
                    "conservation_status": species.conservation_status,
                    "country": species.country,
                    "distance_m": round(distance, 2) if distance else None
                }
            }
            features.append(feature)

        result = {
            "success": True,
            "type": "FeatureCollection",
            "features": features,
            "count": len(features),
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius
        }

        # 5분 캐싱
        cache_set(cache_key, result, 300)

        return result

    except Exception as e:
        logger.error(f"Error fetching nearby species: {str(e)}")
        # PostGIS가 설치되지 않은 경우 fallback
        if "ST_DWithin" in str(e) or "geography" in str(e):
            return await _get_nearby_species_fallback(db, lat, lon, radius, category, limit)
        raise HTTPException(status_code=500, detail=str(e))


async def _get_nearby_species_fallback(
    db: Session,
    lat: float,
    lon: float,
    radius: float,
    category: Optional[str],
    limit: int
):
    """PostGIS가 없는 경우 Haversine 공식 사용"""
    # Haversine 근사치 (정확도 낮음)
    # 1도 ≈ 111km
    lat_range = radius / 111
    lon_range = radius / (111 * abs(func.cos(func.radians(lat))))

    query = db.query(Species).filter(
        Species.latitude.isnot(None),
        Species.longitude.isnot(None),
        Species.latitude.between(lat - lat_range, lat + lat_range),
        Species.longitude.between(lon - lon_range, lon + lon_range)
    )

    if category:
        query = query.filter(Species.category == category)

    species_list = query.limit(limit).all()

    features = []
    for species in species_list:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [species.longitude, species.latitude]
            },
            "properties": {
                "id": species.id,
                "name": species.name,
                "scientific_name": species.scientific_name,
                "category": species.category,
                "conservation_status": species.conservation_status,
                "country": species.country
            }
        }
        features.append(feature)

    return {
        "success": True,
        "type": "FeatureCollection",
        "features": features,
        "count": len(features),
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius,
        "note": "Approximate results (PostGIS not available)"
    }


@router.get(
    "/clusters",
    summary="종 클러스터 조회",
    description="지도 줌 레벨에 따른 종 클러스터를 반환합니다."
)
async def get_species_clusters(
    north: float = Query(...),
    south: float = Query(...),
    east: float = Query(...),
    west: float = Query(...),
    zoom: int = Query(5, ge=1, le=18, description="줌 레벨"),
    db: Session = Depends(get_db)
):
    """줌 레벨에 따른 클러스터링"""
    try:
        # 줌 레벨에 따른 그리드 크기 계산
        # 높은 줌 = 작은 그리드 = 더 세밀한 클러스터
        grid_size = 180 / (2 ** zoom)

        grid_lat = func.floor(Species.latitude / grid_size) * grid_size + (grid_size / 2)
        grid_lon = func.floor(Species.longitude / grid_size) * grid_size + (grid_size / 2)

        clusters = db.query(
            grid_lat.label('lat'),
            grid_lon.label('lon'),
            func.count(Species.id).label('count')
        ).filter(
            Species.latitude.isnot(None),
            Species.longitude.isnot(None),
            Species.latitude.between(south, north),
            Species.longitude.between(west, east)
        ).group_by(
            grid_lat, grid_lon
        ).all()

        features = []
        for cluster in clusters:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [cluster.lon, cluster.lat]
                },
                "properties": {
                    "count": cluster.count,
                    "cluster": True
                }
            }
            features.append(feature)

        return {
            "success": True,
            "type": "FeatureCollection",
            "features": features,
            "cluster_count": len(features),
            "zoom": zoom,
            "grid_size": grid_size
        }

    except Exception as e:
        logger.error(f"Error fetching clusters: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
