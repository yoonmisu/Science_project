"""
이미지 서비스 - 외부 API를 통해 실제 생물 종 사진 가져오기
"""
import requests
from typing import Optional
import urllib.parse


class ImageService:
    """생물 종 이미지를 외부 API에서 가져오는 서비스"""

    @staticmethod
    def get_wikimedia_image(species_name: str, scientific_name: Optional[str] = None) -> Optional[str]:
        """
        Wikimedia Commons에서 생물 종 이미지 URL 가져오기

        Args:
            species_name: 종의 일반 이름 (예: "호랑이")
            scientific_name: 학명 (예: "Panthera tigris") - 있으면 더 정확한 결과

        Returns:
            이미지 URL 또는 None
        """
        try:
            # 학명이 있으면 우선 사용, 없으면 일반 이름 사용
            search_term = scientific_name if scientific_name else species_name

            # Wikimedia Commons API로 이미지 검색
            api_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"{search_term}",
                "gsrnamespace": "6",  # File namespace
                "gsrlimit": "1",
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": "400"
            }

            response = requests.get(api_url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # 검색 결과에서 첫 번째 이미지 URL 추출
                if "query" in data and "pages" in data["query"]:
                    pages = data["query"]["pages"]
                    first_page = next(iter(pages.values()))

                    if "imageinfo" in first_page:
                        image_info = first_page["imageinfo"][0]
                        # thumburl (썸네일) 또는 url (원본) 반환
                        return image_info.get("thumburl") or image_info.get("url")

            return None

        except Exception:
            return None

    @staticmethod
    def get_inaturalist_image(species_name: str, scientific_name: Optional[str] = None) -> Optional[str]:
        """
        iNaturalist API에서 생물 종 이미지 URL 가져오기

        Args:
            species_name: 종의 일반 이름
            scientific_name: 학명

        Returns:
            이미지 URL 또는 None
        """
        try:
            search_term = scientific_name if scientific_name else species_name

            # iNaturalist API로 종 검색
            api_url = "https://api.inaturalist.org/v1/taxa"
            params = {
                "q": search_term,
                "per_page": 1
            }

            response = requests.get(api_url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data.get("results") and len(data["results"]) > 0:
                    taxon = data["results"][0]

                    # 기본 사진 URL 반환
                    if "default_photo" in taxon and taxon["default_photo"]:
                        photo = taxon["default_photo"]
                        return photo.get("medium_url") or photo.get("url")

            return None

        except Exception:
            return None

    @staticmethod
    def get_species_image(species_name: str, scientific_name: Optional[str] = None) -> str:
        """
        여러 소스를 시도하여 생물 종 이미지 가져오기

        우선순위:
        1. Wikimedia Commons
        2. iNaturalist
        3. 기본 이모지 아이콘

        Args:
            species_name: 종의 일반 이름
            scientific_name: 학명 (선택)

        Returns:
            이미지 URL (실패시 기본 이모지)
        """
        # 1. Wikimedia 시도
        image_url = ImageService.get_wikimedia_image(species_name, scientific_name)
        if image_url:
            return image_url

        # 2. iNaturalist 시도
        image_url = ImageService.get_inaturalist_image(species_name, scientific_name)
        if image_url:
            return image_url

        # 3. 기본 아이콘 반환
        return "🦎"  # 기본 생물 아이콘


# 전역 인스턴스
image_service = ImageService()
