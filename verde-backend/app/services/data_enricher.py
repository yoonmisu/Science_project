"""
데이터 보강 서비스
수집된 생물 데이터를 보강하고 품질을 향상시킵니다.
"""
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.species import Species
from app.config import settings

logger = logging.getLogger(__name__)


# 생물 한글명 사전 (자주 사용되는 종)
KOREAN_NAME_DICTIONARY = {
    # 동물
    "Panthera tigris": "호랑이",
    "Ursus arctos": "불곰",
    "Ailuropoda melanoleuca": "대왕판다",
    "Elephas maximus": "아시아코끼리",
    "Loxodonta africana": "아프리카코끼리",
    "Canis lupus": "늑대",
    "Vulpes vulpes": "붉은여우",
    "Felis catus": "고양이",
    "Canis familiaris": "개",
    "Sus scrofa": "멧돼지",
    "Cervus elaphus": "붉은사슴",
    "Equus caballus": "말",
    "Bos taurus": "소",
    "Ovis aries": "양",
    "Capra hircus": "염소",

    # 조류
    "Aquila chrysaetos": "검독수리",
    "Haliaeetus albicilla": "흰꼬리수리",
    "Grus japonensis": "두루미",
    "Ciconia boyciana": "황새",
    "Phasianus colchicus": "꿩",
    "Pica pica": "까치",
    "Corvus corax": "큰까마귀",
    "Passer montanus": "참새",
    "Hirundo rustica": "제비",

    # 식물
    "Pinus densiflora": "소나무",
    "Quercus mongolica": "신갈나무",
    "Ginkgo biloba": "은행나무",
    "Acer palmatum": "단풍나무",
    "Prunus serrulata": "벚나무",
    "Bambusa": "대나무",
    "Nelumbo nucifera": "연꽃",
    "Rosa rugosa": "해당화",
    "Hibiscus syriacus": "무궁화",

    # 곤충
    "Apis mellifera": "양봉꿀벌",
    "Papilio machaon": "산호랑나비",
    "Lucanus cervus": "사슴벌레",
    "Lampyridae": "반딧불이",
    "Gryllus bimaculatus": "쌍별귀뚜라미",

    # 해양생물
    "Balaenoptera musculus": "대왕고래",
    "Orcinus orca": "범고래",
    "Delphinus delphis": "참돌고래",
    "Chelonia mydas": "푸른바다거북",
    "Octopus vulgaris": "문어",
    "Sepia officinalis": "갑오징어",
}


