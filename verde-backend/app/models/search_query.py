from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(200), nullable=False, index=True)
    search_count = Column(Integer, default=1, nullable=False)
    last_searched_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    category = Column(String(50), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)

    # Composite indexes
    __table_args__ = (
        Index('ix_search_queries_query_category', 'query_text', 'category'),
        Index('ix_search_queries_search_count', 'search_count'),
    )

    def __repr__(self):
        return f"<SearchQuery(id={self.id}, query_text={self.query_text}, count={self.search_count})>"
