import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.species import Species


class TestSpeciesEndpoints:
    """Species API 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_species_list_empty(self, client: AsyncClient):
        """빈 종 목록 조회"""
        response = await client.get("/api/v1/species/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_species_list_with_data(self, client: AsyncClient, multiple_species):
        """종 목록 조회"""
        response = await client.get("/api/v1/species/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 20
        assert data["data"]["total"] == 20

    @pytest.mark.asyncio
    async def test_get_species_list_pagination(self, client: AsyncClient, multiple_species):
        """페이지네이션 테스트"""
        response = await client.get("/api/v1/species/?page=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 5
        assert data["data"]["page"] == 1
        assert data["data"]["pages"] == 4

        # 두 번째 페이지
        response = await client.get("/api/v1/species/?page=2&limit=5")
        data = response.json()
        assert len(data["data"]["items"]) == 5
        assert data["data"]["page"] == 2

    @pytest.mark.asyncio
    async def test_get_species_list_filter_by_category(self, client: AsyncClient, multiple_species):
        """카테고리 필터링"""
        response = await client.get("/api/v1/species/?category=동물")
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["category"] == "동물"

    @pytest.mark.asyncio
    async def test_get_species_list_filter_by_country(self, client: AsyncClient, multiple_species):
        """국가 필터링"""
        response = await client.get("/api/v1/species/?country=대한민국")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 10
        for item in data["data"]["items"]:
            assert item["country"] == "대한민국"

    @pytest.mark.asyncio
    async def test_get_species_list_filter_by_conservation_status(self, client: AsyncClient, multiple_species):
        """보전상태 필터링"""
        response = await client.get("/api/v1/species/?conservation_status=멸종위기")
        assert response.status_code == 200
        data = response.json()
        for item in data["data"]["items"]:
            assert item["conservation_status"] == "멸종위기"

    @pytest.mark.asyncio
    async def test_get_species_list_sorting(self, client: AsyncClient, multiple_species):
        """정렬 테스트"""
        response = await client.get("/api/v1/species/?sort_by=search_count&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        items = data["data"]["items"]
        # 내림차순 정렬 확인
        for i in range(len(items) - 1):
            assert items[i]["search_count"] >= items[i + 1]["search_count"]

    @pytest.mark.asyncio
    async def test_get_species_by_id(self, client: AsyncClient, sample_species):
        """특정 종 조회"""
        response = await client.get(f"/api/v1/species/{sample_species.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "테스트 생물"
        # 조회수 증가 확인
        assert data["data"]["search_count"] == 11

    @pytest.mark.asyncio
    async def test_get_species_by_id_not_found(self, client: AsyncClient):
        """존재하지 않는 종 조회 - 404"""
        response = await client.get("/api/v1/species/99999")
        assert response.status_code == 404
        data = response.json()
        assert "찾을 수 없습니다" in data["detail"]

    @pytest.mark.asyncio
    async def test_create_species(self, client: AsyncClient, sample_species_data):
        """새 종 등록"""
        response = await client.post("/api/v1/species/", json=sample_species_data)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == sample_species_data["name"]
        assert "message" in data

    @pytest.mark.asyncio
    async def test_create_species_validation_error(self, client: AsyncClient):
        """잘못된 데이터로 종 등록 - 422"""
        invalid_data = {
            "name": "",  # 빈 이름
            "category": "invalid",  # 잘못된 카테고리
        }
        response = await client.post("/api/v1/species/", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_species(self, client: AsyncClient, sample_species):
        """종 정보 수정"""
        update_data = {
            "name": "수정된 생물",
            "description": "수정된 설명"
        }
        response = await client.put(f"/api/v1/species/{sample_species.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "수정된 생물"
        assert data["data"]["description"] == "수정된 설명"

    @pytest.mark.asyncio
    async def test_update_species_not_found(self, client: AsyncClient):
        """존재하지 않는 종 수정 - 404"""
        response = await client.put("/api/v1/species/99999", json={"name": "test"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_species(self, client: AsyncClient, sample_species):
        """종 삭제"""
        response = await client.delete(f"/api/v1/species/{sample_species.id}")
        assert response.status_code == 204

        # 삭제 확인
        response = await client.get(f"/api/v1/species/{sample_species.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_species_not_found(self, client: AsyncClient):
        """존재하지 않는 종 삭제 - 404"""
        response = await client.delete("/api/v1/species/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_random_species(self, client: AsyncClient, sample_species):
        """랜덤 종 조회"""
        response = await client.get("/api/v1/species/random")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    @pytest.mark.asyncio
    async def test_get_random_species_empty(self, client: AsyncClient):
        """데이터 없을 때 랜덤 종 조회 - 404"""
        response = await client.get("/api/v1/species/random")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_popular_species(self, client: AsyncClient, multiple_species):
        """인기 종 조회"""
        response = await client.get("/api/v1/species/popular?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 5


class TestSpeciesCRUD:
    """데이터베이스 CRUD 테스트"""

    def test_create_species_db(self, db_session: Session):
        """DB에 종 생성"""
        species = Species(
            name="DB 테스트 생물",
            scientific_name="DB Testus",
            category="식물",
            region="서울",
            country="대한민국",
            conservation_status="안전"
        )
        db_session.add(species)
        db_session.commit()

        assert species.id is not None
        assert species.search_count == 0

    def test_read_species_db(self, db_session: Session, sample_species):
        """DB에서 종 조회"""
        species = db_session.query(Species).filter(Species.id == sample_species.id).first()
        assert species is not None
        assert species.name == "테스트 생물"

    def test_update_species_db(self, db_session: Session, sample_species):
        """DB에서 종 수정"""
        sample_species.name = "수정된 이름"
        db_session.commit()

        species = db_session.query(Species).filter(Species.id == sample_species.id).first()
        assert species.name == "수정된 이름"

    def test_delete_species_db(self, db_session: Session, sample_species):
        """DB에서 종 삭제"""
        species_id = sample_species.id
        db_session.delete(sample_species)
        db_session.commit()

        species = db_session.query(Species).filter(Species.id == species_id).first()
        assert species is None

    def test_species_with_characteristics(self, db_session: Session):
        """JSON 필드 테스트"""
        species = Species(
            name="JSON 테스트",
            category="동물",
            region="테스트",
            country="테스트",
            characteristics=["특징1", "특징2", "특징3"]
        )
        db_session.add(species)
        db_session.commit()

        loaded = db_session.query(Species).filter(Species.id == species.id).first()
        assert loaded.characteristics == ["특징1", "특징2", "특징3"]

    def test_filter_by_multiple_conditions(self, db_session: Session, multiple_species):
        """복합 조건 필터링"""
        results = db_session.query(Species).filter(
            Species.country == "대한민국",
            Species.category == "동물"
        ).all()

        for species in results:
            assert species.country == "대한민국"
            assert species.category == "동물"
