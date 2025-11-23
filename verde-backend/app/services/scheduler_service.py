import logging
from datetime import datetime
from contextlib import contextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.database import SessionLocal
from app.cache import cache_clear_pattern, CacheKeys

logger = logging.getLogger(__name__)


@contextmanager
def get_db_session():
    """스케줄러용 DB 세션 컨텍스트 매니저"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SchedulerService:
    """APScheduler 기반 스케줄링 서비스"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """스케줄 작업 설정"""
        # 매일 자정에 캐시 정리
        self.scheduler.add_job(
            self.clear_expired_cache,
            CronTrigger(hour=0, minute=0),
            id="clear_cache",
            name="Clear expired cache",
            replace_existing=True
        )

        # 매시간 검색 순위 동기화
        self.scheduler.add_job(
            self.sync_search_rankings,
            IntervalTrigger(hours=1),
            id="sync_rankings",
            name="Sync search rankings",
            replace_existing=True
        )

        # 매일 오전 3시에 통계 업데이트
        self.scheduler.add_job(
            self.update_region_statistics,
            CronTrigger(hour=3, minute=0),
            id="update_stats",
            name="Update region statistics",
            replace_existing=True
        )

        # 매일 새벽 2시에 생물종 데이터 업데이트
        self.scheduler.add_job(
            self.daily_species_update,
            CronTrigger(hour=2, minute=0),
            id="daily_species",
            name="Daily species data update",
            replace_existing=True
        )

        # 매주 월요일 새벽 3시에 멸종위기종 업데이트
        self.scheduler.add_job(
            self.weekly_endangered_update,
            CronTrigger(day_of_week="mon", hour=3, minute=0),
            id="weekly_endangered",
            name="Weekly endangered species update",
            replace_existing=True
        )

        # 매달 1일 새벽 4시에 전체 통계 재계산
        self.scheduler.add_job(
            self.monthly_statistics_update,
            CronTrigger(day=1, hour=4, minute=0),
            id="monthly_stats",
            name="Monthly statistics recalculation",
            replace_existing=True
        )

        logger.info("Scheduler jobs configured")

    def start(self):
        """스케줄러 시작"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """스케줄러 종료"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def get_jobs(self):
        """등록된 작업 목록"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs

    # 스케줄 작업 함수들
    async def clear_expired_cache(self):
        """만료된 캐시 정리"""
        try:
            # 오래된 검색 순위 캐시 정리
            cache_clear_pattern("trending:*")
            cache_clear_pattern("popular:*")

            logger.info(f"Cache cleared at {datetime.utcnow()}")

        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    async def sync_search_rankings(self):
        """Redis 검색 순위를 DB에 동기화"""
        try:
            from app.models.search_query import SearchQuery
            from app.cache import get_top_searches

            with get_db_session() as db:
                # Redis에서 상위 검색어 가져오기
                top_searches = get_top_searches(limit=100)

                for item in top_searches:
                    query_text = item.get("query")
                    score = int(item.get("score", 0))

                    # DB 업데이트
                    existing = db.query(SearchQuery).filter(
                        SearchQuery.query_text == query_text
                    ).first()

                    if existing:
                        existing.search_count = max(existing.search_count, score)
                    else:
                        new_query = SearchQuery(
                            query_text=query_text,
                            search_count=score
                        )
                        db.add(new_query)

                db.commit()
                logger.info(f"Search rankings synced: {len(top_searches)} queries")

        except Exception as e:
            logger.error(f"Error syncing search rankings: {str(e)}")

    async def update_region_statistics(self):
        """지역별 생물 다양성 통계 업데이트"""
        try:
            from sqlalchemy import func
            from app.models.species import Species
            from app.models.region_biodiversity import RegionBiodiversity

            with get_db_session() as db:
                # 지역별 통계 계산
                region_stats = db.query(
                    Species.region,
                    func.count(Species.id).label('total'),
                    func.count(
                        func.case((Species.conservation_status.in_(['멸종위기', '취약']), 1))
                    ).label('endangered')
                ).group_by(Species.region).all()

                for stat in region_stats:
                    region = db.query(RegionBiodiversity).filter(
                        RegionBiodiversity.region_name == stat.region
                    ).first()

                    if region:
                        region.total_species_count = stat.total
                        region.endangered_count = stat.endangered

                db.commit()
                logger.info(f"Region statistics updated: {len(region_stats)} regions")

        except Exception as e:
            logger.error(f"Error updating region statistics: {str(e)}")

    async def update_gbif_data(self):
        """GBIF에서 새로운 데이터 업데이트"""
        try:
            from app.services.import_service import GBIFService

            with get_db_session() as db:
                async with GBIFService(db) as gbif:
                    # 예: 한국의 멸종위기종 업데이트
                    result = await gbif.import_species_from_gbif(
                        query="endangered",
                        country="Korea",
                        region="아시아",
                        limit=100
                    )

                    logger.info(f"GBIF data updated: {result['imported']} new species")

        except Exception as e:
            logger.error(f"Error updating GBIF data: {str(e)}")

    async def daily_species_update(self):
        """매일 새벽 2시: 생물종 데이터 업데이트"""
        logger.info("Starting daily species update...")
        try:
            from app.services.data_collector import data_collector
            result = await data_collector.collect_all_countries(limit_per_country=1000)
            logger.info(f"Daily species update complete: {result}")
        except Exception as e:
            logger.error(f"Daily species update failed: {str(e)}")

    async def weekly_endangered_update(self):
        """매주 월요일 새벽 3시: 멸종위기종 업데이트"""
        logger.info("Starting weekly endangered species update...")
        try:
            from app.services.data_collector import data_collector
            result = await data_collector.update_endangered_species()
            logger.info(f"Weekly endangered update complete: {result}")
        except Exception as e:
            logger.error(f"Weekly endangered update failed: {str(e)}")

    async def monthly_statistics_update(self):
        """매달 1일 새벽 4시: 전체 통계 재계산"""
        logger.info("Starting monthly statistics update...")
        try:
            from app.services.data_collector import data_collector
            result = await data_collector.update_region_statistics()
            logger.info(f"Monthly statistics update complete: {result}")
        except Exception as e:
            logger.error(f"Monthly statistics update failed: {str(e)}")


# 싱글톤 인스턴스
scheduler_service = SchedulerService()
