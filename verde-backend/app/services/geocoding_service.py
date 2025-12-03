"""
Geocoding 서비스 - 좌표를 국가로 변환

좌표(위도, 경도)를 받아 해당 위치의 국가를 식별합니다.
Nominatim (OpenStreetMap) 무료 서비스를 사용합니다.
"""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from typing import Optional
import time


class GeocodingService:
    """좌표 기반 국가 식별 서비스"""

    def __init__(self):
        # Nominatim geocoder 초기화 (User-Agent 필수)
        self.geolocator = Nominatim(user_agent="verde-biodiversity-app/1.0")
        self.cache = {}  # 간단한 캐시

    def get_country_from_coordinates(self, lat: float, lng: float) -> Optional[str]:
        """
        좌표로부터 국가 코드 얻기

        Args:
            lat: 위도 (-90 ~ 90)
            lng: 경도 (-180 ~ 180)

        Returns:
            국가 코드 (소문자) 또는 None

        Examples:
            >>> get_country_from_coordinates(37.5665, 126.9780)  # 서울
            'korea'
            >>> get_country_from_coordinates(40.7128, -74.0060)  # 뉴욕
            'usa'
        """
        # 캐시 확인 (좌표를 반올림하여 캐시)
        cache_key = f"{round(lat, 2)},{round(lng, 2)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Reverse geocoding: 좌표 → 주소
            location = self.geolocator.reverse(
                f"{lat}, {lng}",
                language="en",
                timeout=5
            )

            if not location or not location.raw.get('address'):
                print(f"⚠️  좌표 {lat}, {lng}에 대한 주소를 찾을 수 없습니다.")
                return None

            address = location.raw['address']

            # 국가 코드 추출
            country_code = address.get('country_code', '').lower()

            if not country_code:
                print(f"⚠️  주소에 국가 코드가 없습니다: {address}")
                return None

            # 국가 코드를 데이터베이스 형식으로 매핑
            country_mapping = self._map_country_code(country_code)

            # 캐시에 저장
            self.cache[cache_key] = country_mapping

            print(f"✅ 좌표 ({lat}, {lng}) → 국가: {country_mapping}")
            return country_mapping

        except GeocoderTimedOut:
            print(f"❌ Geocoding 시간 초과: ({lat}, {lng})")
            return None
        except GeocoderServiceError as e:
            print(f"❌ Geocoding 서비스 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return None

    def _map_country_code(self, iso_code: str) -> str:
        """
        ISO 국가 코드를 데이터베이스 국가 이름으로 매핑

        Args:
            iso_code: ISO 3166-1 alpha-2 국가 코드 (예: 'kr', 'us', 'jp')

        Returns:
            데이터베이스 국가 이름 (예: 'korea', 'usa', 'japan')
        """
        mapping = {
            # 아시아
            'kr': 'korea',
            'jp': 'japan',
            'cn': 'china',
            'in': 'india',

            # 북미
            'us': 'usa',
            'ca': 'canada',
            'mx': 'mexico',

            # 유럽
            'ru': 'russia',
            'gb': 'uk',
            'de': 'germany',
            'fr': 'france',

            # 남미
            'br': 'brazil',
            'ar': 'argentina',

            # 아프리카
            'za': 'southafrica',
            'ke': 'kenya',

            # 오세아니아
            'au': 'australia',
            'nz': 'newzealand',
        }

        # 매핑된 국가 반환, 없으면 원본 코드 반환
        return mapping.get(iso_code, iso_code)


# 전역 인스턴스
geocoding_service = GeocodingService()
