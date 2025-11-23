"""
GBIF (Global Biodiversity Information Facility) API 통합 서비스
https://www.gbif.org/developer/summary
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GBIFService:
    """GBIF API 클라이언트"""

    BASE_URL = "https://api.gbif.org/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def close(self):
        await self.client.aclose()

    # =========================================================================
    # 국가별 생물종 검색
    # =========================================================================
    async def fetch_species_by_region(
        self,
        country_code: str,
        limit: int = 100,
        offset: int = 0,
        taxon_key: Optional[int] = None
    ) -> List[Dict]:
        """
        국가 코드로 생물종 검색

        Args:
            country_code: ISO 국가 코드 (예: 'KR', 'US', 'JP')
            limit: 결과 수 제한
            offset: 페이지 오프셋
            taxon_key: 특정 분류군 필터

        Returns:
            Species 모델 형식의 데이터 리스트
        """
        try:
            url = f"{self.BASE_URL}/occurrence/search"
            params = {
                "country": country_code,
                "limit": limit,
                "offset": offset,
                "hasCoordinate": True,
                "hasGeospatialIssue": False,
                "occurrenceStatus": "PRESENT"
            }

            if taxon_key:
                params["taxonKey"] = taxon_key

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            species_list = []
            seen_species = set()

            for result in data.get("results", []):
                species_name = result.get("species") or result.get("scientificName")
                if species_name and species_name not in seen_species:
                    seen_species.add(species_name)
                    species = self._transform_gbif_to_species(result, country_code)
                    species_list.append(species)

            logger.info(f"GBIF fetch for {country_code}: {len(species_list)} unique species")
            return species_list

        except Exception as e:
            logger.error(f"GBIF fetch error for {country_code}: {str(e)}")
            raise

    # =========================================================================
    # 좌표 기반 검색
    # =========================================================================
    async def fetch_species_by_coordinates(
        self,
        lat: float,
        lon: float,
        radius_km: int = 50,
        limit: int = 100
    ) -> List[Dict]:
        """
        위도/경도 기반 주변 생물종 검색

        Args:
            lat: 위도
            lon: 경도
            radius_km: 검색 반경 (km)
            limit: 결과 수 제한

        Returns:
            Species 모델 형식의 데이터 리스트
        """
        try:
            url = f"{self.BASE_URL}/occurrence/search"

            # WKT 형식으로 원형 영역 정의 (근사치로 사각형 사용)
            # 위도 1도 ≈ 111km
            lat_delta = radius_km / 111.0
            lon_delta = radius_km / (111.0 * abs(cos_deg(lat)))

            geometry = (
                f"POLYGON(("
                f"{lon - lon_delta} {lat - lat_delta},"
                f"{lon + lon_delta} {lat - lat_delta},"
                f"{lon + lon_delta} {lat + lat_delta},"
                f"{lon - lon_delta} {lat + lat_delta},"
                f"{lon - lon_delta} {lat - lat_delta}"
                f"))"
            )

            params = {
                "geometry": geometry,
                "limit": limit,
                "hasCoordinate": True,
                "hasGeospatialIssue": False
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            species_list = []
            seen_species = set()

            for result in data.get("results", []):
                species_name = result.get("species")
                if species_name and species_name not in seen_species:
                    seen_species.add(species_name)
                    species = self._transform_gbif_to_species(result)
                    species_list.append(species)

            logger.info(f"GBIF coordinate search ({lat}, {lon}): {len(species_list)} species")
            return species_list

        except Exception as e:
            logger.error(f"GBIF coordinate search error: {str(e)}")
            raise

    # =========================================================================
    # 생물 다양성 통계
    # =========================================================================
    async def get_biodiversity_statistics(self, country_code: str) -> Dict:
        """
        국가별 생물 다양성 통계

        Args:
            country_code: ISO 국가 코드

        Returns:
            통계 데이터 딕셔너리
        """
        try:
            # 총 종 수
            total_url = f"{self.BASE_URL}/occurrence/search"
            total_params = {
                "country": country_code,
                "limit": 0,
                "facet": "speciesKey",
                "facetLimit": 0
            }

            total_response = await self.client.get(total_url, params=total_params)
            total_data = total_response.json()
            total_species = total_data.get("count", 0)

            # 카테고리별 통계
            categories = {
                "식물": 6,      # Plantae kingdom key
                "동물": 1,      # Animalia kingdom key
                "곤충": 212,    # Insecta class key
                "균류": 5       # Fungi kingdom key
            }

            category_stats = {}
            for category_name, taxon_key in categories.items():
                cat_params = {
                    "country": country_code,
                    "taxonKey": taxon_key,
                    "limit": 0
                }
                cat_response = await self.client.get(total_url, params=cat_params)
                cat_data = cat_response.json()
                category_stats[category_name] = cat_data.get("count", 0)

            # 멸종위기종 (IUCN status가 있는 종)
            endangered_params = {
                "country": country_code,
                "iucnRedListCategory": ["CR", "EN", "VU"],
                "limit": 0
            }
            endangered_response = await self.client.get(total_url, params=endangered_params)
            endangered_data = endangered_response.json()
            endangered_count = endangered_data.get("count", 0)

            stats = {
                "country_code": country_code,
                "total_occurrences": total_species,
                "endangered_count": endangered_count,
                "by_category": category_stats,
                "last_updated": datetime.utcnow().isoformat()
            }

            logger.info(f"GBIF statistics for {country_code}: {total_species} total")
            return stats

        except Exception as e:
            logger.error(f"GBIF statistics error for {country_code}: {str(e)}")
            raise

    # =========================================================================
    # 이름으로 검색
    # =========================================================================
    async def search_species_by_name(
        self,
        name: str,
        fuzzy: bool = True,
        limit: int = 20
    ) -> List[Dict]:
        """
        생물명으로 검색 (한글/영문/학명)

        Args:
            name: 검색어
            fuzzy: Fuzzy matching 사용 여부
            limit: 결과 수 제한

        Returns:
            검색 결과 리스트
        """
        try:
            url = f"{self.BASE_URL}/species/search"
            params = {
                "q": name,
                "limit": limit,
                "rank": "SPECIES"
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "gbif_key": item.get("key"),
                    "scientific_name": item.get("scientificName"),
                    "canonical_name": item.get("canonicalName"),
                    "vernacular_names": item.get("vernacularNames", []),
                    "kingdom": item.get("kingdom"),
                    "phylum": item.get("phylum"),
                    "class": item.get("class"),
                    "order": item.get("order"),
                    "family": item.get("family"),
                    "genus": item.get("genus"),
                    "status": item.get("taxonomicStatus"),
                    "match_type": item.get("matchType", "EXACT")
                })

            # Fuzzy search가 실패하면 suggest API 사용
            if fuzzy and len(results) == 0:
                suggest_url = f"{self.BASE_URL}/species/suggest"
                suggest_params = {"q": name, "limit": limit}
                suggest_response = await self.client.get(suggest_url, params=suggest_params)
                suggest_data = suggest_response.json()

                for item in suggest_data:
                    results.append({
                        "gbif_key": item.get("key"),
                        "scientific_name": item.get("scientificName"),
                        "canonical_name": item.get("canonicalName"),
                        "vernacular_names": [],
                        "kingdom": item.get("kingdom"),
                        "rank": item.get("rank"),
                        "match_type": "FUZZY"
                    })

            logger.info(f"GBIF name search '{name}': {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"GBIF name search error: {str(e)}")
            raise

    # =========================================================================
    # 종 상세 정보
    # =========================================================================
    async def get_species_details(self, gbif_key: int) -> Dict:
        """GBIF 종 상세 정보"""
        try:
            response = await self.client.get(f"{self.BASE_URL}/species/{gbif_key}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"GBIF species detail error: {str(e)}")
            raise

    async def get_species_media(self, gbif_key: int, limit: int = 10) -> List[Dict]:
        """종 이미지/미디어 조회"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/species/{gbif_key}/media",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            media = []
            for item in data.get("results", []):
                if item.get("type") == "StillImage":
                    media.append({
                        "url": item.get("identifier"),
                        "title": item.get("title"),
                        "creator": item.get("creator"),
                        "license": item.get("license"),
                        "publisher": item.get("publisher")
                    })

            return media
        except Exception as e:
            logger.error(f"GBIF media error: {str(e)}")
            raise

    async def get_species_vernacular_names(self, gbif_key: int) -> List[Dict]:
        """종의 일반명(각 언어별 이름) 조회"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/species/{gbif_key}/vernacularNames"
            )
            response.raise_for_status()
            data = response.json()

            names = []
            for item in data.get("results", []):
                names.append({
                    "name": item.get("vernacularName"),
                    "language": item.get("language"),
                    "country": item.get("country"),
                    "source": item.get("source")
                })

            return names
        except Exception as e:
            logger.error(f"GBIF vernacular names error: {str(e)}")
            raise

    # =========================================================================
    # 데이터 변환 유틸리티
    # =========================================================================
    def _transform_gbif_to_species(self, gbif_data: Dict, country_code: str = None) -> Dict:
        """GBIF 응답을 Species 모델 형식으로 변환"""

        # 일반명 또는 학명 사용
        name = gbif_data.get("vernacularName") or gbif_data.get("species") or gbif_data.get("scientificName", "Unknown")

        return {
            "name": name,
            "scientific_name": gbif_data.get("scientificName", ""),
            "category": self._determine_category(gbif_data),
            "region": gbif_data.get("stateProvince", ""),
            "country": gbif_data.get("country", country_code or ""),
            "description": self._generate_description(gbif_data),
            "characteristics": {
                "kingdom": gbif_data.get("kingdom", ""),
                "phylum": gbif_data.get("phylum", ""),
                "class": gbif_data.get("class", ""),
                "order": gbif_data.get("order", ""),
                "family": gbif_data.get("family", ""),
                "genus": gbif_data.get("genus", ""),
                "gbif_key": gbif_data.get("speciesKey") or gbif_data.get("key"),
                "dataset_key": gbif_data.get("datasetKey", ""),
                "basis_of_record": gbif_data.get("basisOfRecord", "")
            },
            "latitude": gbif_data.get("decimalLatitude"),
            "longitude": gbif_data.get("decimalLongitude"),
            "conservation_status": self._map_iucn_status(gbif_data.get("iucnRedListCategory")),
            "gbif_id": gbif_data.get("key"),
            "occurrence_date": gbif_data.get("eventDate"),
            "recorded_by": gbif_data.get("recordedBy")
        }

    def _determine_category(self, gbif_data: Dict) -> str:
        """생물 분류 정보로 카테고리 결정"""
        kingdom = (gbif_data.get("kingdom") or "").lower()
        class_name = (gbif_data.get("class") or "").lower()
        phylum = (gbif_data.get("phylum") or "").lower()
        order = (gbif_data.get("order") or "").lower()

        # 식물
        if kingdom == "plantae":
            return "식물"

        # 곤충
        if "insecta" in class_name:
            return "곤충"

        # 해양생물
        marine_classes = [
            "actinopterygii",  # 조기어강
            "chondrichthyes",  # 연골어강
            "cephalopoda",     # 두족강
            "malacostraca",    # 연갑강 (새우, 게)
            "echinoidea",      # 성게강
            "asteroidea"       # 불가사리강
        ]
        if any(mc in class_name for mc in marine_classes):
            return "해양생물"

        # 동물
        if kingdom == "animalia" or phylum == "chordata":
            return "동물"

        return "기타"

    def _generate_description(self, gbif_data: Dict) -> str:
        """분류 정보로 설명 생성"""
        parts = []

        family = gbif_data.get("family")
        if family:
            parts.append(f"{family}과에 속하는 생물")

        order = gbif_data.get("order")
        if order:
            parts.append(f"{order}목")

        if not parts:
            kingdom = gbif_data.get("kingdom", "")
            parts.append(f"{kingdom} 계통의 생물")

        return ". ".join(parts)

    def _map_iucn_status(self, status: str) -> Optional[str]:
        """IUCN 상태를 한글로 매핑"""
        if not status:
            return None

        status_map = {
            "CR": "멸종위기",
            "EN": "멸종위기",
            "VU": "취약",
            "NT": "준위협",
            "LC": "관심대상",
            "DD": "정보부족",
            "NE": None
        }

        return status_map.get(status.upper())


def cos_deg(degrees: float) -> float:
    """도 단위 코사인 계산"""
    import math
    return math.cos(math.radians(degrees))


# 싱글톤 인스턴스
gbif_service = GBIFService()
