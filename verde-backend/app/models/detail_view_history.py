from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DetailViewHistory(Base):
    """상세 조회 기록 모델"""
    __tablename__ = "detail_view_history"

    id = Column(Integer, primary_key=True, index=True)
    taxon_id = Column(Integer, index=True, nullable=False)  # IUCN taxon ID
    species_name = Column(String, nullable=True)  # 종 이름 (표시용)
    scientific_name = Column(String, nullable=True)  # 학명
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 조회 시간
    category = Column(String, nullable=True)  # 카테고리 (동물/식물/곤충/해양생물)

    def __repr__(self):
        return f"<DetailViewHistory(taxon_id={self.taxon_id}, species_name='{self.species_name}', viewed_at='{self.viewed_at}')>"
