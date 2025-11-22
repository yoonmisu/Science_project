import redis
from redis import ConnectionPool
from typing import Optional, Any, List
import json
import logging
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)

# Redis 연결 풀 설정
pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=20,
    decode_responses=True
)

# Redis 클라이언트
redis_client = redis.Redis(connection_pool=pool)


def get_cache():
    """Get Redis cache client"""
    return redis_client


def health_check() -> bool:
    """Redis 헬스 체크"""
    try:
        return redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False


# =============================================================================
# 기본 캐싱 유틸리티 함수
# =============================================================================

def cache_get(key: str) -> Optional[Any]:
    """캐시에서 데이터 조회"""
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Cache get error for key '{key}': {str(e)}")
        return None


def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """캐시에 데이터 저장

    Args:
        key: 캐시 키
        value: 저장할 데이터
        ttl: Time To Live (초), 기본 1시간
    """
    try:
        serialized = json.dumps(value, default=str, ensure_ascii=False)
        redis_client.setex(key, ttl, serialized)
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Cache set error for key '{key}': {str(e)}")
        return False


def cache_delete(key: str) -> bool:
    """캐시에서 데이터 삭제"""
    try:
        redis_client.delete(key)
        logger.debug(f"Cache deleted: {key}")
        return True
    except Exception as e:
        logger.error(f"Cache delete error for key '{key}': {str(e)}")
        return False


def cache_clear_pattern(pattern: str) -> int:
    """패턴에 매칭되는 모든 키 삭제

    Args:
        pattern: Redis 패턴 (예: "species:*", "search:*")

    Returns:
        삭제된 키 개수
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            count = redis_client.delete(*keys)
            logger.info(f"Cache cleared: {count} keys matching '{pattern}'")
            return count
        return 0
    except Exception as e:
        logger.error(f"Cache clear pattern error for '{pattern}': {str(e)}")
        return 0


def cache_exists(key: str) -> bool:
    """캐시 키 존재 여부 확인"""
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        logger.error(f"Cache exists error for key '{key}': {str(e)}")
        return False


def cache_ttl(key: str) -> int:
    """캐시 키의 남은 TTL 조회 (초)"""
    try:
        return redis_client.ttl(key)
    except Exception as e:
        logger.error(f"Cache TTL error for key '{key}': {str(e)}")
        return -1


# =============================================================================
# 실시간 검색어 랭킹 (Sorted Set)
# =============================================================================

SEARCH_RANKING_KEY = "search:ranking"
SEARCH_RANKING_TTL = 86400  # 24시간


def increment_search_count(query: str, category: str = None) -> float:
    """검색어 카운트 증가 (ZINCRBY)

    Args:
        query: 검색어
        category: 카테고리 (선택)

    Returns:
        증가 후 점수
    """
    try:
        # 카테고리가 있으면 키에 포함
        key = SEARCH_RANKING_KEY
        if category:
            key = f"{SEARCH_RANKING_KEY}:{category}"

        # 점수 증가
        score = redis_client.zincrby(key, 1, query)

        # TTL 설정 (키가 새로 생성된 경우)
        if redis_client.ttl(key) == -1:
            redis_client.expire(key, SEARCH_RANKING_TTL)

        logger.debug(f"Search count incremented: '{query}' = {score}")
        return score
    except Exception as e:
        logger.error(f"Increment search count error: {str(e)}")
        return 0


def get_top_searches(limit: int = 10, category: str = None) -> List[dict]:
    """인기 검색어 Top N 조회 (ZREVRANGE)

    Args:
        limit: 조회할 개수
        category: 카테고리 필터 (선택)

    Returns:
        [{"query": "검색어", "count": 점수}, ...]
    """
    try:
        key = SEARCH_RANKING_KEY
        if category:
            key = f"{SEARCH_RANKING_KEY}:{category}"

        # 점수와 함께 내림차순 조회
        results = redis_client.zrevrange(key, 0, limit - 1, withscores=True)

        return [
            {"query": query, "count": int(score)}
            for query, score in results
        ]
    except Exception as e:
        logger.error(f"Get top searches error: {str(e)}")
        return []


def get_search_rank(query: str, category: str = None) -> Optional[int]:
    """특정 검색어의 순위 조회

    Returns:
        순위 (1부터 시작), 없으면 None
    """
    try:
        key = SEARCH_RANKING_KEY
        if category:
            key = f"{SEARCH_RANKING_KEY}:{category}"

        rank = redis_client.zrevrank(key, query)
        return rank + 1 if rank is not None else None
    except Exception as e:
        logger.error(f"Get search rank error: {str(e)}")
        return None


def reset_search_ranking(category: str = None) -> bool:
    """검색어 랭킹 초기화"""
    try:
        key = SEARCH_RANKING_KEY
        if category:
            key = f"{SEARCH_RANKING_KEY}:{category}"

        redis_client.delete(key)
        logger.info(f"Search ranking reset: {key}")
        return True
    except Exception as e:
        logger.error(f"Reset search ranking error: {str(e)}")
        return False


# =============================================================================
# 캐시 키 상수
# =============================================================================

class CacheKeys:
    """캐시 키 상수 정의"""

    # 오늘의 랜덤 생물 (24시간)
    RANDOM_SPECIES = "species:random:{date}"
    RANDOM_SPECIES_TTL = 86400

    # 실시간 검색어 랭킹 (5분 캐시)
    TRENDING_SEARCHES = "search:trending"
    TRENDING_SEARCHES_TTL = 300

    # 지역별 통계 (1시간)
    REGION_STATS = "region:stats:{region}"
    REGION_STATS_TTL = 3600

    # 인기 생물종 (30분)
    POPULAR_SPECIES = "species:popular"
    POPULAR_SPECIES_TTL = 1800

    # 전체 통계 (10분)
    GLOBAL_STATS = "stats:global"
    GLOBAL_STATS_TTL = 600

    # 종 상세 정보 (5분)
    SPECIES_DETAIL = "species:detail:{id}"
    SPECIES_DETAIL_TTL = 300

    @staticmethod
    def random_species_key() -> str:
        """오늘 날짜 기반 랜덤 종 키"""
        return CacheKeys.RANDOM_SPECIES.format(date=datetime.now().strftime("%Y%m%d"))

    @staticmethod
    def region_stats_key(region: str) -> str:
        """지역 통계 키"""
        return CacheKeys.REGION_STATS.format(region=region)

    @staticmethod
    def species_detail_key(species_id: int) -> str:
        """종 상세 정보 키"""
        return CacheKeys.SPECIES_DETAIL.format(id=species_id)


# =============================================================================
# 편의 함수
# =============================================================================

def get_or_set_cache(key: str, ttl: int, fetch_func, *args, **kwargs) -> Any:
    """캐시에서 가져오거나, 없으면 함수 실행 후 캐시에 저장

    Args:
        key: 캐시 키
        ttl: TTL (초)
        fetch_func: 데이터를 가져올 함수
        *args, **kwargs: fetch_func에 전달할 인자

    Returns:
        캐시된 데이터 또는 새로 가져온 데이터
    """
    # 캐시에서 조회
    cached = cache_get(key)
    if cached is not None:
        logger.debug(f"Cache hit: {key}")
        return cached

    # 캐시 미스 - 함수 실행
    logger.debug(f"Cache miss: {key}")
    data = fetch_func(*args, **kwargs)

    # 캐시에 저장
    if data is not None:
        cache_set(key, data, ttl)

    return data
