from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)

    # Search Information
    query = Column(String(500), nullable=False, index=True)
    category = Column(String(50))  # Filter by category if specified
    region = Column(String(100))  # Filter by region if specified

    # Results
    results_count = Column(Integer, default=0)

    # User Information (optional)
    user_ip = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SearchQuery '{self.query}' ({self.results_count} results)>"
