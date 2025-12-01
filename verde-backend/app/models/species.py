from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.db.session import Base

class Species(Base):
    __tablename__ = "species"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    scientific_name = Column(String(255))
    common_name = Column(String(255))
    category = Column(String(50), nullable=False, index=True)
    country = Column(String(50), nullable=False, index=True)
    image = Column(String(255))
    color = Column(String(50))
    status = Column(String(50), index=True)
    description = Column(Text)
    population = Column(String(255))
    threats = Column(JSON)
    mentions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
