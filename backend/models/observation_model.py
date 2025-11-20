# models/observation_model.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from models.base import Base
from geoalchemy2 import Geometry  # PostGIS 지리 공간 데이터 타입
from datetime import datetime, UTC


class Observation(Base):
    """
    지도상의 특정 지점에서 종이 관측된 기록을 저장하는 모델
    (GeoAlchemy2를 사용하여 공간 정보 처리)
    """
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)

    # 종 모델과의 관계 (Foreign Key)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)

    # 관측 시점
    observed_at = Column(DateTime, default=datetime.now(UTC))

    # 지리 공간 데이터 (PostGIS의 POINT 타입 사용)
    # srid=4326은 위도/경도를 나타내는 WGS84 좌표계를 의미합니다.
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)

    # 종 모델과의 관계 정의
    species = relationship("Species", backref="observations")

    # (선택적) 위도와 경도를 일반 컬럼으로도 저장 (쿼리 편의성)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Observation(species_id={self.species_id}, location='{self.location}')>"