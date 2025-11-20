from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base


class RegionBiodiversity(Base):
    __tablename__ = "region_biodiversity"

    id = Column(Integer, primary_key=True, index=True)

    # Region Information
    region = Column(String(100), nullable=False, unique=True, index=True)
    region_ko = Column(String(100))  # Korean name

    # Species Counts
    total_species = Column(Integer, default=0)
    animal_count = Column(Integer, default=0)
    plant_count = Column(Integer, default=0)
    insect_count = Column(Integer, default=0)
    marine_count = Column(Integer, default=0)

    # Conservation Statistics
    endangered_count = Column(Integer, default=0)
    critically_endangered_count = Column(Integer, default=0)

    # Biodiversity Metrics
    biodiversity_index = Column(Float)  # Custom biodiversity score
    endemic_species_count = Column(Integer, default=0)  # Species unique to this region

    # Geographic Data
    area_km2 = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RegionBiodiversity {self.region} ({self.total_species} species)>"