class DataEnricher:

    def __init__(self, db: Session):
        self.db = db
        self.stats = {
            "translated": 0,
            "descriptions_added": 0,
            "images_filtered": 0,
            "errors": 0
        }

    async def translate_name(self, scientific_name: str) -> Optional[str]:
        """
        학명을 한글명으로 번역

        1. 로컬 사전에서 먼저 검색
        2. 없으면 Wikipedia API로 검색
        """
        # 로컬 사전 검색
        if scientific_name in KOREAN_NAME_DICTIONARY:
            return KOREAN_NAME_DICTIONARY[scientific_name]

        # 속명만으로 검색
        genus = scientific_name.split()[0] if scientific_name else None
        if genus and genus in KOREAN_NAME_DICTIONARY:
            return KOREAN_NAME_DICTIONARY[genus]

        # Wikipedia API로 한글 페이지 검색
        try:
            korean_name = await self._fetch_wikipedia_korean_name(scientific_name)
            if korean_name:
                return korean_name
        except Exception as e:
            logger.error(f"Wikipedia translation error: {str(e)}")

        return None

    async def _fetch_wikipedia_korean_name(self, scientific_name: str) -> Optional[str]:
        """Wikipedia에서 한글명 검색"""
        url = "https://ko.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": scientific_name,
            "format": "json",
            "srlimit": 1
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            data = response.json()

            if data.get("query", {}).get("search"):
                title = data["query"]["search"][0]["title"]
                # 괄호 안의 분류 제거
                korean_name = title.split("(")[0].strip()
                return korean_name

        return None

    async def enrich_missing_korean_names(self, limit: int = 100) -> Dict:
        """누락된 한글명 보강"""
        # 한글명이 없거나 영문인 종 검색
        species_to_enrich = self.db.query(Species).filter(
            Species.scientific_name.isnot(None),
            or_(
                Species.name == Species.scientific_name,
                Species.name.op('~')('^[A-Za-z]')  # 영문으로 시작하는 이름
            )
        ).limit(limit).all()

        enriched = []
        for species in species_to_enrich:
            korean_name = await self.translate_name(species.scientific_name)

            if korean_name and korean_name != species.name:
                old_name = species.name
                species.name = korean_name
                enriched.append({
                    "id": species.id,
                    "scientific_name": species.scientific_name,
                    "old_name": old_name,
                    "new_name": korean_name
                })
                self.stats["translated"] += 1

            # Rate limiting
            await asyncio.sleep(0.5)

        self.db.commit()

        return {
            "processed": len(species_to_enrich),
            "enriched": len(enriched),
            "details": enriched[:20]  # 최대 20개만 반환
        }

    async def check_image_quality(self, image_url: str) -> Dict:
        """이미지 품질 확인"""
        result = {
            "valid": False,
            "width": 0,
            "height": 0,
            "size_kb": 0,
            "reason": None
        }

        try:
            async with httpx.AsyncClient() as client:
                # HEAD 요청으로 기본 정보 확인
                response = await client.head(
                    image_url,
                    timeout=10.0,
                    follow_redirects=True
                )

                if response.status_code != 200:
                    result["reason"] = f"HTTP {response.status_code}"
                    return result

                content_type = response.headers.get("content-type", "")
                if "image" not in content_type:
                    result["reason"] = f"Invalid content type: {content_type}"
                    return result

                content_length = int(response.headers.get("content-length", 0))
                result["size_kb"] = content_length // 1024

                # 너무 작은 이미지 필터링 (10KB 미만)
                if content_length < 10 * 1024:
                    result["reason"] = "Image too small"
                    return result

                result["valid"] = True

        except Exception as e:
            result["reason"] = str(e)

        return result

    async def filter_low_quality_images(self, min_size_kb: int = 10) -> Dict:
        """저화질 이미지 필터링"""
        species_with_images = self.db.query(Species).filter(
            Species.image_url.isnot(None)
        ).all()

        filtered = []
        for species in species_with_images:
            quality = await self.check_image_quality(species.image_url)

            if not quality["valid"]:
                filtered.append({
                    "id": species.id,
                    "name": species.name,
                    "url": species.image_url,
                    "reason": quality["reason"]
                })
                species.image_url = None
                self.stats["images_filtered"] += 1

            # Rate limiting
            await asyncio.sleep(0.2)

        self.db.commit()

        return {
            "checked": len(species_with_images),
            "filtered": len(filtered),
            "details": filtered[:50]
        }

    async def generate_description(self, species: Species) -> Optional[str]:
        """
        생물 설명 자동 생성

        Wikipedia 요약을 가져오거나 기본 템플릿 사용
        """
        # Wikipedia에서 요약 가져오기 시도
        description = await self._fetch_wikipedia_summary(species.scientific_name)

        if description:
            return description

        # 기본 템플릿 생성
        return self._generate_template_description(species)

    async def _fetch_wikipedia_summary(self, scientific_name: str) -> Optional[str]:
        """Wikipedia에서 종 설명 가져오기"""
        if not scientific_name:
            return None

        url = "https://ko.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": scientific_name,
            "format": "json",
            "redirects": 1
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                data = response.json()

                pages = data.get("query", {}).get("pages", {})
                for page_id, page in pages.items():
                    if page_id != "-1":
                        extract = page.get("extract", "")
                        if extract and len(extract) > 50:
                            # 너무 긴 경우 자르기
                            if len(extract) > 500:
                                extract = extract[:500] + "..."
                            return extract

        except Exception as e:
            logger.error(f"Wikipedia summary error: {str(e)}")

        return None

    def _generate_template_description(self, species: Species) -> str:
        """템플릿 기반 설명 생성"""
        category_descriptions = {
            "식물": "식물",
            "동물": "동물",
            "곤충": "곤충",
            "해양생물": "해양 생물"
        }

        category_name = category_descriptions.get(species.category, "생물")

        parts = []

        # 기본 설명
        parts.append(f"{species.name}은(는) {species.country}에 서식하는 {category_name}입니다.")

        # 학명 추가
        if species.scientific_name:
            parts.append(f"학명은 {species.scientific_name}입니다.")

        # 보전 상태 추가
        if species.conservation_status:
            status_descriptions = {
                "멸종위기": "멸종위기 상태로 보호가 필요합니다.",
                "취약": "취약한 상태로 주의가 필요합니다.",
                "준위협": "준위협 상태입니다.",
                "관심대상": "관심이 필요한 종입니다.",
                "안전": "현재 안정적인 개체수를 유지하고 있습니다."
            }
            status_desc = status_descriptions.get(species.conservation_status, "")
            if status_desc:
                parts.append(status_desc)

        return " ".join(parts)

    async def enrich_missing_descriptions(self, limit: int = 100) -> Dict:
        """누락된 설명 보강"""
        species_without_desc = self.db.query(Species).filter(
            or_(
                Species.description.is_(None),
                Species.description == ""
            )
        ).limit(limit).all()

        enriched = []
        for species in species_without_desc:
            description = await self.generate_description(species)

            if description:
                species.description = description
                enriched.append({
                    "id": species.id,
                    "name": species.name,
                    "description_length": len(description)
                })
                self.stats["descriptions_added"] += 1

            # Rate limiting
            await asyncio.sleep(0.3)

        self.db.commit()

        return {
            "processed": len(species_without_desc),
            "enriched": len(enriched),
            "details": enriched[:20]
        }

    async def enrich_all(self, limit_per_task: int = 50) -> Dict:
        """전체 데이터 보강 실행"""
        results = {}

        logger.info("Starting data enrichment...")

        # 1. 한글명 보강
        logger.info("Enriching Korean names...")
        results["korean_names"] = await self.enrich_missing_korean_names(limit_per_task)

        # 2. 설명 보강
        logger.info("Enriching descriptions...")
        results["descriptions"] = await self.enrich_missing_descriptions(limit_per_task)

        # 3. 이미지 품질 필터링
        logger.info("Filtering low quality images...")
        results["images"] = await self.filter_low_quality_images()

        results["stats"] = self.stats
        results["completed_at"] = datetime.utcnow().isoformat()

        logger.info(f"Data enrichment completed: {self.stats}")
        return results

    def get_enrichment_suggestions(self) -> Dict:
        """보강이 필요한 데이터 현황"""
        total = self.db.query(func.count(Species.id)).scalar()

        # 한글명이 없는 종
        needs_korean_name = self.db.query(func.count(Species.id)).filter(
            Species.scientific_name.isnot(None),
            or_(
                Species.name == Species.scientific_name,
                Species.name.op('~')('^[A-Za-z]')
            )
        ).scalar()

        # 설명이 없는 종
        needs_description = self.db.query(func.count(Species.id)).filter(
            or_(
                Species.description.is_(None),
                Species.description == ""
            )
        ).scalar()

        # 이미지가 없는 종
        needs_image = self.db.query(func.count(Species.id)).filter(
            Species.image_url.is_(None)
        ).scalar()

        # 좌표가 없는 종
        needs_coordinates = self.db.query(func.count(Species.id)).filter(
            or_(
                Species.latitude.is_(None),
                Species.longitude.is_(None)
            )
        ).scalar()

        return {
            "total_records": total,
            "suggestions": {
                "korean_name": {
                    "count": needs_korean_name,
                    "percentage": round(needs_korean_name / total * 100, 1) if total > 0 else 0
                },
                "description": {
                    "count": needs_description,
                    "percentage": round(needs_description / total * 100, 1) if total > 0 else 0
                },
                "image": {
                    "count": needs_image,
                    "percentage": round(needs_image / total * 100, 1) if total > 0 else 0
                },
                "coordinates": {
                    "count": needs_coordinates,
                    "percentage": round(needs_coordinates / total * 100, 1) if total > 0 else 0
                }
            }
        }
