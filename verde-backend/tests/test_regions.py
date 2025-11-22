import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.region_biodiversity import RegionBiodiversity
from app.models.species import Species


class TestRegionsEndpoints:
    """Regions API 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_all_regions_empty(self, client: AsyncClient):
        """빈 지역 목록 조회"""
        response = await client.get("/api/v1/regions/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_all_regions(self, client: AsyncClient, sample_region):
        """지역 목록 조회"""
        response = await client.get("/api/v1/regions/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["region_name"] == "대한민국"

    @pytest.mark.asyncio
    async def test_regions_sorted_by_species_count(self, client: AsyncClient, db_session: Session):
        """종 수 기준 정렬 확인"""
        # 여러 지역 생성
        regions = [
            RegionBiodiversity(region_name="지역1", country="테스트", total_species_count=100),
            RegionBiodiversity(region_name="지역2", country="테스트", total_species_count=300),
            RegionBiodiversity(region_name="지역3", country="테스트", total_species_count=200),
        ]
        for r in regions:
            db_session.add(r)
        db_session.commit()

        response = await client.get("/api/v1/regions/")
        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]

        # 내림차순 정렬 확인
        assert items[0]["total_species_count"] >= items[1]["total_species_count"]
        assert items[1]["total_species_count"] >= items[2]["total_species_count"]

    @pytest.mark.asyncio
    async def test_get_region_species(self, client: AsyncClient, db_session: Session):
        """특정 지역의 생물종 목록"""
        # 지역에 속한 종 생성
        for i in range(5):
            species = Species(
                name=f"지역 종 {i}",
                category="동물",
                region="테스트지역",
                country="테스트"
            )
            db_session.add(species)
        db_session.commit()

        response = await client.get("/api/v1/regions/테스트지역/species")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["region"] == "테스트지역"
        assert data["data"]["total"] == 5

    @pytest.mark.asyncio
    async def test_get_region_species_with_category_filter(self, client: AsyncClient, db_session: Session):
        """지역 종 목록 카테고리 필터링"""
        # 다양한 카테고리 종 생성
        for category in ["동물", "동물", "식물"]:
            species = Species(
                name=f"종 {category}",
                category=category,
                region="필터테스트",
                country="테스트"
            )
            db_session.add(species)
        db_session.commit()

        response = await client.get("/api/v1/regions/필터테스트/species?category=동물")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 2
        assert data["data"]["category"] == "동물"

    @pytest.mark.asyncio
    async def test_get_region_species_pagination(self, client: AsyncClient, db_session: Session):
        """지역 종 목록 페이지네이션"""
        for i in range(15):
            species = Species(
                name=f"페이지 종 {i}",
                category="동물",
                region="페이지테스트",
                country="테스트"
            )
            db_session.add(species)
        db_session.commit()

        response = await client.get("/api/v1/regions/페이지테스트/species?page=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5
        assert data["data"]["pages"] == 3

    @pytest.mark.asyncio
    async def test_get_region_biodiversity_from_table(self, client: AsyncClient, sample_region):
        """지역 생물다양성 상세 통계 - 테이블에서"""
        response = await client.get(f"/api/v1/regions/{sample_region.region_name}/biodiversity")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["region_name"] == "대한민국"
        assert data["data"]["total_species_count"] == 100

    @pytest.mark.asyncio
    async def test_get_region_biodiversity_calculated(self, client: AsyncClient, db_session: Session):
        """지역 생물다양성 상세 통계 - 계산"""
        # 종만 있고 RegionBiodiversity는 없는 경우
        for i in range(10):
            species = Species(
                name=f"계산 종 {i}",
                category=["동물", "식물", "곤충", "해양생물"][i % 4],
                region="계산테스트",
                country="테스트",
                conservation_status="멸종위기" if i < 3 else "안전"
            )
            db_session.add(species)
        db_session.commit()

        response = await client.get("/api/v1/regions/계산테스트/biodiversity")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_species_count"] == 10
        assert data["data"]["endangered_count"] == 3

    @pytest.mark.asyncio
    async def test_get_region_biodiversity_not_found(self, client: AsyncClient):
        """존재하지 않는 지역 - 404"""
        response = await client.get("/api/v1/regions/없는지역/biodiversity")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_region_biodiversity(self, client: AsyncClient):
        """지역 생물다양성 정보 등록"""
        region_data = {
            "region_name": "새지역",
            "country": "테스트국가",
            "latitude": 35.0,
            "longitude": 127.0,
            "total_species_count": 50,
            "endangered_count": 10,
            "plant_count": 15,
            "animal_count": 15,
            "insect_count": 10,
            "marine_count": 10
        }
        response = await client.post("/api/v1/regions/", json=region_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["region_name"] == "새지역"

    @pytest.mark.asyncio
    async def test_create_region_duplicate(self, client: AsyncClient, sample_region):
        """중복 지역 등록 - 400"""
        region_data = {
            "region_name": "대한민국",  # 이미 존재
            "country": "대한민국"
        }
        response = await client.post("/api/v1/regions/", json=region_data)
        assert response.status_code == 400
        assert "이미 등록된" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_region_category_species(self, client: AsyncClient, db_session: Session):
        """지역 및 카테고리별 종 목록"""
        for i in range(5):
            species = Species(
                name=f"카테고리 종 {i}",
                category="동물",
                region="카테고리테스트",
                country="테스트"
            )
            db_session.add(species)
        db_session.commit()

        response = await client.get("/api/v1/regions/카테고리테스트/categories/동물")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["region"] == "카테고리테스트"
        assert data["data"]["category"] == "동물"
        assert data["data"]["total"] == 5


class TestRegionBiodiversityCRUD:
    """RegionBiodiversity 데이터베이스 CRUD 테스트"""

    def test_create_region(self, db_session: Session):
        """지역 생성"""
        region = RegionBiodiversity(
            region_name="테스트 지역",
            country="테스트 국가",
            latitude=37.0,
            longitude=127.0,
            total_species_count=100
        )
        db_session.add(region)
        db_session.commit()

        assert region.id is not None

    def test_region_unique_constraint(self, db_session: Session, sample_region):
        """지역 이름 unique 제약"""
        duplicate = RegionBiodiversity(
            region_name="대한민국",  # 중복
            country="테스트"
        )
        db_session.add(duplicate)

        with pytest.raises(Exception):
            db_session.commit()

    def test_update_region_stats(self, db_session: Session, sample_region):
        """지역 통계 업데이트"""
        sample_region.total_species_count = 200
        sample_region.endangered_count = 50
        db_session.commit()

        region = db_session.query(RegionBiodiversity).filter(
            RegionBiodiversity.id == sample_region.id
        ).first()
        assert region.total_species_count == 200
        assert region.endangered_count == 50

    def test_get_region_by_country(self, db_session: Session):
        """국가별 지역 조회"""
        regions = [
            RegionBiodiversity(region_name="지역A", country="국가1"),
            RegionBiodiversity(region_name="지역B", country="국가1"),
            RegionBiodiversity(region_name="지역C", country="국가2"),
        ]
        for r in regions:
            db_session.add(r)
        db_session.commit()

        results = db_session.query(RegionBiodiversity).filter(
            RegionBiodiversity.country == "국가1"
        ).all()
        assert len(results) == 2

    def test_region_coordinates(self, db_session: Session):
        """좌표 저장 테스트"""
        region = RegionBiodiversity(
            region_name="좌표테스트",
            country="테스트",
            latitude=37.5665,
            longitude=126.9780
        )
        db_session.add(region)
        db_session.commit()

        loaded = db_session.query(RegionBiodiversity).filter(
            RegionBiodiversity.region_name == "좌표테스트"
        ).first()
        assert loaded.latitude == 37.5665
        assert loaded.longitude == 126.9780


class TestRegionStatistics:
    """지역 통계 계산 테스트"""

    def test_calculate_category_counts(self, db_session: Session):
        """카테고리별 종 수 계산"""
        categories = ["동물", "동물", "식물", "곤충", "해양생물"]
        for i, cat in enumerate(categories):
            species = Species(
                name=f"종 {i}",
                category=cat,
                region="통계테스트",
                country="테스트"
            )
            db_session.add(species)
        db_session.commit()

        from sqlalchemy import func
        results = db_session.query(
            Species.category,
            func.count(Species.id).label("count")
        ).filter(
            Species.region == "통계테스트"
        ).group_by(Species.category).all()

        stats = {r.category: r.count for r in results}
        assert stats["동물"] == 2
        assert stats["식물"] == 1
        assert stats["곤충"] == 1
        assert stats["해양생물"] == 1

    def test_calculate_endangered_count(self, db_session: Session):
        """멸종위기종 수 계산"""
        statuses = ["멸종위기", "멸종위기", "취약", "안전", "안전"]
        for i, status in enumerate(statuses):
            species = Species(
                name=f"종 {i}",
                category="동물",
                region="멸종위기테스트",
                country="테스트",
                conservation_status=status
            )
            db_session.add(species)
        db_session.commit()

        endangered = db_session.query(Species).filter(
            Species.region == "멸종위기테스트",
            Species.conservation_status.in_(["멸종위기", "취약"])
        ).count()

        assert endangered == 3
