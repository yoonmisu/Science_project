# /models/species_model.py

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography

from .base import BaseModel


class Species(BaseModel):
    """종(Species) 정보를 저장하는 모델"""
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name_korean: Mapped[str] = mapped_column(String(255), index=True, nullable=False, comment="한국어 종 이름")
    name_scientific: Mapped[str] = mapped_column(String(255), index=True, nullable=False, comment="학명")
    location = mapped_column(
        Geography(geometry_type='POINT', srid=4326),
        nullable=False,
        comment="발견 위치 (위도, 경도)"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="종에 대한 설명")
