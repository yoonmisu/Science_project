import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock

from app.main import app
from app.database import Base, get_db
from app.models.species import Species
from app.models.search_query import SearchQuery
from app.models.region_biodiversity import RegionBiodiversity

# 테스트용 SQLite 인메모리 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """테스트용 데이터베이스 세션"""
    # 기존 테이블 정리 후 새로 생성 (인덱스 충돌 방지)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def override_get_db(db_session: Session):
    """get_db 의존성 오버라이드"""
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


@pytest.fixture(scope="function")
def mock_redis():
    """Redis 모킹"""
    mock = MagicMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.zincrby.return_value = 1.0
    mock.zrevrange.return_value = []
    mock.ttl.return_value = -1
    mock.expire.return_value = True
    mock.ping.return_value = True
    mock.keys.return_value = []
    mock.exists.return_value = 0
    return mock


@pytest.fixture(scope="function")
async def client(override_get_db, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """비동기 테스트 클라이언트"""
    app.dependency_overrides[get_db] = override_get_db

    with patch('app.cache.redis_client', mock_redis):
        with patch('app.routers.species.cache_get', return_value=None):
            with patch('app.routers.species.cache_set', return_value=True):
                with patch('app.routers.search.cache_get', return_value=None):
                    with patch('app.routers.search.cache_set', return_value=True):
                        with patch('app.routers.search.increment_search_count', return_value=1.0):
                            with patch('app.routers.search.get_top_searches', return_value=[]):
                                transport = ASGITransport(app=app)
                                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                                    yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_species_data():
    """샘플 종 데이터"""
    return {
        "name": "테스트 생물",
        "scientific_name": "Testus speciesus",
        "category": "동물",
        "region": "테스트 지역",
        "country": "대한민국",
        "description": "테스트용 생물 설명입니다.",
        "characteristics": ["특징1", "특징2"],
        "image_url": "https://example.com/test.jpg",
        "conservation_status": "취약"
    }


@pytest.fixture
def sample_species(db_session: Session) -> Species:
    """샘플 종 생성"""
    species = Species(
        name="테스트 생물",
        scientific_name="Testus speciesus",
        category="동물",
        region="테스트 지역",
        country="대한민국",
        description="테스트용 생물입니다.",
        characteristics=["특징1", "특징2"],
        conservation_status="취약",
        search_count=10
    )
    db_session.add(species)
    db_session.commit()
    db_session.refresh(species)
    return species


@pytest.fixture
def multiple_species(db_session: Session) -> list[Species]:
    """여러 종 생성"""
    species_list = []
    categories = ["동물", "식물", "곤충", "해양생물"]
    statuses = ["멸종위기", "취약", "준위협", "관심대상", "안전"]

    for i in range(20):
        species = Species(
            name=f"생물 {i+1}",
            scientific_name=f"Species {i+1}",
            category=categories[i % 4],
            region=f"지역 {i % 3 + 1}",
            country="대한민국" if i < 10 else "미국",
            description=f"생물 {i+1} 설명",
            conservation_status=statuses[i % 5],
            search_count=i * 10
        )
        db_session.add(species)
        species_list.append(species)

    db_session.commit()
    return species_list


@pytest.fixture
def sample_region(db_session: Session) -> RegionBiodiversity:
    """샘플 지역 생성"""
    region = RegionBiodiversity(
        region_name="대한민국",
        country="대한민국",
        latitude=37.5665,
        longitude=126.9780,
        total_species_count=100,
        endangered_count=20,
        plant_count=30,
        animal_count=25,
        insect_count=25,
        marine_count=20
    )
    db_session.add(region)
    db_session.commit()
    db_session.refresh(region)
    return region


@pytest.fixture
def sample_search_query(db_session: Session) -> SearchQuery:
    """샘플 검색어 생성"""
    query = SearchQuery(
        query_text="테스트 검색어",
        category="동물",
        region="대한민국",
        search_count=50
    )
    db_session.add(query)
    db_session.commit()
    db_session.refresh(query)
    return query


@pytest.fixture
def endangered_species(db_session: Session) -> list[Species]:
    """멸종위기종 생성"""
    species_list = []

    for i in range(5):
        species = Species(
            name=f"멸종위기종 {i+1}",
            scientific_name=f"Endangered {i+1}",
            category=["동물", "식물", "곤충", "해양생물"][i % 4],
            region="대한민국",
            country="대한민국",
            conservation_status="멸종위기",
            search_count=(5 - i) * 20
        )
        db_session.add(species)
        species_list.append(species)

    for i in range(3):
        species = Species(
            name=f"취약종 {i+1}",
            scientific_name=f"Vulnerable {i+1}",
            category="동물",
            region="미국",
            country="미국",
            conservation_status="취약",
            search_count=(3 - i) * 15
        )
        db_session.add(species)
        species_list.append(species)

    db_session.commit()
    return species_list
