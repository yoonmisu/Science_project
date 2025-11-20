# cruds/observation_crud.py
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, literal_column
from models.observation_model import Observation
from models.species_model import Species
from schemas.map_search_schema import ObservationCreate, MapSearchRequest
from geoalchemy2.shape import to_shape
from shapely.geometry import Point


async def create_observation(db: AsyncSession, obs_data: ObservationCreate) -> Observation:
    """새 관측 기록을 생성합니다. (위도/경도를 PostGIS Geometry 타입으로 변환)"""

    # 1. 위도/경도를 Shapely Point 객체로 생성
    point = Point(obs_data.longitude, obs_data.latitude)

    # 2. DB 모델 인스턴스 생성
    new_obs = Observation(
        species_id=obs_data.species_id,
        latitude=obs_data.latitude,
        longitude=obs_data.longitude,
        # GeoAlchemy2 Geometry 타입에 Shapely Point 객체를 할당
        location=point
    )

    db.add(new_obs)
    await db.commit()
    await db.refresh(new_obs)

    return new_obs


async def search_species_diversity_by_bbox(db: AsyncSession, search_req: MapSearchRequest) -> List[dict]:
    """
    주어진 경계 상자(Bounding Box) 내에서 관측된 종의 다양성과 횟수를 조회합니다.
    PostGIS의 ST_Within 함수를 사용합니다.
    """

    # PostGIS의 ST_MakeEnvelope 함수를 사용하여 경계 상자(POLYGON)를 생성합니다.
    # WGS84 좌표계 (SRID 4326)를 사용합니다.
    bbox_wkt = f'SRID=4326;POLYGON(( \
        {search_req.min_lon} {search_req.min_lat}, \
        {search_req.min_lon} {search_req.max_lat}, \
        {search_req.max_lon} {search_req.max_lat}, \
        {search_req.max_lon} {search_req.min_lat}, \
        {search_req.min_lon} {search_req.min_lat} \
    ))'

    # ST_Within(A, B): A 지오메트리가 B 지오메트리 안에 완전히 포함되는지 확인
    query = select(
        Observation.species_id,
        func.count(Observation.species_id).label("count"),
        Species.scientific_name,
        Species.common_name
    ).join(
        Species, Observation.species_id == Species.id
    ).where(
        func.ST_Within(
            Observation.location,
            func.ST_GeomFromEWKT(bbox_wkt)  # WKT(Well-Known Text)로부터 Geometry 생성
        )
    ).group_by(
        Observation.species_id, Species.scientific_name, Species.common_name
    ).order_by(
        literal_column("count").desc()
    )

    result = await db.execute(query)
    # SQLAlchemy의 Row 객체를 Dictionary 리스트로 변환
    return [row._asdict() for row in result]