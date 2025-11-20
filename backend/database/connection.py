# /database/connection.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 환경 변수 로드
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# 🚨 DB URL 구성 (FATAL 오류 해결: POSTGRES_DB 사용) 🚨
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "ssl": "disable",
        "timeout": 10
    }  # SSL 검증 비활성화
)

# 비동기 세션 생성기
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 🚨 get_db_session 함수 정의 (ImportError 해결) 🚨
async def get_db_session() -> AsyncSession:
    """FastAPI 엔드포인트에서 비동기 DB 세션을 가져오기 위한 의존성."""
    async with AsyncSessionLocal() as session:
        yield session