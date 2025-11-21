import redis
from redis import ConnectionPool
import json
import logging
from typing import Optional, Any
from datetime import datetime, timedelta
from functools import wraps

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Connection Pool Configuration
pool = ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
)

# Redis Client
redis_client = redis.Redis(connection_pool=pool)


def get_redis_client() -> redis.Redis:
    """Get Redis client instance"""
    return redis_client


def health_check() -> dict:
    """Check Redis connection health"""
    try:
        redis_client.ping()
        info = redis_client.info()
        return {
            "status": "healthy",
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0)
        }
    except redis.ConnectionError as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Redis health check error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# =============================================================================
# Basic Caching Functions
# =============================================================================

def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except redis.ConnectionError as e:
        logger.warning(f"Redis connection error on get: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error for key {key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL (seconds)"""
    try:
        serialized = json.dumps(value, default=str, ensure_ascii=False)
        redis_client.setex(key, ttl, serialized)
        return True
    except redis.ConnectionError as e:
        logger.warning(f"Redis connection error on set: {e}")
        return False
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    try:
        redis_client.delete(key)
        return True
    except redis.ConnectionError as e:
        logger.warning(f"Redis connection error on delete: {e}")
        return False
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


def cache_clear_pattern(pattern: str) -> int:
    """Delete all keys matching pattern"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except redis.ConnectionError as e:
        logger.warning(f"Redis connection error on clear pattern: {e}")
        return 0
    except Exception as e:
        logger.error(f"Cache clear pattern error for {pattern}: {e}")
        return 0


def cache_exists(key: str) -> bool:
    """Check if key exists in cache"""
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        logger.error(f"Cache exists error for key {key}: {e}")
        return False


def cache_get_ttl(key: str) -> int:
    """Get remaining TTL for a key"""
    try:
        return redis_client.ttl(key)
    except Exception as e:
        logger.error(f"Cache TTL error for key {key}: {e}")
        return -1


# =============================================================================
# Real-time Search Ranking (Sorted Set)
# =============================================================================

SEARCH_RANKING_KEY = "search:ranking"
SEARCH_RANKING_DAILY_KEY = "search:ranking:{date}"


def increment_search_count(query: str, increment: int = 1) -> float:
    """Increment search count using ZINCRBY"""
    try:
        # Global ranking
        score = redis_client.zincrby(SEARCH_RANKING_KEY, increment, query)

        # Daily ranking with auto-expiry
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = SEARCH_RANKING_DAILY_KEY.format(date=today)
        redis_client.zincrby(daily_key, increment, query)

        # Set expiry for daily key (25 hours to ensure full day coverage)
        redis_client.expire(daily_key, 90000)

        logger.debug(f"Search count incremented for '{query}': {score}")
        return score
    except Exception as e:
        logger.error(f"Error incrementing search count for '{query}': {e}")
        return 0


def get_top_searches(limit: int = 10, daily: bool = False) -> list[dict]:
    """Get top N searches using ZREVRANGE"""
    try:
        if daily:
            today = datetime.now().strftime("%Y-%m-%d")
            key = SEARCH_RANKING_DAILY_KEY.format(date=today)
        else:
            key = SEARCH_RANKING_KEY

        # Get top searches with scores
        results = redis_client.zrevrange(key, 0, limit - 1, withscores=True)

        return [
            {"query": query, "count": int(score)}
            for query, score in results
        ]
    except Exception as e:
        logger.error(f"Error getting top searches: {e}")
        return []


def get_search_rank(query: str) -> Optional[int]:
    """Get rank of a search query (0-based, None if not found)"""
    try:
        rank = redis_client.zrevrank(SEARCH_RANKING_KEY, query)
        return rank
    except Exception as e:
        logger.error(f"Error getting search rank for '{query}': {e}")
        return None


def get_search_score(query: str) -> Optional[float]:
    """Get search count for a query"""
    try:
        score = redis_client.zscore(SEARCH_RANKING_KEY, query)
        return score
    except Exception as e:
        logger.error(f"Error getting search score for '{query}': {e}")
        return None


def remove_from_ranking(query: str) -> bool:
    """Remove a query from ranking"""
    try:
        redis_client.zrem(SEARCH_RANKING_KEY, query)
        return True
    except Exception as e:
        logger.error(f"Error removing '{query}' from ranking: {e}")
        return False


def clear_search_ranking() -> bool:
    """Clear all search rankings"""
    try:
        redis_client.delete(SEARCH_RANKING_KEY)
        # Clear daily rankings
        cache_clear_pattern("search:ranking:*")
        return True
    except Exception as e:
        logger.error(f"Error clearing search ranking: {e}")
        return False


# =============================================================================
# Specialized Cache Functions
# =============================================================================

# Cache key patterns
CACHE_KEYS = {
    "random_species": "species:random:{date}",
    "trending_searches": "search:trending",
    "region_stats": "regions:{region}:stats",
    "popular_species": "species:popular",
    "endangered_stats": "endangered:stats",
    "species_detail": "species:{id}",
}


def get_random_species_cache(date: str) -> Optional[dict]:
    """Get cached random species for a specific date"""
    key = CACHE_KEYS["random_species"].format(date=date)
    return cache_get(key)


def set_random_species_cache(date: str, data: dict) -> bool:
    """Cache random species for 24 hours"""
    key = CACHE_KEYS["random_species"].format(date=date)
    return cache_set(key, data, ttl=86400)  # 24 hours


def get_trending_searches_cache() -> Optional[list]:
    """Get cached trending searches"""
    return cache_get(CACHE_KEYS["trending_searches"])


def set_trending_searches_cache(data: list) -> bool:
    """Cache trending searches for 5 minutes"""
    return cache_set(CACHE_KEYS["trending_searches"], data, ttl=300)


def get_region_stats_cache(region: str) -> Optional[dict]:
    """Get cached region statistics"""
    key = CACHE_KEYS["region_stats"].format(region=region)
    return cache_get(key)


def set_region_stats_cache(region: str, data: dict) -> bool:
    """Cache region statistics for 1 hour"""
    key = CACHE_KEYS["region_stats"].format(region=region)
    return cache_set(key, data, ttl=3600)


def get_popular_species_cache() -> Optional[list]:
    """Get cached popular species"""
    return cache_get(CACHE_KEYS["popular_species"])


def set_popular_species_cache(data: list) -> bool:
    """Cache popular species for 30 minutes"""
    return cache_set(CACHE_KEYS["popular_species"], data, ttl=1800)


def invalidate_species_cache(species_id: int = None) -> int:
    """Invalidate species-related caches"""
    count = 0
    if species_id:
        cache_delete(CACHE_KEYS["species_detail"].format(id=species_id))
        count += 1

    # Invalidate aggregate caches
    cache_delete(CACHE_KEYS["popular_species"])
    count += cache_clear_pattern("species:stats:*")
    count += cache_clear_pattern("regions:*:stats")

    return count


def invalidate_region_cache(region: str = None) -> int:
    """Invalidate region-related caches"""
    if region:
        return cache_clear_pattern(f"regions:{region}:*")
    return cache_clear_pattern("regions:*")


# =============================================================================
# Cache Decorator
# =============================================================================

def cached(key_pattern: str, ttl: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from pattern and arguments
            cache_key = key_pattern.format(*args, **kwargs)

            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl)
                logger.debug(f"Cached result for {cache_key}")

            return result
        return wrapper
    return decorator


# =============================================================================
# Initialization
# =============================================================================

def init_cache():
    """Initialize cache system"""
    try:
        redis_client.ping()
        logger.info("Redis cache initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Redis cache: {e}")
        return False
