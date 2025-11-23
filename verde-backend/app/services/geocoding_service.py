"""
Nominatim 기반 지오코딩 서비스
OpenStreetMap의 무료 지오코딩 API 사용
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
import httpx

from app.cache import cache_get, cache_set

logger = logging.getLogger(__name__)


class GeocodingService:
    """Nominatim 지오코딩 서비스"""

    BASE_URL = "https://nominatim.openstreetmap.org"

    # Nominatim 사용 정책: 1초당 1요청
    RATE_LIMIT_DELAY = 1.0

    # 캐시 TTL (24시간 - 지명은 자주 변경되지 않음)
    CACHE_TTL = 86400

    def __init__(self):
        self._last_request_time = 0
        self.headers = {
            "User-Agent": "Verde-Biodiversity-App/1.0 (contact@verde.app)"
        }

    async def _rate_limit(self):
        """Nominatim rate limiting 준수"""
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self._last_request_time

        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    async def get_coordinates(self, place_name: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        지명으로 위도/경도 검색

        Args:
            place_name: 검색할 지명
            country_code: 국가 코드 (ISO 3166-1 alpha-2)

        Returns:
            {
                "lat": float,
                "lon": float,
                "display_name": str,
                "type": str,
                "importance": float,
                "boundingbox": [south, north, west, east]
            }
        """
        # 캐시 확인
        cache_key = f"geocode:forward:{place_name}:{country_code or 'all'}"
        cached = cache_get(cache_key)
        if cached:
            logger.debug(f"Geocoding cache hit: {place_name}")
            return cached

        await self._rate_limit()

        params = {
            "q": place_name,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }

        if country_code:
            params["countrycodes"] = country_code.lower()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()

                results = response.json()

                if not results:
                    logger.info(f"No geocoding results for: {place_name}")
                    return None

                result = results[0]

                geocode_data = {
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "display_name": result.get("display_name", ""),
                    "type": result.get("type", ""),
                    "class": result.get("class", ""),
                    "importance": float(result.get("importance", 0)),
                    "boundingbox": [float(x) for x in result.get("boundingbox", [])],
                    "address": result.get("address", {})
                }

                # 캐시 저장
                cache_set(cache_key, geocode_data, self.CACHE_TTL)

                logger.info(f"Geocoded '{place_name}' -> ({geocode_data['lat']}, {geocode_data['lon']})")
                return geocode_data

        except httpx.HTTPStatusError as e:
            logger.error(f"Geocoding HTTP error for '{place_name}': {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Geocoding error for '{place_name}': {str(e)}")
            return None

    async def reverse_geocode(self, lat: float, lon: float, zoom: int = 18) -> Optional[Dict[str, Any]]:
        """
        위도/경도로 지명 검색

        Args:
            lat: 위도
            lon: 경도
            zoom: 상세 수준 (3=국가, 10=도시, 18=건물)

        Returns:
            {
                "display_name": str,
                "address": {
                    "country": str,
                    "state": str,
                    "city": str,
                    ...
                },
                "type": str
            }
        """
        # 캐시 확인 (소수점 4자리로 반올림하여 캐시 키 생성)
        lat_key = round(lat, 4)
        lon_key = round(lon, 4)
        cache_key = f"geocode:reverse:{lat_key}:{lon_key}:{zoom}"
        cached = cache_get(cache_key)
        if cached:
            logger.debug(f"Reverse geocoding cache hit: ({lat}, {lon})")
            return cached

        await self._rate_limit()

        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": zoom,
            "addressdetails": 1
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/reverse",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()

                result = response.json()

                if "error" in result:
                    logger.info(f"No reverse geocoding results for: ({lat}, {lon})")
                    return None

                geocode_data = {
                    "display_name": result.get("display_name", ""),
                    "address": result.get("address", {}),
                    "type": result.get("type", ""),
                    "class": result.get("class", ""),
                    "lat": float(result.get("lat", lat)),
                    "lon": float(result.get("lon", lon)),
                    "boundingbox": [float(x) for x in result.get("boundingbox", [])]
                }

                # 캐시 저장
                cache_set(cache_key, geocode_data, self.CACHE_TTL)

                logger.info(f"Reverse geocoded ({lat}, {lon}) -> {geocode_data['display_name'][:50]}")
                return geocode_data

        except httpx.HTTPStatusError as e:
            logger.error(f"Reverse geocoding HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Reverse geocoding error: {str(e)}")
            return None

    async def search_places(
        self,
        query: str,
        limit: int = 5,
        country_code: Optional[str] = None,
        viewbox: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        여러 장소 검색 (자동완성용)

        Args:
            query: 검색어
            limit: 결과 개수 (최대 10)
            country_code: 국가 필터
            viewbox: 검색 영역 제한 [west, south, east, north]

        Returns:
            장소 목록
        """
        # 캐시 확인
        cache_key = f"geocode:search:{query}:{limit}:{country_code or 'all'}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        await self._rate_limit()

        params = {
            "q": query,
            "format": "json",
            "limit": min(limit, 10),
            "addressdetails": 1
        }

        if country_code:
            params["countrycodes"] = country_code.lower()

        if viewbox:
            params["viewbox"] = ",".join(map(str, viewbox))
            params["bounded"] = 1

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()

                results = response.json()

                places = []
                for result in results:
                    places.append({
                        "lat": float(result["lat"]),
                        "lon": float(result["lon"]),
                        "display_name": result.get("display_name", ""),
                        "type": result.get("type", ""),
                        "class": result.get("class", ""),
                        "importance": float(result.get("importance", 0)),
                        "address": result.get("address", {})
                    })

                # 캐시 저장 (1시간)
                cache_set(cache_key, places, 3600)

                return places

        except Exception as e:
            logger.error(f"Place search error: {str(e)}")
            return []

    async def get_country_bounds(self, country_code: str) -> Optional[Dict[str, Any]]:
        """
        국가의 경계 박스 가져오기

        Args:
            country_code: ISO 3166-1 alpha-2 국가 코드

        Returns:
            {
                "north": float,
                "south": float,
                "east": float,
                "west": float,
                "center": {"lat": float, "lon": float}
            }
        """
        # 국가 이름으로 검색
        country_names = {
            "KR": "South Korea",
            "JP": "Japan",
            "US": "United States",
            "CN": "China",
            "RU": "Russia",
            "BR": "Brazil",
            "AU": "Australia",
            "DE": "Germany",
            "FR": "France",
            "GB": "United Kingdom"
        }

        country_name = country_names.get(country_code.upper(), country_code)

        # 캐시 확인
        cache_key = f"geocode:country_bounds:{country_code}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        result = await self.get_coordinates(country_name)

        if result and result.get("boundingbox"):
            bbox = result["boundingbox"]
            bounds = {
                "south": bbox[0],
                "north": bbox[1],
                "west": bbox[2],
                "east": bbox[3],
                "center": {
                    "lat": result["lat"],
                    "lon": result["lon"]
                }
            }

            # 국가 경계는 오래 캐시 (7일)
            cache_set(cache_key, bounds, 604800)

            return bounds

        return None


# 싱글톤 인스턴스
geocoding_service = GeocodingService()
