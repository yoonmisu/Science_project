from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.config import settings

# 최적화된 엔진 설정
    # Connection pooling 최적화
    poolclass=QueuePool,
    pool_pre_ping=True,       # 연결 유효성 검사
    pool_size=20,             # 기본 풀 크기
    max_overflow=30,          # 초과 연결 허용 수
    pool_timeout=30,          # 연결 대기 타임아웃
    pool_recycle=3600,        # 1시간마다 연결 재사용
    # 쿼리 최적화
    echo=settings.DEBUG,      # 디버그 모드에서만 SQL 출력
    echo_pool=False,
    # 성능 설정
    connect_args={
        "options": "-c statement_timeout=30000"  # 30초 쿼리 타임아웃
    } if "postgresql" in settings.database_url_fixed else {}


# 연결 이벤트 핸들러
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite 성능 최적화 (테스트용)"""
    if "sqlite" in settings.database_url_fixed:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # 성능 향상을 위해 커밋 후 만료 비활성화
)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """일반 함수용 세션 생성 (의존성 주입 외부에서 사용)"""
    return SessionLocal()
