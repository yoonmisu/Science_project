from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class RegionBiodiversity(Base):
    __tablename__ = "region_biodiversity"

    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(100), nullable=False, unique=True, index=True)
    country = Column(String(100), nullable=False, index=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    total_species_count = Column(Integer, default=0, nullable=False)
    endangered_count = Column(Integer, default=0, nullable=False)
    plant_count = Column(Integer, default=0, nullable=False)
    animal_count = Column(Integer, default=0, nullable=False)
    insect_count = Column(Integer, default=0, nullable=False)
    marine_count = Column(Integer, default=0, nullable=False)

    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Composite indexes
    __table_args__ = (
        Index('ix_region_biodiversity_country', 'country'),
        Index('ix_region_biodiversity_coords', 'latitude', 'longitude'),
    )

    def __repr__(self):
        return f"<RegionBiodiversity(id={self.id}, region_name={self.region_name}, country={self.country})>"
