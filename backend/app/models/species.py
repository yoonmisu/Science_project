from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.database import Base


class CategoryEnum(str, enum.Enum):
    ANIMAL = "animal"
    PLANT = "plant"
    INSECT = "insect"
    MARINE = "marine"


class ConservationStatusEnum(str, enum.Enum):
    LC = "LC"  # Least Concern
    NT = "NT"  # Near Threatened
    VU = "VU"  # Vulnerable
    EN = "EN"  # Endangered
    CR = "CR"  # Critically Endangered
    EW = "EW"  # Extinct in the Wild
    EX = "EX"  # Extinct


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Information
    name_ko = Column(String(255), nullable=False, index=True)  # Korean name
    name_en = Column(String(255), index=True)  # English name
    name_scientific = Column(String(255), index=True)  # Scientific name

    # Classification
    category = Column(Enum(CategoryEnum), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)  # Korea, Japan, USA, China, Russia

    # Details
    description = Column(Text)
    habitat = Column(Text)
    distribution = Column(Text)

    # Conservation
    conservation_status = Column(Enum(ConservationStatusEnum), default=ConservationStatusEnum.LC)
    is_endangered = Column(Boolean, default=False, index=True)
    population_trend = Column(String(50))  # increasing, stable, decreasing, unknown

    # Media
    image_url = Column(String(500))
    thumbnail_url = Column(String(500))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Species {self.name_ko} ({self.name_scientific})>"
