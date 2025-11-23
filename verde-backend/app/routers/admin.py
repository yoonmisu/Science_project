"""
관리자 API
통계 대시보드, 데이터 품질 관리, 시스템 모니터링
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.database import get_db
from app.models.species import Species
from app.models.search_query import SearchQuery
from app.models.region_biodiversity import RegionBiodiversity
from app.services.auth_service import get_current_admin_user
from app.models.user import User
from app.cache import cache_get, cache_set
from app.services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={404: {"description": "Not found"}}
)


@router.get(
    "/statistics",
    summary="전체 통계 대시보드",
    description="시스템 전체 통계를 조회합니다. 관리자 권한이 필요합니다."
)
async def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """관리자 통계 대시보드"""
    try:
        # 캐시 확인 (5분)
        cache_key = "admin:statistics"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # 1. 총 생물종 수
        total_species = db.query(func.count(Species.id)).scalar()

        # 2. 국가별 데이터 커버리지
        country_coverage = db.query(
            Species.country,
            func.count(Species.id).label('count')
        ).group_by(Species.country).all()

        country_stats = {
            country: count for country, count in country_coverage
        }

        # 3. 카테고리별 분포
        category_distribution = db.query(
            Species.category,
            func.count(Species.id).label('count')
        ).group_by(Species.category).all()

        category_stats = {
            category: count for category, count in category_distribution
        }

        # 4. 보전 상태별 분포
        conservation_distribution = db.query(
            Species.conservation_status,
            func.count(Species.id).label('count')
        ).group_by(Species.conservation_status).all()

        conservation_stats = {
            status: count for status, count in conservation_distribution
        }

        # 5. 지역별 분포
        region_distribution = db.query(
            Species.region,
            func.count(Species.id).label('count')
        ).group_by(Species.region).all()

        region_stats = {
            region: count for region, count in region_distribution
        }

        # 6. 마지막 업데이트 시간
        last_update = db.query(func.max(Species.updated_at)).scalar()

        # 7. 데이터 완성도
        with_coordinates = db.query(func.count(Species.id)).filter(
            Species.latitude.isnot(None)
        ).scalar()

        with_images = db.query(func.count(Species.id)).filter(
            Species.image_url.isnot(None)
        ).scalar()

        with_descriptions = db.query(func.count(Species.id)).filter(
            Species.description.isnot(None),
            Species.description != ""
        ).scalar()

        # 8. 검색 통계
        total_searches = db.query(func.sum(SearchQuery.search_count)).scalar() or 0
        unique_queries = db.query(func.count(SearchQuery.id)).scalar()

        # 9. 최근 7일간 추가된 종
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_additions = db.query(func.count(Species.id)).filter(
            Species.created_at >= week_ago
        ).scalar()

        result = {
            "success": True,
            "data": {
                "overview": {
                    "total_species": total_species,
                    "total_countries": len(country_stats),
                    "total_regions": len(region_stats),
                    "total_categories": len(category_stats)
                },
                "country_coverage": country_stats,
                "category_distribution": category_stats,
                "conservation_distribution": conservation_stats,
                "region_distribution": region_stats,
                "data_completeness": {
                    "coordinates": {
                        "count": with_coordinates,
                        "percentage": round(with_coordinates / total_species * 100, 1) if total_species > 0 else 0
                    },
                    "images": {
                        "count": with_images,
                        "percentage": round(with_images / total_species * 100, 1) if total_species > 0 else 0
                    },
                    "descriptions": {
                        "count": with_descriptions,
                        "percentage": round(with_descriptions / total_species * 100, 1) if total_species > 0 else 0
                    }
                },
                "search_statistics": {
                    "total_searches": total_searches,
                    "unique_queries": unique_queries
                },
                "recent_activity": {
                    "new_species_7days": recent_additions
                },
                "last_update": last_update.isoformat() if last_update else None,
                "generated_at": datetime.utcnow().isoformat()
            }
        }

        # 캐시 저장 (5분)
        cache_set(cache_key, result, 300)

        return result

    except Exception as e:
        logger.error(f"Error fetching admin statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/data-quality",
    summary="데이터 품질 보고서",
    description="데이터 품질 현황을 분석합니다."
)
async def get_data_quality_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """데이터 품질 보고서"""
    from app.services.data_validator import DataValidator

    validator = DataValidator(db)
    report = validator.get_data_quality_report()

    return {
        "success": True,
        "data": report
    }


@router.post(
    "/validate-data",
    summary="데이터 검증 실행",
    description="전체 데이터를 검증하고 수정 가능한 오류를 자동으로 수정합니다."
)
async def validate_all_data(
    fix_errors: bool = Query(False, description="오류 자동 수정 여부"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """데이터 검증 실행"""
    from app.services.data_validator import DataValidator

    validator = DataValidator(db)
    results = validator.validate_all(fix_errors=fix_errors)

    return {
        "success": True,
        "data": results
    }


@router.post(
    "/remove-duplicates",
    summary="중복 데이터 제거",
    description="중복된 종 데이터를 제거합니다."
)
async def remove_duplicate_data(
    keep: str = Query("newest", description="유지할 데이터 (newest/oldest)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """중복 데이터 제거"""
    from app.services.data_validator import DataValidator

    if keep not in ["newest", "oldest"]:
        raise HTTPException(status_code=400, detail="keep must be 'newest' or 'oldest'")

    validator = DataValidator(db)

    # 먼저 중복 확인
    duplicates = validator.find_duplicates()

    if not duplicates:
        return {
            "success": True,
            "message": "중복 데이터가 없습니다",
            "removed": 0
        }

    # 중복 제거
    removed = validator.remove_duplicates(keep=keep)

    return {
        "success": True,
        "message": f"{removed}개의 중복 레코드가 제거되었습니다",
        "removed": removed,
        "duplicate_groups": len(duplicates)
    }


@router.get(
    "/enrichment-suggestions",
    summary="데이터 보강 제안",
    description="보강이 필요한 데이터 현황을 확인합니다."
)
async def get_enrichment_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """데이터 보강 제안"""
    from app.services.data_enricher import DataEnricher

    enricher = DataEnricher(db)
    suggestions = enricher.get_enrichment_suggestions()

    return {
        "success": True,
        "data": suggestions
    }


@router.post(
    "/enrich-data",
    summary="데이터 보강 실행",
    description="한글명, 설명 등 누락된 데이터를 자동으로 보강합니다."
)
async def enrich_data(
    task: str = Query("all", description="작업 유형 (all/korean_names/descriptions/images)"),
    limit: int = Query(50, ge=1, le=500, description="처리할 최대 레코드 수"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """데이터 보강 실행"""
    from app.services.data_enricher import DataEnricher

    enricher = DataEnricher(db)

    if task == "all":
        results = await enricher.enrich_all(limit_per_task=limit)
    elif task == "korean_names":
        results = await enricher.enrich_missing_korean_names(limit=limit)
    elif task == "descriptions":
        results = await enricher.enrich_missing_descriptions(limit=limit)
    elif task == "images":
        results = await enricher.filter_low_quality_images()
    else:
        raise HTTPException(status_code=400, detail="Invalid task type")

    return {
        "success": True,
        "task": task,
        "data": results
    }


@router.get(
    "/scheduler/jobs",
    summary="스케줄러 작업 목록",
    description="등록된 스케줄러 작업 목록을 조회합니다."
)
async def get_scheduler_jobs(
    current_user: User = Depends(get_current_admin_user)
):
    """스케줄러 작업 목록"""
    jobs = scheduler_service.get_jobs()

    return {
        "success": True,
        "data": {
            "jobs": jobs,
            "count": len(jobs),
            "scheduler_running": scheduler_service.scheduler.running
        }
    }


@router.get(
    "/api-usage",
    summary="API 사용 통계",
    description="API 호출 통계를 조회합니다."
)
async def get_api_usage_statistics(
    days: int = Query(7, ge=1, le=30, description="조회 기간 (일)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """API 사용 통계"""
    # 검색어 순위
    top_searches = db.query(
        SearchQuery.query_text,
        SearchQuery.search_count
    ).order_by(
        SearchQuery.search_count.desc()
    ).limit(20).all()

    search_rankings = [
        {"query": q.query_text, "count": q.search_count}
        for q in top_searches
    ]

    # 기간별 검색 추이 (일별)
    since = datetime.utcnow() - timedelta(days=days)
    daily_searches = db.query(
        func.date(SearchQuery.created_at).label('date'),
        func.count(SearchQuery.id).label('count')
    ).filter(
        SearchQuery.created_at >= since
    ).group_by(
        func.date(SearchQuery.created_at)
    ).order_by('date').all()

    daily_stats = [
        {"date": str(d.date), "count": d.count}
        for d in daily_searches
    ]

    return {
        "success": True,
        "data": {
            "top_searches": search_rankings,
            "daily_searches": daily_stats,
            "period_days": days
        }
    }


@router.get(
    "/country-progress",
    summary="국가별 데이터 수집 현황",
    description="국가별 데이터 수집 완성도를 확인합니다."
)
async def get_country_progress(
    min_target: int = Query(100, description="최소 목표 종 수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """국가별 데이터 수집 현황"""
    # 국가별 종 수
    country_counts = db.query(
        Species.country,
        func.count(Species.id).label('count')
    ).group_by(Species.country).all()

    progress = []
    for country, count in country_counts:
        status = "complete" if count >= min_target else "incomplete"
        progress.append({
            "country": country,
            "count": count,
            "target": min_target,
            "percentage": min(round(count / min_target * 100, 1), 100),
            "status": status
        })

    # 완성도순 정렬
    progress.sort(key=lambda x: x["count"], reverse=True)

    complete = sum(1 for p in progress if p["status"] == "complete")
    incomplete = len(progress) - complete

    return {
        "success": True,
        "data": {
            "summary": {
                "total_countries": len(progress),
                "complete": complete,
                "incomplete": incomplete,
                "completion_rate": round(complete / len(progress) * 100, 1) if progress else 0
            },
            "countries": progress
        }
    }


@router.post(
    "/validate-images",
    summary="이미지 URL 일괄 검증",
    description="이미지 URL의 유효성을 일괄 검증합니다."
)
async def validate_images(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """이미지 URL 일괄 검증"""
    from app.services.data_validator import DataValidator

    validator = DataValidator(db)
    results = await validator.validate_images_batch(limit=limit)

    return {
        "success": True,
        "data": results
    }


@router.get(
    "/system-health",
    summary="시스템 상태",
    description="시스템 전반적인 상태를 확인합니다."
)
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """시스템 상태"""
    from app.cache import health_check as redis_health_check

    # DB 상태
    db_healthy = True
    try:
        db.execute("SELECT 1")
    except Exception:
        db_healthy = False

    # Redis 상태
    redis_healthy = redis_health_check()

    # 스케줄러 상태
    scheduler_running = scheduler_service.scheduler.running

    return {
        "success": True,
        "data": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "connected": db_healthy
            },
            "redis": {
                "status": "healthy" if redis_healthy else "unhealthy",
                "connected": redis_healthy
            },
            "scheduler": {
                "status": "running" if scheduler_running else "stopped",
                "jobs_count": len(scheduler_service.get_jobs())
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    }
