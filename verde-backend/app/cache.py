import redis
from app.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)


def get_cache():
    """Get Redis cache client"""
    return redis_client
