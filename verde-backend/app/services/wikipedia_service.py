import httpx
from typing import Optional, Dict, Any

class WikipediaService:
    # 지원하는 언어 코드 매핑 (ISO 639-1)
    SUPPORTED_LANGUAGES = {
        'ko': 'ko',  # 한국어
        'en': 'en',  # 영어
        'ja': 'ja',  # 일본어
        'zh': 'zh',  # 중국어
        'es': 'es',  # 스페인어
        'fr': 'fr',  # 프랑스어
        'de': 'de',  # 독일어
        'pt': 'pt',  # 포르투갈어
        'ru': 'ru',  # 러시아어
        'it': 'it',  # 이탈리아어
        'vi': 'vi',  # 베트남어
        'th': 'th',  # 태국어
        'id': 'id',  # 인도네시아어
    }

    def __init__(self):
        # User-Agent 헤더 추가 (Wikipedia API는 User-Agent 필수)
        headers = {
            "User-Agent": "VerdeApp/1.0 (https://github.com/verde-app/verde; verde@example.com)"
        }
        # 타임아웃을 5초로 설정하여 안정적인 응답 보장
        self.client = httpx.AsyncClient(timeout=5.0, headers=headers)

    def _get_base_url(self, lang: str = "en") -> str:
        """언어별 Wikipedia API URL 반환"""
        lang_code = self.SUPPORTED_LANGUAGES.get(lang, 'en')
        return f"https://{lang_code}.wikipedia.org/api/rest_v1/page/summary"

    async def get_species_info(self, scientific_name: str, lang: str = "en") -> Dict[str, Any]:
        """
        학명(Scientific Name)으로 Wikipedia 정보를 가져옵니다.
        이미지 URL과 요약 설명을 반환합니다.

        Args:
            scientific_name: 학명 (예: "Panthera tigris")
            lang: 언어 코드 (예: "ko", "en", "ja", "zh")

        Returns:
            {description, image_url, common_name} 또는 빈 딕셔너리
        """
        try:
            # 공백을 언더스코어로 변환
            title = scientific_name.replace(" ", "_")
            base_url = self._get_base_url(lang)
            url = f"{base_url}/{title}"

            print(f"🌐 Fetching Wikipedia ({lang}): {url}")
            response = await self.client.get(url)

            print(f"📡 Wikipedia response status: {response.status_code}")
            if response.status_code != 200:
                # 해당 언어에서 페이지를 찾지 못한 경우, 영어로 폴백
                if lang != "en":
                    print(f"⚠️ {lang} Wikipedia에서 찾지 못함, 영어로 폴백...")
                    return await self.get_species_info(scientific_name, lang="en")
                print(f"⚠️ Non-200 status from Wikipedia for {scientific_name}: {response.status_code}")
                return {}

            data = response.json()
            print(f"📦 Wikipedia data keys: {list(data.keys())[:10]}")

            # 이미지 URL 우선순위: originalimage > thumbnail
            # originalimage가 있으면 더 고품질 이미지 사용
            image_url = ""
            if "originalimage" in data and data["originalimage"].get("source"):
                image_url = data["originalimage"]["source"]
                print(f"✅ Wikipedia originalimage: {image_url[:80]}...")
            elif "thumbnail" in data and data["thumbnail"].get("source"):
                # thumbnail이 있으면 width를 800으로 확대
                thumbnail_url = data["thumbnail"]["source"]
                # URL에서 width 파라미터 수정 (예: /300px- -> /800px-)
                image_url = thumbnail_url.replace("/300px-", "/800px-").replace("/200px-", "/800px-").replace("/400px-", "/800px-")
                print(f"✅ Wikipedia thumbnail (upscaled): {image_url[:80]}...")
            else:
                print(f"⚠️ No image found in Wikipedia for {scientific_name}")

            result = {
                "description": data.get("extract", ""),
                "image_url": image_url,
                "common_name": data.get("title", scientific_name), # 위키피디아 제목을 일반명으로 사용 시도
                "lang": lang  # 어떤 언어에서 가져왔는지 표시
            }

            print(f"📦 Wikipedia result for {scientific_name} ({lang}): image={'Yes' if image_url else 'No'}, desc={len(result['description'])} chars")
            return result

        except Exception as e:
            print(f"❌ Wikipedia API Error for {scientific_name}: {e}")
            return {}

    async def close(self):
        await self.client.aclose()

wikipedia_service = WikipediaService()
