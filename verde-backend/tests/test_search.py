import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.models.species import Species
from app.models.search_query import SearchQuery


class TestSearchEndpoints:
    """Search API 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_search_species_basic(self, client: AsyncClient, multiple_species):
        """기본 검색"""
        search_data = {"query": "생물"}
        response = await client.post("/api/v1/search/", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert data["data"]["query"] == "생물"

    @pytest.mark.asyncio
    async def test_search_species_with_category(self, client: AsyncClient, multiple_species):
        """카테고리 필터링 검색"""
        search_data = {
            "query": "생물",
            "category": "동물"
        }
        response = await client.post("/api/v1/search/", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["category"] == "동물"

    @pytest.mark.asyncio
    async def test_search_species_with_region(self, client: AsyncClient, multiple_species):
        """지역 필터링 검색"""
        search_data = {
            "query": "생물",
            "region": "지역 1"
        }
        response = await client.post("/api/v1/search/", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["region"] == "지역 1"

    @pytest.mark.asyncio
    async def test_search_species_pagination(self, client: AsyncClient, multiple_species):
        """검색 결과 페이지네이션"""
        search_data = {"query": "생물"}
        response = await client.post("/api/v1/search/?page=1&limit=5", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 5
        assert data["data"]["page"] == 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, client: AsyncClient, multiple_species):
        """검색 결과 없음"""
        search_data = {"query": "존재하지않는검색어xyz"}
        response = await client.post("/api/v1/search/", json=search_data)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    @pytest.mark.asyncio
    async def test_search_validation_error(self, client: AsyncClient):
        """빈 검색어 - 422"""
        search_data = {"query": ""}
        response = await client.post("/api/v1/search/", json=search_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_trending_searches(self, client: AsyncClient):
        """실시간 인기 검색어"""
        response = await client.get("/api/v1/search/trending")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @pytest.mark.asyncio
    async def test_get_trending_searches_with_limit(self, client: AsyncClient):
        """인기 검색어 limit"""
        response = await client.get("/api/v1/search/trending?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 3

    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, client: AsyncClient, multiple_species):
        """검색어 자동완성"""
        response = await client.get("/api/v1/search/suggestions?q=생물")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "suggestions" in data["data"]
        assert len(data["data"]["suggestions"]) <= 10

    @pytest.mark.asyncio
    async def test_get_search_suggestions_validation(self, client: AsyncClient):
        """자동완성 빈 검색어 - 422"""
        response = await client.get("/api/v1/search/suggestions?q=")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_popular_searches(self, client: AsyncClient, sample_search_query):
        """전체 인기 검색어"""
        response = await client.get("/api/v1/search/popular")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    @pytest.mark.asyncio
    async def test_get_realtime_ranking(self, client: AsyncClient):
        """실시간 검색어 순위"""
        response = await client.get("/api/v1/search/realtime")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSearchQueryCRUD:
    """SearchQuery 데이터베이스 CRUD 테스트"""

    def test_create_search_query(self, db_session: Session):
        """검색어 생성"""
        query = SearchQuery(
            query_text="테스트 검색",
            category="동물",
            region="대한민국",
            search_count=1
        )
        db_session.add(query)
        db_session.commit()

        assert query.id is not None
        assert query.search_count == 1

    def test_increment_search_count(self, db_session: Session, sample_search_query):
        """검색 카운트 증가"""
        original_count = sample_search_query.search_count
        sample_search_query.search_count += 1
        db_session.commit()

        query = db_session.query(SearchQuery).filter(
            SearchQuery.id == sample_search_query.id
        ).first()
        assert query.search_count == original_count + 1

    def test_find_existing_search_query(self, db_session: Session, sample_search_query):
        """기존 검색어 찾기"""
        existing = db_session.query(SearchQuery).filter(
            SearchQuery.query_text == "테스트 검색어",
            SearchQuery.category == "동물",
            SearchQuery.region == "대한민국"
        ).first()

        assert existing is not None
        assert existing.id == sample_search_query.id

    def test_get_popular_queries_sorted(self, db_session: Session):
        """인기 검색어 정렬"""
        # 검색어 여러 개 생성
        for i in range(5):
            query = SearchQuery(
                query_text=f"검색어 {i}",
                search_count=(5 - i) * 10
            )
            db_session.add(query)
        db_session.commit()

        # 검색 카운트 내림차순 정렬
        from sqlalchemy import desc
        results = db_session.query(SearchQuery).order_by(
            desc(SearchQuery.search_count)
        ).limit(3).all()

        assert len(results) == 3
        assert results[0].search_count >= results[1].search_count
        assert results[1].search_count >= results[2].search_count


class TestSearchRanking:
    """검색어 랭킹 업데이트 테스트"""

    @pytest.mark.asyncio
    async def test_search_updates_ranking(self, client: AsyncClient, multiple_species):
        """검색 시 랭킹 업데이트"""
        with patch('app.routers.search.increment_search_count') as mock_increment:
            mock_increment.return_value = 5.0

            search_data = {"query": "테스트"}
            response = await client.post("/api/v1/search/", json=search_data)

            assert response.status_code == 200
            mock_increment.assert_called_once_with("테스트", None)

    @pytest.mark.asyncio
    async def test_search_with_category_updates_ranking(self, client: AsyncClient, multiple_species):
        """카테고리 검색 시 랭킹 업데이트"""
        with patch('app.routers.search.increment_search_count') as mock_increment:
            mock_increment.return_value = 1.0

            search_data = {"query": "테스트", "category": "동물"}
            response = await client.post("/api/v1/search/", json=search_data)

            assert response.status_code == 200
            mock_increment.assert_called_once_with("테스트", "동물")


class TestCaching:
    """캐싱 동작 테스트"""

    @pytest.mark.asyncio
    async def test_trending_searches_caching(self, client: AsyncClient):
        """인기 검색어 캐싱"""
        with patch('app.routers.search.cache_get') as mock_get:
            cached_data = {
                "success": True,
                "data": [{"query": "캐시된 검색어", "count": 100}]
            }
            mock_get.return_value = cached_data

            response = await client.get("/api/v1/search/trending")

            # 캐시된 데이터 반환 확인
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_trending_searches_cache_miss(self, client: AsyncClient):
        """인기 검색어 캐시 미스"""
        with patch('app.routers.search.cache_get', return_value=None):
            with patch('app.routers.search.cache_set') as mock_set:
                with patch('app.routers.search.get_top_searches', return_value=[]):
                    response = await client.get("/api/v1/search/trending")

                    assert response.status_code == 200
                    # 캐시 저장 호출 확인
                    mock_set.assert_called_once()

    def test_search_by_scientific_name(self, db_session: Session):
        """학명으로 검색"""
        species = Species(
            name="한글명",
            scientific_name="Testus scientificus",
            category="동물",
            region="테스트",
            country="테스트"
        )
        db_session.add(species)
        db_session.commit()

        from sqlalchemy import or_
        results = db_session.query(Species).filter(
            or_(
                Species.name.ilike("%scientificus%"),
                Species.scientific_name.ilike("%scientificus%")
            )
        ).all()

        assert len(results) == 1
        assert results[0].scientific_name == "Testus scientificus"

    def test_search_by_description(self, db_session: Session):
        """설명으로 검색"""
        species = Species(
            name="테스트",
            category="동물",
            region="테스트",
            country="테스트",
            description="유니크한 설명 키워드"
        )
        db_session.add(species)
        db_session.commit()

        from sqlalchemy import or_
        results = db_session.query(Species).filter(
            or_(
                Species.name.ilike("%키워드%"),
                Species.description.ilike("%키워드%")
            )
        ).all()

        assert len(results) == 1
