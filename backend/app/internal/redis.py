import redis
from app.internal.config import config


def get_redis_client() -> redis.Redis:
    return redis.from_url(config.REDIS_URL, decode_responses=False)


redis_client = get_redis_client()
