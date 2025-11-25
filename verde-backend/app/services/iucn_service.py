"""
IUCN Red List API 통합 서비스
https://apiv3.iucnredlist.org/api/v3/docs
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class IUCNService:
    """
    IUCN Red List API 연동 서비스

    사용자 시나리오:
    1. 사용자가 "한국의 멸종위기종 현황" 요청
    2. 이 서비스가 IUCN Red List API에서 공식 평가 데이터 가져옴
    3. CR(위급), EN(위기), VU(취약) 등급 분류
    4. 보전 상태 및 위협 요인 정보 제공

    주요 기능:
    - fetch_endangered_species: 멸종위기종 목록 (CR, EN, VU)
    - get_species_conservation_status: 종별 상세 보전 정보
    - get_regional_assessment: 국가별 멸종위기 평가
    - get_country_species: 국가별 평가된 종 목록

    IUCN 보전 상태 등급:
    - EX: 멸종 (Extinct)
    - EW: 야생멸종 (Extinct in the Wild)
    - CR: 위급 (Critically Endangered) ⚠️
    - EN: 위기 (Endangered) ⚠️
    - VU: 취약 (Vulnerable) ⚠️
    - NT: 준위협 (Near Threatened)
    - LC: 관심대상 (Least Concern)

    데이터 신뢰성:
    - 전 세계 생물학자들이 평가한 공식 데이터
    - 위협 요인, 보전 조치, 서식지 정보 포함
    """

    BASE_URL = "https://apiv3.iucnredlist.org/api/v3"

    # IUCN 보전 상태 코드
    CONSERVATION_STATUS = {
        "EX": {"name": "멸종", "name_en": "Extinct", "priority": 1},
        "EW": {"name": "야생멸종", "name_en": "Extinct in the Wild", "priority": 2},
        "CR": {"name": "멸종위기", "name_en": "Critically Endangered", "priority": 3},
        "EN": {"name": "멸종위기", "name_en": "Endangered", "priority": 4},
        "VU": {"name": "취약", "name_en": "Vulnerable", "priority": 5},
        "NT": {"name": "준위협", "name_en": "Near Threatened", "priority": 6},
        "LC": {"name": "관심대상", "name_en": "Least Concern", "priority": 7},
        "DD": {"name": "정보부족", "name_en": "Data Deficient", "priority": 8},
        "NE": {"name": "미평가", "name_en": "Not Evaluated", "priority": 9}
    }

    def __init__(self):
        self.api_key = getattr(settings, 'IUCN_API_KEY', '')
        self.client = httpx.AsyncClient(timeout=30.0)

        if not self.api_key:
            logger.warning("IUCN_API_KEY not configured")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def close(self):
        await self.client.aclose()

    def _get_url(self, endpoint: str) -> str:
        """API URL 생성"""
        return f"{self.BASE_URL}/{endpoint}?token={self.api_key}"

    # =========================================================================
    # 멸종위기종 목록
    # =========================================================================
    async def fetch_endangered_species(
        self,
        category: Optional[str] = None,
        page: int = 0
    ) -> List[Dict]:
        """
        멸종위기종 목록 조회

        Args:
            category: IUCN 카테고리 (CR, EN, VU)
            page: 페이지 번호

        Returns:
            멸종위기종 리스트
        """
        try:
            if not self.api_key:
                logger.error("IUCN API key not configured")
                return []

            if category:
                url = self._get_url(f"species/category/{category}")
            else:
                # 모든 멸종위기종 (CR, EN, VU)
                all_species = []
                for cat in ["CR", "EN", "VU"]:
                    url = self._get_url(f"species/category/{cat}")
                    response = await self.client.get(url)
                    response.raise_for_status()
                    data = response.json()

                    for species in data.get("result", []):
                        species["category"] = cat
                        all_species.append(self._transform_species(species))

                logger.info(f"IUCN endangered species: {len(all_species)}")
                return all_species

            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            species_list = []
            for species in data.get("result", []):
                species["category"] = category
                species_list.append(self._transform_species(species))

            logger.info(f"IUCN {category} species: {len(species_list)}")
            return species_list

        except Exception as e:
            logger.error(f"IUCN endangered species error: {str(e)}")
            raise

    # =========================================================================
    # 종 보전 상태 조회
    # =========================================================================
    async def get_species_conservation_status(
        self,
        scientific_name: str
    ) -> Optional[Dict]:
        """
        특정 종의 상세 보전 정보

        Args:
            scientific_name: 학명

        Returns:
            보전 정보 딕셔너리
        """
        try:
            if not self.api_key:
                return None

            url = self._get_url(f"species/{scientific_name}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            result = data.get("result", [])
            if not result:
                return None

            species_data = result[0]

            # 추가 정보 조회
            threats = await self._get_species_threats(species_data.get("taxonid"))
            conservation_measures = await self._get_conservation_measures(species_data.get("taxonid"))
            habitats = await self._get_species_habitats(species_data.get("taxonid"))

            return {
                "taxon_id": species_data.get("taxonid"),
                "scientific_name": species_data.get("scientific_name"),
                "kingdom": species_data.get("kingdom"),
                "phylum": species_data.get("phylum"),
                "class": species_data.get("class"),
                "order": species_data.get("order"),
                "family": species_data.get("family"),
                "genus": species_data.get("genus"),
                "main_common_name": species_data.get("main_common_name"),
                "category": species_data.get("category"),
                "category_name": self.CONSERVATION_STATUS.get(
                    species_data.get("category"), {}
                ).get("name", ""),
                "criteria": species_data.get("criteria"),
                "population_trend": species_data.get("population_trend"),
                "marine_system": species_data.get("marine_system"),
                "freshwater_system": species_data.get("freshwater_system"),
                "terrestrial_system": species_data.get("terrestrial_system"),
                "assessor": species_data.get("assessor"),
                "reviewer": species_data.get("reviewer"),
                "assessment_date": species_data.get("assessment_date"),
                "threats": threats,
                "conservation_measures": conservation_measures,
                "habitats": habitats
            }

        except Exception as e:
            logger.error(f"IUCN conservation status error: {str(e)}")
            raise

    async def _get_species_threats(self, taxon_id: int) -> List[Dict]:
        """종에 대한 위협 요인 조회"""
        try:
            url = self._get_url(f"threats/species/id/{taxon_id}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "code": t.get("code"),
                    "title": t.get("title"),
                    "timing": t.get("timing"),
                    "scope": t.get("scope"),
                    "severity": t.get("severity"),
                    "score": t.get("score"),
                    "invasive": t.get("invasive")
                }
                for t in data.get("result", [])
            ]
        except:
            return []

    async def _get_conservation_measures(self, taxon_id: int) -> List[Dict]:
        """보전 조치 조회"""
        try:
            url = self._get_url(f"measures/species/id/{taxon_id}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "code": m.get("code"),
                    "title": m.get("title")
                }
                for m in data.get("result", [])
            ]
        except:
            return []

    async def _get_species_habitats(self, taxon_id: int) -> List[Dict]:
        """서식지 정보 조회"""
        try:
            url = self._get_url(f"habitats/species/id/{taxon_id}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "code": h.get("code"),
                    "habitat": h.get("habitat"),
                    "suitability": h.get("suitability"),
                    "season": h.get("season"),
                    "major_importance": h.get("majorimportance")
                }
                for h in data.get("result", [])
            ]
        except:
            return []

    # =========================================================================
    # 지역별 평가
    # =========================================================================
    async def get_regional_assessment(
        self,
        country_code: str
    ) -> Dict:
        """
        국가별 멸종위기종 평가

        Args:
            country_code: ISO 국가 코드

        Returns:
            지역 평가 통계
        """
        try:
            if not self.api_key:
                return {}

            url = self._get_url(f"country/getspecies/{country_code}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            species_list = data.get("result", [])

            # 카테고리별 통계
            category_counts = {}
            for species in species_list:
                cat = species.get("category", "NE")
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # 위험 종 수 계산
            endangered_count = sum([
                category_counts.get("CR", 0),
                category_counts.get("EN", 0),
                category_counts.get("VU", 0)
            ])

            return {
                "country_code": country_code,
                "total_assessed": len(species_list),
                "endangered_count": endangered_count,
                "by_category": category_counts,
                "critically_endangered": category_counts.get("CR", 0),
                "endangered": category_counts.get("EN", 0),
                "vulnerable": category_counts.get("VU", 0),
                "near_threatened": category_counts.get("NT", 0),
                "least_concern": category_counts.get("LC", 0),
                "data_deficient": category_counts.get("DD", 0),
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"IUCN regional assessment error: {str(e)}")
            raise

    # =========================================================================
    # 국가별 종 목록
    # =========================================================================
    async def get_country_species(
        self,
        country_code: str,
        page: int = 0
    ) -> List[Dict]:
        """국가별 평가된 종 목록"""
        try:
            if not self.api_key:
                return []

            url = self._get_url(f"country/getspecies/{country_code}")
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            species_list = []
            for species in data.get("result", []):
                species_list.append(self._transform_species(species))

            logger.info(f"IUCN species for {country_code}: {len(species_list)}")
            return species_list

        except Exception as e:
            logger.error(f"IUCN country species error: {str(e)}")
            raise

    # =========================================================================
    # 학명으로 검색
    # =========================================================================
    async def search_by_name(self, name: str) -> List[Dict]:
        """학명으로 종 검색"""
        try:
            if not self.api_key:
                return []

            url = self._get_url(f"species/{name}")
            response = await self.client.get(url)

            if response.status_code == 404:
                return []

            response.raise_for_status()
            data = response.json()

            return [
                self._transform_species(s)
                for s in data.get("result", [])
            ]

        except Exception as e:
            logger.error(f"IUCN search error: {str(e)}")
            return []

    # =========================================================================
    # 유틸리티
    # =========================================================================
    def _transform_species(self, iucn_data: Dict) -> Dict:
        """IUCN 데이터를 표준 형식으로 변환"""
        category = iucn_data.get("category", "NE")
        status_info = self.CONSERVATION_STATUS.get(category, {})

        return {
            "taxon_id": iucn_data.get("taxonid"),
            "scientific_name": iucn_data.get("scientific_name"),
            "common_name": iucn_data.get("main_common_name", ""),
            "kingdom": iucn_data.get("kingdom", ""),
            "phylum": iucn_data.get("phylum", ""),
            "class": iucn_data.get("class", ""),
            "order": iucn_data.get("order", ""),
            "family": iucn_data.get("family", ""),
            "genus": iucn_data.get("genus", ""),
            "category_code": category,
            "category_name": status_info.get("name", ""),
            "category_name_en": status_info.get("name_en", ""),
            "priority": status_info.get("priority", 9),
            "population_trend": iucn_data.get("population_trend", ""),
            "assessment_date": iucn_data.get("assessment_date", "")
        }

    def get_status_name(self, code: str) -> str:
        """상태 코드를 한글 이름으로 변환"""
        return self.CONSERVATION_STATUS.get(code, {}).get("name", "미평가")


# 싱글톤 인스턴스
iucn_service = IUCNService()
