from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, Index, Float
from sqlalchemy.sql import func
from geoalchemy2 import Geography
import enum
from app.database import Base


class CategoryEnum(str, enum.Enum):
    PLANT = "식물"
    ANIMAL = "동물"
    INSECT = "곤충"
    MARINE = "해양생물"


class ConservationStatusEnum(str, enum.Enum):
    ENDANGERED = "멸종위기"
    VULNERABLE = "취약"
    NEAR_THREATENED = "준위협"
    LEAST_CONCERN = "관심대상"
    SAFE = "안전"


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True, comment="한글명")
    scientific_name = Column(String(200), nullable=True, comment="학명")
    category = Column(
        Enum(
            CategoryEnum,
            name="category_enum",
            values_callable=lambda x: [e.value for e in x],
            create_constraint=True,
            create_type=False
        ),
        nullable=False,
        index=True
    )
    region = Column(String(100), nullable=False, index=True, comment="지역")
    country = Column(String(100), nullable=False, index=True, comment="국가")

    description = Column(Text, nullable=True, comment="설명")
    characteristics = Column(JSON, nullable=True, comment="특징 리스트")
    image_url = Column(String(500), nullable=True)

    conservation_status = Column(
        Enum(
            ConservationStatusEnum,
            name="conservation_status_enum",
            values_callable=lambda x: [e.value for e in x],
            create_constraint=True,
            create_type=False
        ),
        nullable=True,
        index=True
    )

    search_count = Column(Integer, default=0, nullable=False, comment="조회수")

    # 공간 데이터 컬럼
    latitude = Column(Float, nullable=True, comment="위도")
    longitude = Column(Float, nullable=True, comment="경도")
    location = Column(
        Geography(geometry_type='POINT', srid=4326),
        nullable=True,
        comment="공간 좌표 (PostGIS)"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Composite indexes for common queries
    # Note: Single-column indexes are already created by index=True on columns
    __table_args__ = (
        Index('ix_species_country_category', 'country', 'category'),
        Index('ix_species_region_category', 'region', 'category'),
    )

    def __repr__(self):
        return f"<Species(id={self.id}, name={self.name}, country={self.country})>"
