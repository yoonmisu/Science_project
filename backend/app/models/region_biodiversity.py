from sqlalchemy import Column, Integer, String, DateTime, Float, Index
from sqlalchemy.sql import func
from app.database import Base


class RegionBiodiversity(Base):
    __tablename__ = "region_biodiversity"

    id = Column(Integer, primary_key=True, index=True)

    # Region Information
    region_name = Column(String(100), nullable=False, unique=True, index=True)
    country = Column(String(100), nullable=False, index=True)

    # Geographic Data
    latitude = Column(Float)
    longitude = Column(Float)

    # Species Counts
    total_species_count = Column(Integer, default=0)
    endangered_count = Column(Integer, default=0)
    plant_count = Column(Integer, default=0)
    animal_count = Column(Integer, default=0)
    insect_count = Column(Integer, default=0)
    marine_count = Column(Integer, default=0)

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Composite indexes
    __table_args__ = (
        Index('ix_region_country', 'country'),
        Index('ix_region_coords', 'latitude', 'longitude'),
    )

    def __repr__(self):
        return f"<RegionBiodiversity {self.region_name} ({self.total_species_count} species)>"
