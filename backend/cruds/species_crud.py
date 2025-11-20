# /cruds/species_crud.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_AsText, ST_DWithin, ST_SetSRID, ST_MakePoint

from models.species_model import Species
from schemas import species_schema as schemas


async def get_all_species(session: AsyncSession) -> list[dict]:
    """모든 종 조회 (location을 WKT 문자열로 변환)"""
    result = await session.execute(
        select(
            Species.id,
            Species.name_korean,
            Species.name_scientific,
            ST_AsText(Species.location).label("location"),
            Species.description,
            Species.created_at,
            Species.updated_at
        ).order_by(Species.name_korean)
    )
    return result.mappings().all()


async def create_species(session: AsyncSession, species_data: schemas.SpeciesCreate) -> dict:
    """새로운 종 생성 (lat/lng를 WKT POINT로 변환)"""
    # WKT POINT 생성: POINT(longitude latitude)
    location_wkt = WKTElement(
        f"POINT({species_data.longitude} {species_data.latitude})",
        srid=4326
    )

    db_species = Species(
        name_korean=species_data.name_korean,
        name_scientific=species_data.name_scientific,
        location=location_wkt,
        description=species_data.description
    )

    session.add(db_species)
    await session.commit()
    await session.refresh(db_species)

    # location을 WKT 문자열로 변환하여 반환
    result = await session.execute(
        select(
            Species.id,
            Species.name_korean,
            Species.name_scientific,
            ST_AsText(Species.location).label("location"),
            Species.description,
            Species.created_at,
            Species.updated_at
        ).where(Species.id == db_species.id)
    )
    return result.mappings().first()


async def get_species_nearby(
    session: AsyncSession,
    search_params: schemas.SpeciesNearbySearch
) -> list[dict]:
    """지정된 위치 반경 내의 종 조회"""
    # ST_SetSRID(ST_MakePoint(lng, lat), 4326)으로 기준점 생성
    reference_point = ST_SetSRID(
        ST_MakePoint(search_params.longitude, search_params.latitude),
        4326
    )

    result = await session.execute(
        select(
            Species.id,
            Species.name_korean,
            Species.name_scientific,
            ST_AsText(Species.location).label("location"),
            Species.description,
            Species.created_at,
            Species.updated_at
        )
        .where(
            ST_DWithin(
                Species.location,
                reference_point,
                search_params.radius_meters
            )
        )
        .order_by(Species.name_korean)
    )
    return result.mappings().all()
