import httpx
from typing import Optional, Dict, Any

class WikipediaService:
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
        # User-Agent 헤더 추가 (Wikipedia API는 User-Agent 필수)
        headers = {
            "User-Agent": "VerdeApp/1.0 (https://github.com/verde-app/verde; verde@example.com)"
        }
        # 타임아웃을 5초로 설정하여 안정적인 응답 보장
        self.client = httpx.AsyncClient(timeout=5.0, headers=headers)

    async def get_species_info(self, scientific_name: str) -> Dict[str, Any]:
        """
        학명(Scientific Name)으로 Wikipedia 정보를 가져옵니다.
        이미지 URL과 요약 설명을 반환합니다.
        """
        try:
            # 공백을 언더스코어로 변환
            title = scientific_name.replace(" ", "_")
            url = f"{self.base_url}/{title}"

            print(f"🌐 Fetching Wikipedia: {url}")
            response = await self.client.get(url)

            print(f"📡 Wikipedia response status: {response.status_code}")
            if response.status_code != 200:
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
                "common_name": data.get("title", scientific_name) # 위키피디아 제목을 일반명으로 사용 시도
            }

            print(f"📦 Wikipedia result for {scientific_name}: image={'Yes' if image_url else 'No'}, desc={len(result['description'])} chars")
            return result

        except Exception as e:
            print(f"❌ Wikipedia API Error for {scientific_name}: {e}")
            return {}

    async def close(self):
        await self.client.aclose()

wikipedia_service = WikipediaService()
