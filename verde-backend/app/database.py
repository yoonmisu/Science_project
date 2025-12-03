from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.search_history import Base
import os

# SQLite 데이터베이스 경로
DATABASE_URL = "sqlite:///./verde.db"

# 데이터베이스 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 전용 설정
)

# 세션 로컬 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 테이블 생성
def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("✅ 데이터베이스 테이블이 생성되었습니다.")

# 데이터베이스 세션 의존성
def get_db():
    """FastAPI 의존성: 데이터베이스 세션 제공"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
