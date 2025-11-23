"""
iNaturalist API 통합 서비스
https://api.inaturalist.org/v1/docs/
"""
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class INaturalistService:
    """iNaturalist API 클라이언트"""

    BASE_URL = "https://api.inaturalist.org/v1"

    # 주요 지역 Place ID
    PLACE_IDS = {
        "KR": 7161,      # South Korea
        "US": 1,         # United States
        "JP": 6737,      # Japan
        "CN": 6903,      # China
        "GB": 6857,      # United Kingdom
        "AU": 6744,      # Australia
        "DE": 7207,      # Germany
        "FR": 6753,      # France
        "BR": 6878,      # Brazil
        "IN": 6681       # India
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def close(self):
        await self.client.aclose()

    # =========================================================================
    # 사진이 있는 관찰 기록
    # =========================================================================
    async def fetch_observations_with_photos(
        self,
        place_id: int,
        taxon_id: Optional[int] = None,
        quality_grade: str = "research",
        limit: int = 100,
        page: int = 1
    ) -> List[Dict]:
        """
        사진이 있는 생물 관찰 기록 가져오기

        Args:
            place_id: iNaturalist 지역 ID
            taxon_id: 특정 분류군 ID (선택)
            quality_grade: 품질 등급 (research, needs_id, casual)
            limit: 결과 수
            page: 페이지 번호

        Returns:
            관찰 기록 리스트
        """
        try:
            url = f"{self.BASE_URL}/observations"
            params = {
                "place_id": place_id,
                "photos": True,
                "quality_grade": quality_grade,
                "per_page": limit,
                "page": page,
                "order": "desc",
                "order_by": "votes"
            }

            if taxon_id:
                params["taxon_id"] = taxon_id

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            observations = []
            for result in data.get("results", []):
                obs = self._transform_observation(result)
                observations.append(obs)

            logger.info(f"iNaturalist observations for place {place_id}: {len(observations)}")
            return observations

        except Exception as e:
            logger.error(f"iNaturalist observations error: {str(e)}")
            raise

    # =========================================================================
    # 인기 생물종
    # =========================================================================
    async def get_popular_species(
        self,
        place_id: int,
        limit: int = 50,
        iconic_taxa: Optional[str] = None
    ) -> List[Dict]:
        """
        지역별 인기 생물종 (관찰 횟수 기준)

        Args:
            place_id: iNaturalist 지역 ID
            limit: 결과 수
            iconic_taxa: 분류군 필터 (Plantae, Animalia, Insecta 등)

        Returns:
            인기 종 리스트
        """
        try:
            url = f"{self.BASE_URL}/observations/species_counts"
            params = {
                "place_id": place_id,
                "per_page": limit,
                "quality_grade": "research"
            }

            if iconic_taxa:
                params["iconic_taxa"] = iconic_taxa

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            species_list = []
            for result in data.get("results", []):
                taxon = result.get("taxon", {})
                species_list.append({
                    "taxon_id": taxon.get("id"),
                    "name": taxon.get("preferred_common_name") or taxon.get("name"),
                    "scientific_name": taxon.get("name"),
                    "rank": taxon.get("rank"),
                    "observation_count": result.get("count", 0),
                    "iconic_taxon": taxon.get("iconic_taxon_name"),
                    "photo_url": self._get_best_photo_url(taxon),
                    "wikipedia_url": taxon.get("wikipedia_url"),
                    "conservation_status": taxon.get("conservation_status")
                })

            logger.info(f"iNaturalist popular species for place {place_id}: {len(species_list)}")
            return species_list

        except Exception as e:
            logger.error(f"iNaturalist popular species error: {str(e)}")
            raise

    # =========================================================================
    # 이름으로 검색
    # =========================================================================
    async def search_by_common_name(
        self,
        name: str,
        locale: str = "ko",
        limit: int = 20
    ) -> List[Dict]:
        """
        한글 이름으로 검색

        Args:
            name: 검색어 (한글 또는 영문)
            locale: 언어 코드 (ko, en, ja 등)
            limit: 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            url = f"{self.BASE_URL}/taxa/autocomplete"
            params = {
                "q": name,
                "per_page": limit,
                "locale": locale,
                "preferred_place_id": self.PLACE_IDS.get("KR", 7161)
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for taxon in data.get("results", []):
                results.append({
                    "taxon_id": taxon.get("id"),
                    "name": taxon.get("preferred_common_name") or taxon.get("name"),
                    "scientific_name": taxon.get("name"),
                    "rank": taxon.get("rank"),
                    "iconic_taxon": taxon.get("iconic_taxon_name"),
                    "photo_url": self._get_best_photo_url(taxon),
                    "observations_count": taxon.get("observations_count", 0),
                    "matched_term": taxon.get("matched_term"),
                    "is_active": taxon.get("is_active", True)
                })

            logger.info(f"iNaturalist search '{name}': {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"iNaturalist search error: {str(e)}")
            raise

    # =========================================================================
    # 종 상세 정보
    # =========================================================================
    async def get_taxon_details(self, taxon_id: int) -> Dict:
        """특정 분류군의 상세 정보"""
        try:
            url = f"{self.BASE_URL}/taxa/{taxon_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            result = data.get("results", [{}])[0]

            return {
                "taxon_id": result.get("id"),
                "name": result.get("preferred_common_name") or result.get("name"),
                "scientific_name": result.get("name"),
                "rank": result.get("rank"),
                "iconic_taxon": result.get("iconic_taxon_name"),
                "ancestry": result.get("ancestry"),
                "wikipedia_summary": result.get("wikipedia_summary"),
                "wikipedia_url": result.get("wikipedia_url"),
                "photos": [
                    {
                        "url": p.get("url"),
                        "medium_url": p.get("medium_url"),
                        "small_url": p.get("small_url"),
                        "attribution": p.get("attribution")
                    }
                    for p in result.get("taxon_photos", [])
                ],
                "conservation_status": result.get("conservation_status"),
                "observations_count": result.get("observations_count", 0)
            }

        except Exception as e:
            logger.error(f"iNaturalist taxon detail error: {str(e)}")
            raise

    # =========================================================================
    # 지역별 통계
    # =========================================================================
    async def get_place_statistics(self, place_id: int) -> Dict:
        """지역별 생물 다양성 통계"""
        try:
            # 전체 관찰 수
            obs_url = f"{self.BASE_URL}/observations"
            obs_params = {
                "place_id": place_id,
                "quality_grade": "research",
                "per_page": 0
            }
            obs_response = await self.client.get(obs_url, params=obs_params)
            obs_data = obs_response.json()

            # 종 수
            species_url = f"{self.BASE_URL}/observations/species_counts"
            species_params = {
                "place_id": place_id,
                "quality_grade": "research",
                "per_page": 0
            }
            species_response = await self.client.get(species_url, params=species_params)
            species_data = species_response.json()

            # 카테고리별 통계
            categories = {}
            for iconic in ["Plantae", "Animalia", "Insecta", "Aves", "Mammalia", "Reptilia", "Amphibia", "Actinopterygii"]:
                cat_params = {
                    "place_id": place_id,
                    "iconic_taxa": iconic,
                    "quality_grade": "research",
                    "per_page": 0
                }
                cat_response = await self.client.get(species_url, params=cat_params)
                cat_data = cat_response.json()
                categories[iconic] = cat_data.get("total_results", 0)

            return {
                "place_id": place_id,
                "total_observations": obs_data.get("total_results", 0),
                "total_species": species_data.get("total_results", 0),
                "by_iconic_taxa": categories,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"iNaturalist statistics error: {str(e)}")
            raise

    # =========================================================================
    # 좌표 기반 검색
    # =========================================================================
    async def fetch_observations_by_coordinates(
        self,
        lat: float,
        lon: float,
        radius_km: int = 50,
        limit: int = 100
    ) -> List[Dict]:
        """좌표 기반 주변 관찰 기록"""
        try:
            url = f"{self.BASE_URL}/observations"
            params = {
                "lat": lat,
                "lng": lon,
                "radius": radius_km,
                "photos": True,
                "quality_grade": "research",
                "per_page": limit,
                "order_by": "observed_on"
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            observations = []
            for result in data.get("results", []):
                obs = self._transform_observation(result)
                observations.append(obs)

            return observations

        except Exception as e:
            logger.error(f"iNaturalist coordinate search error: {str(e)}")
            raise

    # =========================================================================
    # 유틸리티
    # =========================================================================
    def _transform_observation(self, obs_data: Dict) -> Dict:
        """관찰 데이터 변환"""
        taxon = obs_data.get("taxon", {})
        photos = obs_data.get("photos", [])

        return {
            "observation_id": obs_data.get("id"),
            "observed_on": obs_data.get("observed_on"),
            "place_guess": obs_data.get("place_guess"),
            "latitude": obs_data.get("geojson", {}).get("coordinates", [None, None])[1],
            "longitude": obs_data.get("geojson", {}).get("coordinates", [None, None])[0],
            "taxon": {
                "id": taxon.get("id"),
                "name": taxon.get("preferred_common_name") or taxon.get("name"),
                "scientific_name": taxon.get("name"),
                "rank": taxon.get("rank"),
                "iconic_taxon": taxon.get("iconic_taxon_name")
            },
            "photos": [
                {
                    "url": p.get("url"),
                    "medium_url": p.get("url", "").replace("square", "medium"),
                    "large_url": p.get("url", "").replace("square", "large"),
                    "attribution": p.get("attribution")
                }
                for p in photos[:5]  # 최대 5장
            ],
            "quality_grade": obs_data.get("quality_grade"),
            "species_guess": obs_data.get("species_guess"),
            "user": {
                "id": obs_data.get("user", {}).get("id"),
                "login": obs_data.get("user", {}).get("login")
            }
        }

    def _get_best_photo_url(self, taxon: Dict) -> Optional[str]:
        """최적의 사진 URL 추출"""
        if taxon.get("default_photo"):
            return taxon["default_photo"].get("medium_url") or taxon["default_photo"].get("url")

        photos = taxon.get("taxon_photos", [])
        if photos:
            photo = photos[0].get("photo", {})
            return photo.get("medium_url") or photo.get("url")

        return None

    def get_place_id(self, country_code: str) -> Optional[int]:
        """국가 코드로 Place ID 조회"""
        return self.PLACE_IDS.get(country_code.upper())


# 싱글톤 인스턴스
inaturalist_service = INaturalistService()
