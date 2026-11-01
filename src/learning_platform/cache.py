"""Redis cache for each student's course completion percentage."""

import os

import redis

from learning_platform.progress import get_completion_percentage

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_SECONDS = 300


def get_redis_client() -> redis.Redis:
    """Create a client for the Redis server."""
    return redis.Redis.from_url(REDIS_URL)


def cache_key(student_id: int, course_id: int) -> str:
    """Return the Redis key for one student's progress in one course."""
    return f"progress:{student_id}:{course_id}"


def get_cached_completion(redis_client, conn, student_id: int, course_id: int) -> float:
    """Return the completion percentage, from Redis if cached, else from PostgreSQL.

    A value calculated from PostgreSQL is stored in Redis for CACHE_SECONDS,
    so the next request for it is answered from memory.
    """
    key = cache_key(student_id, course_id)
    cached = redis_client.get(key)
    if cached is not None:
        return float(cached)

    percentage = get_completion_percentage(conn, student_id, course_id)
    redis_client.set(key, percentage, ex=CACHE_SECONDS)
    return percentage


def clear_cached_completion(redis_client, student_id: int, course_id: int) -> None:
    """Delete a cached percentage, so the next request recalculates it."""
    redis_client.delete(cache_key(student_id, course_id))