import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.species import Species


class TestEndangeredEndpoints:
    """Endangered API 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_endangered_species_empty(self, client: AsyncClient):
        """빈 멸종위기종 목록"""
        response = await client.get("/api/v1/endangered/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_endangered_species(self, client: AsyncClient, endangered_species):
        """멸종위기종 목록 조회"""
        response = await client.get("/api/v1/endangered/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 멸종위기 + 취약 종만 포함
        assert data["data"]["total"] == 8

    @pytest.mark.asyncio
    async def test_get_endangered_species_filter_by_region(self, client: AsyncClient, endangered_species):
        """지역별 멸종위기종 필터링"""
        response = await client.get("/api/v1/endangered/?region=대한민국")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 5
        for item in data["data"]["items"]:
            assert item["region"] == "대한민국"

    @pytest.mark.asyncio
    async def test_get_endangered_species_filter_by_category(self, client: AsyncClient, endangered_species):
        """카테고리별 멸종위기종 필터링"""
        response = await client.get("/api/v1/endangered/?category=동물")
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["category"] == "동물"

    @pytest.mark.asyncio
    async def test_get_endangered_species_pagination(self, client: AsyncClient, endangered_species):
        """멸종위기종 페이지네이션"""
        response = await client.get("/api/v1/endangered/?page=1&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 3
        assert data["data"]["page"] == 1

    @pytest.mark.asyncio
    async def test_get_most_mentioned_endangered(self, client: AsyncClient, endangered_species):
        """가장 많이 조회된 멸종위기종"""
        response = await client.get("/api/v1/endangered/most-mentioned?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 5

        # 조회수 내림차순 정렬 확인
        for i in range(len(data["data"]) - 1):
            assert data["data"][i]["search_count"] >= data["data"][i + 1]["search_count"]

    @pytest.mark.asyncio
    async def test_get_endangered_statistics(self, client: AsyncClient, endangered_species):
        """멸종위기종 통계"""
        response = await client.get("/api/v1/endangered/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_endangered" in data["data"]
        assert "by_category" in data["data"]
        assert "by_region" in data["data"]
        assert "by_conservation_status" in data["data"]
        assert "by_country" in data["data"]

    @pytest.mark.asyncio
    async def test_get_endangered_statistics_values(self, client: AsyncClient, endangered_species):
        """멸종위기종 통계 값 확인"""
        response = await client.get("/api/v1/endangered/statistics")
        data = response.json()

        # 전체 멸종위기종 수
        assert data["data"]["total_endangered"] == 8

        # 보전상태별
        assert "멸종위기" in data["data"]["by_conservation_status"]
        assert "취약" in data["data"]["by_conservation_status"]

    @pytest.mark.asyncio
    async def test_get_critical_species(self, client: AsyncClient, endangered_species):
        """멸종위기 상태 종 조회"""
        response = await client.get("/api/v1/endangered/critical?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 모두 멸종위기 상태인지 확인
        for item in data["data"]:
            assert item["conservation_status"] == "멸종위기"

    @pytest.mark.asyncio
    async def test_get_region_endangered(self, client: AsyncClient, endangered_species):
        """지역별 멸종위기종 요약"""
        response = await client.get("/api/v1/endangered/region/대한민국")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["region"] == "대한민국"
        assert data["data"]["total_endangered"] == 5
        assert "by_category" in data["data"]
        assert "by_conservation_status" in data["data"]

    @pytest.mark.asyncio
    async def test_get_region_endangered_with_category(self, client: AsyncClient, endangered_species):
        """지역별 멸종위기종 카테고리 필터"""
        response = await client.get("/api/v1/endangered/region/대한민국?category=동물")
        assert response.status_code == 200
        data = response.json()

        # 동물 카테고리만 포함
        if "동물" in data["data"]["by_category"]:
            for species in data["data"]["by_category"]["동물"]:
                assert "id" in species
                assert "name" in species

    @pytest.mark.asyncio
    async def test_get_region_endangered_empty(self, client: AsyncClient, endangered_species):
        """멸종위기종 없는 지역"""
        response = await client.get("/api/v1/endangered/region/없는지역")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_endangered"] == 0


class TestEndangeredCRUD:
    """멸종위기종 데이터베이스 테스트"""

    def test_filter_endangered_only(self, db_session: Session, endangered_species):
        """멸종위기 + 취약만 필터링"""
        results = db_session.query(Species).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).all()

        assert len(results) == 8
        for species in results:
            assert species.conservation_status in ["멸종위기", "취약"]

    def test_count_by_conservation_status(self, db_session: Session, endangered_species):
        """보전상태별 카운트"""
        results = db_session.query(
            Species.conservation_status,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).group_by(Species.conservation_status).all()

        stats = {r.conservation_status: r.count for r in results}
        assert stats["멸종위기"] == 5
        assert stats["취약"] == 3

    def test_count_by_region(self, db_session: Session, endangered_species):
        """지역별 멸종위기종 카운트"""
        results = db_session.query(
            Species.region,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).group_by(Species.region).all()

        stats = {r.region: r.count for r in results}
        assert stats["대한민국"] == 5
        assert stats["미국"] == 3

    def test_count_by_category(self, db_session: Session, endangered_species):
        """카테고리별 멸종위기종 카운트"""
        results = db_session.query(
            Species.category,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).group_by(Species.category).all()

        stats = {r.category: r.count for r in results}
        assert "동물" in stats

    def test_most_mentioned_sorting(self, db_session: Session, endangered_species):
        """조회수 정렬 확인"""
        results = db_session.query(Species).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).order_by(desc(Species.search_count)).limit(5).all()

        # 내림차순 정렬 확인
        for i in range(len(results) - 1):
            assert results[i].search_count >= results[i + 1].search_count

    def test_count_by_country(self, db_session: Session, endangered_species):
        """국가별 멸종위기종 카운트"""
        results = db_session.query(
            Species.country,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).group_by(Species.country).order_by(desc("count")).all()

        assert len(results) > 0
        # 첫 번째가 가장 많음
        if len(results) > 1:
            assert results[0].count >= results[1].count


class TestEndangeredFiltering:
    """멸종위기종 복합 필터링 테스트"""

    def test_filter_by_region_and_category(self, db_session: Session, endangered_species):
        """지역 + 카테고리 필터"""
        results = db_session.query(Species).filter(
            Species.conservation_status.in_(["멸종위기", "취약"]),
            Species.region == "대한민국",
            Species.category == "동물"
        ).all()

        for species in results:
            assert species.region == "대한민국"
            assert species.category == "동물"
            assert species.conservation_status in ["멸종위기", "취약"]

    def test_filter_critical_only(self, db_session: Session, endangered_species):
        """멸종위기만 필터"""
        results = db_session.query(Species).filter(
            Species.conservation_status == "멸종위기"
        ).all()

        assert len(results) == 5
        for species in results:
            assert species.conservation_status == "멸종위기"

    def test_search_count_order(self, db_session: Session, endangered_species):
        """조회수 순 정렬"""
        results = db_session.query(Species).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).order_by(desc(Species.search_count)).all()

        # 조회수 내림차순 확인
        for i in range(len(results) - 1):
            assert results[i].search_count >= results[i + 1].search_count


class TestEndangeredStatistics:
    """멸종위기종 통계 계산 테스트"""

    def test_aggregate_by_multiple_dimensions(self, db_session: Session):
        """다차원 집계 테스트"""
        # 다양한 데이터 생성
        data = [
            ("종1", "동물", "대한민국", "멸종위기"),
            ("종2", "식물", "대한민국", "멸종위기"),
            ("종3", "동물", "미국", "취약"),
            ("종4", "곤충", "대한민국", "멸종위기"),
            ("종5", "해양생물", "일본", "취약"),
        ]

        for name, cat, region, status in data:
            species = Species(
                name=name,
                category=cat,
                region=region,
                country=region,
                conservation_status=status
            )
            db_session.add(species)
        db_session.commit()

        # 국가별 집계
        by_country = db_session.query(
            Species.country,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).group_by(Species.country).all()

        country_stats = {r.country: r.count for r in by_country}
        assert country_stats["대한민국"] == 3
        assert country_stats["미국"] == 1
        assert country_stats["일본"] == 1

        # 카테고리별 집계
        by_category = db_session.query(
            Species.category,
            func.count(Species.id).label("count")
        ).filter(
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).group_by(Species.category).all()

        category_stats = {r.category: r.count for r in by_category}
        assert category_stats["동물"] == 2
        assert category_stats["식물"] == 1
