import csv
import json
import logging
from io import StringIO
from typing import List, Optional
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models.species import Species, CategoryEnum, ConservationStatusEnum
from app.models.region_biodiversity import RegionBiodiversity

logger = logging.getLogger(__name__)


class ImportService:
    """데이터 임포트 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def import_species_from_csv(self, csv_content: str) -> dict:
        """CSV 파일에서 종 데이터 임포트"""
        try:
            reader = csv.DictReader(StringIO(csv_content))

            imported = 0
            skipped = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                try:
                    # 필수 필드 확인
                    name = row.get('name', '').strip()
                    if not name:
                        skipped += 1
                        errors.append(f"Row {row_num}: 이름 누락")
                        continue

                    # 중복 확인
                    existing = self.db.query(Species).filter(
                        Species.name == name
                    ).first()

                    if existing:
                        skipped += 1
                        continue

                    # 카테고리 변환
                    category = None
                    category_str = row.get('category', '').strip()
                    if category_str:
                        try:
                            category = CategoryEnum(category_str)
                        except ValueError:
                            pass

                    # 보전 상태 변환
                    conservation_status = None
                    status_str = row.get('conservation_status', '').strip()
                    if status_str:
                        try:
                            conservation_status = ConservationStatusEnum(status_str)
                        except ValueError:
                            pass

                    # 특징 JSON 파싱
                    characteristics = None
                    char_str = row.get('characteristics', '').strip()
                    if char_str:
                        try:
                            characteristics = json.loads(char_str)
                        except json.JSONDecodeError:
                            pass

                    species = Species(
                        name=name,
                        scientific_name=row.get('scientific_name', '').strip() or None,
                        category=category.value if category else None,
                        region=row.get('region', '').strip() or None,
                        country=row.get('country', '').strip() or None,
                        description=row.get('description', '').strip() or None,
                        characteristics=characteristics,
                        image_url=row.get('image_url', '').strip() or None,
                        conservation_status=conservation_status.value if conservation_status else None,
                        search_count=0
                    )

                    self.db.add(species)
                    imported += 1

                except Exception as e:
                    skipped += 1
                    errors.append(f"Row {row_num}: {str(e)}")

            self.db.commit()
            logger.info(f"CSV import completed: {imported} imported, {skipped} skipped")

            return {
                "imported": imported,
                "skipped": skipped,
                "errors": errors[:10]  # 최대 10개 에러만 반환
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"CSV import error: {str(e)}")
            raise

    def import_species_from_json(self, json_content: str) -> dict:
        """JSON 파일에서 종 데이터 임포트"""
        try:
            data = json.loads(json_content)

            if not isinstance(data, list):
                data = [data]

            imported = 0
            skipped = 0
            errors = []

            for idx, item in enumerate(data):
                try:
                    name = item.get('name', '').strip()
                    if not name:
                        skipped += 1
                        errors.append(f"Item {idx}: 이름 누락")
                        continue

                    # 중복 확인
                    existing = self.db.query(Species).filter(
                        Species.name == name
                    ).first()

                    if existing:
                        skipped += 1
                        continue

                    # 카테고리 변환
                    category = None
                    if item.get('category'):
                        try:
                            category = CategoryEnum(item['category'])
                        except ValueError:
                            pass

                    # 보전 상태 변환
                    conservation_status = None
                    if item.get('conservation_status'):
                        try:
                            conservation_status = ConservationStatusEnum(item['conservation_status'])
                        except ValueError:
                            pass

                    species = Species(
                        name=name,
                        scientific_name=item.get('scientific_name'),
                        category=category.value if category else None,
                        region=item.get('region'),
                        country=item.get('country'),
                        description=item.get('description'),
                        characteristics=item.get('characteristics'),
                        image_url=item.get('image_url'),
                        conservation_status=conservation_status.value if conservation_status else None,
                        search_count=0
                    )

                    self.db.add(species)
                    imported += 1

                except Exception as e:
                    skipped += 1
                    errors.append(f"Item {idx}: {str(e)}")

            self.db.commit()
            logger.info(f"JSON import completed: {imported} imported, {skipped} skipped")

            return {
                "imported": imported,
                "skipped": skipped,
                "errors": errors[:10]
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            raise ValueError("유효하지 않은 JSON 형식입니다")
        except Exception as e:
            self.db.rollback()
            logger.error(f"JSON import error: {str(e)}")
            raise


class GBIFService:
    """GBIF API 연동 서비스"""

    BASE_URL = "https://api.gbif.org/v1"

    def __init__(self, db: Session):
        self.db = db
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def search_species(
        self,
        query: str,
        limit: int = 20
    ) -> List[dict]:
        """GBIF에서 종 검색"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/species/search",
                params={
                    "q": query,
                    "limit": limit,
                    "rank": "SPECIES"
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "gbif_key": item.get("key"),
                    "scientific_name": item.get("scientificName"),
                    "canonical_name": item.get("canonicalName"),
                    "kingdom": item.get("kingdom"),
                    "phylum": item.get("phylum"),
                    "class": item.get("class"),
                    "order": item.get("order"),
                    "family": item.get("family"),
                    "genus": item.get("genus"),
                    "status": item.get("taxonomicStatus")
                })

            logger.info(f"GBIF search for '{query}': {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"GBIF search error: {str(e)}")
            raise

    async def get_species_details(self, gbif_key: int) -> dict:
        """GBIF에서 종 상세 정보 조회"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/species/{gbif_key}"
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"GBIF species detail error: {str(e)}")
            raise

    async def get_species_media(self, gbif_key: int, limit: int = 5) -> List[dict]:
        """GBIF에서 종 미디어(이미지) 조회"""
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
                        "license": item.get("license")
                    })

            return media

        except Exception as e:
            logger.error(f"GBIF media error: {str(e)}")
            raise

    async def get_occurrences_by_country(
        self,
        country_code: str,
        limit: int = 100
    ) -> List[dict]:
        """특정 국가의 종 출현 데이터 조회"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/occurrence/search",
                params={
                    "country": country_code,
                    "limit": limit,
                    "hasCoordinate": True
                }
            )
            response.raise_for_status()
            data = response.json()

            occurrences = []
            for item in data.get("results", []):
                occurrences.append({
                    "gbif_key": item.get("speciesKey"),
                    "species": item.get("species"),
                    "latitude": item.get("decimalLatitude"),
                    "longitude": item.get("decimalLongitude"),
                    "country": item.get("country"),
                    "recorded_by": item.get("recordedBy"),
                    "event_date": item.get("eventDate")
                })

            logger.info(f"GBIF occurrences for {country_code}: {len(occurrences)} results")
            return occurrences

        except Exception as e:
            logger.error(f"GBIF occurrences error: {str(e)}")
            raise

    async def import_species_from_gbif(
        self,
        query: str,
        country: str,
        region: str,
        limit: int = 50
    ) -> dict:
        """GBIF에서 종 데이터를 검색하여 DB에 임포트"""
        try:
            results = await self.search_species(query, limit)

            imported = 0
            skipped = 0

            for item in results:
                scientific_name = item.get("scientific_name")
                canonical_name = item.get("canonical_name")

                if not canonical_name:
                    skipped += 1
                    continue

                # 중복 확인
                existing = self.db.query(Species).filter(
                    Species.scientific_name == scientific_name
                ).first()

                if existing:
                    skipped += 1
                    continue

                # 카테고리 결정 (Kingdom 기반)
                kingdom = item.get("kingdom", "").lower()
                if kingdom == "animalia":
                    category = CategoryEnum.동물
                elif kingdom == "plantae":
                    category = CategoryEnum.식물
                else:
                    category = None

                species = Species(
                    name=canonical_name,
                    scientific_name=scientific_name,
                    category=category.value if category else None,
                    region=region,
                    country=country,
                    description=f"Order: {item.get('order', 'N/A')}, Family: {item.get('family', 'N/A')}",
                    characteristics={
                        "kingdom": item.get("kingdom"),
                        "phylum": item.get("phylum"),
                        "class": item.get("class"),
                        "order": item.get("order"),
                        "family": item.get("family"),
                        "genus": item.get("genus"),
                        "gbif_key": item.get("gbif_key")
                    },
                    search_count=0
                )

                self.db.add(species)
                imported += 1

            self.db.commit()
            logger.info(f"GBIF import completed: {imported} imported, {skipped} skipped")

            return {
                "imported": imported,
                "skipped": skipped,
                "query": query
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"GBIF import error: {str(e)}")
            raise
