from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class SearchHistory(Base):
    """검색 기록 모델"""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True, nullable=False)  # 검색어
    searched_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 검색 시간
    category = Column(String, nullable=True)  # 검색된 카테고리
    result_count = Column(Integer, default=0)  # 검색 결과 개수

    def __repr__(self):
        return f"<SearchHistory(query='{self.query}', searched_at='{self.searched_at}')>"
