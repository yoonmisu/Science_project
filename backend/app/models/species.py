from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, Index
from sqlalchemy.sql import func
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

    # Basic Information
    name = Column(String(200), nullable=False, index=True)  # 한글명
    scientific_name = Column(String(200), index=True)  # 학명

    # Classification
    category = Column(Enum(CategoryEnum), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)  # 지역
    country = Column(String(100), nullable=False, index=True)  # 국가

    # Details
    description = Column(Text)  # 설명
    characteristics = Column(JSON)  # 특징 리스트

    # Conservation
    conservation_status = Column(
        Enum(ConservationStatusEnum),
        default=ConservationStatusEnum.SAFE,
        index=True
    )

    # Media
    image_url = Column(String(500))

    # Statistics
    search_count = Column(Integer, default=0, index=True)  # 조회수

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_species_category_country', 'category', 'country'),
        Index('ix_species_country_region', 'country', 'region'),
        Index('ix_species_conservation_category', 'conservation_status', 'category'),
    )

    def __repr__(self):
        return f"<Species {self.name} ({self.scientific_name})>"
