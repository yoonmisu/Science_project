"""
통합 데이터 수집 서비스
GBIF, iNaturalist, IUCN API에서 데이터를 주기적으로 수집하여 DB에 저장
"""
import logging
from typing import List, Dict
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.species import Species, CategoryEnum, ConservationStatusEnum
from app.models.region_biodiversity import RegionBiodiversity
from app.services.gbif_service import gbif_service
from app.services.inaturalist_service import inaturalist_service
from app.services.iucn_service import iucn_service

logger = logging.getLogger(__name__)

# 주요 국가 목록
TARGET_COUNTRIES = [
    {"code": "KR", "name": "Korea", "region": "아시아"},
    {"code": "US", "name": "USA", "region": "북미"},
    {"code": "CN", "name": "China", "region": "아시아"},
    {"code": "JP", "name": "Japan", "region": "아시아"},
    {"code": "GB", "name": "United Kingdom", "region": "유럽"},
    {"code": "DE", "name": "Germany", "region": "유럽"},
    {"code": "FR", "name": "France", "region": "유럽"},
    {"code": "AU", "name": "Australia", "region": "오세아니아"},
    {"code": "BR", "name": "Brazil", "region": "남미"},
    {"code": "IN", "name": "India", "region": "아시아"}
]


class DataCollector:
    """통합 데이터 수집기"""

    def __init__(self):
        self.gbif = gbif_service
        self.inat = inaturalist_service
        self.iucn = iucn_service

    def _get_db(self) -> Session:
        """DB 세션 생성"""
        return SessionLocal()

    # =========================================================================
    # 종 데이터 수집 및 저장
    # =========================================================================
    async def collect_species_by_country(
        self,
        country_code: str,
        country_name: str,
        region: str,
        limit: int = 500
    ) -> Dict:
        """
        국가별 생물종 데이터 수집

        Args:
            country_code: ISO 국가 코드
            country_name: 국가 이름
            region: 지역명
            limit: 수집할 종 수

        Returns:
            수집 결과 통계
        """
        db = self._get_db()
        try:
            logger.info(f"Collecting species for {country_name} ({country_code})...")

            # GBIF에서 데이터 수집
            gbif_species = await self.gbif.fetch_species_by_region(
                country_code, limit=limit
            )

            # iNaturalist에서 인기 종 수집
            place_id = self.inat.get_place_id(country_code)
            inat_species = []
            if place_id:
                inat_species = await self.inat.get_popular_species(
                    place_id, limit=50
                )

            # DB에 저장
            imported = 0
            updated = 0
            skipped = 0

            for species_data in gbif_species:
                result = await self._upsert_species(db, species_data, country_name, region)
                if result == "imported":
                    imported += 1
                elif result == "updated":
                    updated += 1
                else:
                    skipped += 1

            db.commit()

            result = {
                "country": country_name,
                "country_code": country_code,
                "imported": imported,
                "updated": updated,
                "skipped": skipped,
                "total_processed": len(gbif_species),
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Species collection for {country_name} complete: {result}")
            return result

        except Exception as e:
            db.rollback()
            logger.error(f"Error collecting species for {country_name}: {str(e)}")
            raise
        finally:
            db.close()

    async def _upsert_species(
        self,
        db: Session,
        species_data: Dict,
        country_name: str,
        region: str
    ) -> str:
        """종 데이터 업서트 (Insert or Update)"""
        try:
            scientific_name = species_data.get("scientific_name")
            name = species_data.get("name")

            if not scientific_name and not name:
                return "skipped"

            # 기존 데이터 확인
            existing = None
            if scientific_name:
                existing = db.query(Species).filter(
                    Species.scientific_name == scientific_name
                ).first()

            if not existing and name:
                existing = db.query(Species).filter(
                    Species.name == name
                ).first()

            # 카테고리 변환
            category = self._map_category(species_data.get("category"))

            # 보전 상태 변환
            conservation_status = self._map_conservation_status(
                species_data.get("conservation_status")
            )

            if existing:
                # 업데이트
                if species_data.get("characteristics"):
                    existing.characteristics = species_data["characteristics"]
                if conservation_status:
                    existing.conservation_status = conservation_status
                return "updated"
            else:
                # 새로 추가
                new_species = Species(
                    name=name or scientific_name,
                    scientific_name=scientific_name,
                    category=category,
                    region=region,
                    country=country_name,
                    description=species_data.get("description", ""),
                    characteristics=species_data.get("characteristics"),
                    conservation_status=conservation_status,
                    search_count=0
                )
                db.add(new_species)
                return "imported"

        except Exception as e:
            logger.warning(f"Error upserting species: {str(e)}")
            return "skipped"

    def _map_category(self, category_str: str) -> str:
        """카테고리 문자열을 Enum 값으로 매핑"""
        if not category_str:
            return None

        category_map = {
            "식물": "식물",
            "동물": "동물",
            "곤충": "곤충",
            "해양생물": "해양생물",
            "기타": None
        }

        return category_map.get(category_str)

    def _map_conservation_status(self, status: str) -> str:
        """보전 상태 매핑"""
        if not status:
            return None

        status_map = {
            "멸종위기": "멸종위기",
            "취약": "취약",
            "준위협": "준위협",
            "관심대상": "관심대상",
            "안전": "안전"
        }

        return status_map.get(status)

    # =========================================================================
    # 멸종위기종 업데이트
    # =========================================================================
    async def update_endangered_species(self, country_code: str = None) -> Dict:
        """
        멸종위기종 보전 상태 업데이트

        Args:
            country_code: 특정 국가만 업데이트 (None이면 전체)

        Returns:
            업데이트 결과
        """
        db = self._get_db()
        try:
            logger.info("Updating endangered species conservation status...")

            if country_code:
                # 특정 국가
                endangered_list = await self.iucn.get_country_species(country_code)
            else:
                # 전체 멸종위기종
                endangered_list = await self.iucn.fetch_endangered_species()

            updated = 0
            not_found = 0

            for species_data in endangered_list:
                scientific_name = species_data.get("scientific_name")
                if not scientific_name:
                    continue

                # DB에서 종 찾기
                species = db.query(Species).filter(
                    Species.scientific_name == scientific_name
                ).first()

                if species:
                    # 보전 상태 업데이트
                    new_status = self._map_iucn_to_status(
                        species_data.get("category_code")
                    )
                    if new_status:
                        species.conservation_status = new_status
                        updated += 1
                else:
                    not_found += 1

            db.commit()

            result = {
                "updated": updated,
                "not_found": not_found,
                "total_processed": len(endangered_list),
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Endangered species update complete: {result}")
            return result

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating endangered species: {str(e)}")
            raise
        finally:
            db.close()

    def _map_iucn_to_status(self, iucn_code: str) -> str:
        """IUCN 코드를 보전 상태로 매핑"""
        status_map = {
            "CR": "멸종위기",
            "EN": "멸종위기",
            "VU": "취약",
            "NT": "준위협",
            "LC": "관심대상"
        }
        return status_map.get(iucn_code)

    # =========================================================================
    # 지역 통계 업데이트
    # =========================================================================
    async def update_region_statistics(self) -> Dict:
        """모든 지역의 생물 다양성 통계 업데이트"""
        db = self._get_db()
        try:
            logger.info("Updating region biodiversity statistics...")

            results = []

            for country_info in TARGET_COUNTRIES:
                country_name = country_info["name"]
                region_name = country_info["region"]

                # 지역별 통계 계산
                stats = db.query(
                    func.count(Species.id).label('total'),
                    func.count(
                        func.nullif(Species.conservation_status.in_(['멸종위기', '취약']), False)
                    ).label('endangered')
                ).filter(
                    Species.country == country_name
                ).first()

                # 카테고리별 통계
                category_stats = {}
                for cat in ['식물', '동물', '곤충', '해양생물']:
                    count = db.query(func.count(Species.id)).filter(
                        Species.country == country_name,
                        Species.category == cat
                    ).scalar()
                    category_stats[cat] = count or 0

                # RegionBiodiversity 업데이트
                region = db.query(RegionBiodiversity).filter(
                    RegionBiodiversity.country == country_name
                ).first()

                if region:
                    region.total_species_count = stats.total or 0
                    region.endangered_count = stats.endangered or 0
                    region.plant_count = category_stats.get('식물', 0)
                    region.animal_count = category_stats.get('동물', 0)
                    region.insect_count = category_stats.get('곤충', 0)
                    region.marine_count = category_stats.get('해양생물', 0)
                else:
                    # 새로 생성
                    new_region = RegionBiodiversity(
                        region_name=region_name,
                        country=country_name,
                        total_species_count=stats.total or 0,
                        endangered_count=stats.endangered or 0,
                        plant_count=category_stats.get('식물', 0),
                        animal_count=category_stats.get('동물', 0),
                        insect_count=category_stats.get('곤충', 0),
                        marine_count=category_stats.get('해양생물', 0)
                    )
                    db.add(new_region)

                results.append({
                    "country": country_name,
                    "total": stats.total or 0,
                    "endangered": stats.endangered or 0
                })

            db.commit()

            logger.info(f"Region statistics updated for {len(results)} countries")
            return {
                "countries_updated": len(results),
                "details": results,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating region statistics: {str(e)}")
            raise
        finally:
            db.close()

    # =========================================================================
    # 전체 데이터 수집 (일괄)
    # =========================================================================
    async def collect_all_countries(self, limit_per_country: int = 500) -> Dict:
        """모든 대상 국가의 데이터 수집"""
        results = []

        for country_info in TARGET_COUNTRIES:
            try:
                result = await self.collect_species_by_country(
                    country_info["code"],
                    country_info["name"],
                    country_info["region"],
                    limit=limit_per_country
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to collect for {country_info['name']}: {str(e)}")
                results.append({
                    "country": country_info["name"],
                    "error": str(e)
                })

        return {
            "total_countries": len(TARGET_COUNTRIES),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }


# 싱글톤 인스턴스
data_collector = DataCollector()


# =========================================================================
# 스케줄러 작업 함수
# =========================================================================
async def daily_species_update():
    """매일 새벽 2시: 생물종 데이터 업데이트"""
    logger.info("Starting daily species update...")
    try:
        result = await data_collector.collect_all_countries(limit_per_country=1000)
        logger.info(f"Daily species update complete: {result}")
    except Exception as e:
        logger.error(f"Daily species update failed: {str(e)}")


async def weekly_endangered_update():
    """매주 월요일 새벽 3시: 멸종위기종 업데이트"""
    logger.info("Starting weekly endangered species update...")
    try:
        result = await data_collector.update_endangered_species()
        logger.info(f"Weekly endangered update complete: {result}")
    except Exception as e:
        logger.error(f"Weekly endangered update failed: {str(e)}")


async def monthly_statistics_update():
    """매달 1일 새벽 4시: 전체 통계 재계산"""
    logger.info("Starting monthly statistics update...")
    try:
        result = await data_collector.update_region_statistics()
        logger.info(f"Monthly statistics update complete: {result}")
    except Exception as e:
        logger.error(f"Monthly statistics update failed: {str(e)}")
