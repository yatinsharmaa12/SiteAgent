import os
import time
from threading import Lock
from typing import Dict, List, Optional

from fastapi import HTTPException, Request

# Limits: (max_requests, window_seconds)
LOGIN_LIMIT = (
    int(os.getenv("RATE_LIMIT_LOGIN_MAX", "10")),
    int(os.getenv("RATE_LIMIT_LOGIN_WINDOW", "60")),
)
REGISTER_LIMIT = (
    int(os.getenv("RATE_LIMIT_REGISTER_MAX", "10")),
    int(os.getenv("RATE_LIMIT_REGISTER_WINDOW", "60")),
)
CRAWL_LIMIT = (
    int(os.getenv("RATE_LIMIT_CRAWL_MAX", "10")),
    int(os.getenv("RATE_LIMIT_CRAWL_WINDOW", "3600")),
)
CHAT_LIMIT = (
    int(os.getenv("RATE_LIMIT_CHAT_MAX", "30")),
    int(os.getenv("RATE_LIMIT_CHAT_WINDOW", "60")),
)


def _enabled() -> bool:
    return os.getenv("RATE_LIMIT_ENABLED", "true").lower() not in ("0", "false", "no")


def _redis_client():
    try:
        from redis import Redis

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = Redis.from_url(url, socket_timeout=2)
        client.ping()
        return client
    except Exception:
        return None


_redis = None
_redis_tried = False
_mem: Dict[str, List[float]] = {}
_mem_lock = Lock()


def _get_redis():
    global _redis, _redis_tried
    if not _redis_tried:
        _redis_tried = True
        _redis = _redis_client()
    return _redis


def client_ip(http_request: Optional[Request]) -> str:
    if http_request is None:
        return "unknown"
    try:
        if http_request.client is not None:
            return http_request.client.host or "unknown"
    except Exception:
        pass
    return "unknown"


def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """Fixed-window counter. Raises 429 on excess. Redis-backed, memory fallback."""
    if not _enabled():
        return

    now = time.time()
    redis = _get_redis()
    redis_key = f"ratelimit:{key}"

    if redis is not None:
        try:
            count = redis.incr(redis_key)
            if count == 1:
                redis.expire(redis_key, window_seconds)
            else:
                ttl = redis.ttl(redis_key)
                if ttl == -1:
                    redis.expire(redis_key, window_seconds)
            if count > limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please slow down and try again.",
                    headers={"Retry-After": str(window_seconds)},
                )
            return
        except HTTPException:
            raise
        except Exception:
            pass  # fall through to memory

    with _mem_lock:
        hits = _mem.get(redis_key, [])
        hits = [t for t in hits if now - t < window_seconds]
        if len(hits) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down and try again.",
                headers={"Retry-After": str(window_seconds)},
            )
        hits.append(now)
        _mem[redis_key] = hits


def check_login_rate_limit(http_request: Optional[Request], email: Optional[str] = None) -> None:
    if http_request is None:
        return  # direct unit-test call without HTTP context
    limit, window = LOGIN_LIMIT
    ip = client_ip(http_request)
    check_rate_limit(f"login:ip:{ip}", limit, window)
    if email:
        check_rate_limit(f"login:email:{email.lower().strip()}", limit, window)


def check_register_rate_limit(http_request: Optional[Request]) -> None:
    if http_request is None:
        return
    limit, window = REGISTER_LIMIT
    check_rate_limit(f"register:ip:{client_ip(http_request)}", limit, window)


def check_crawl_rate_limit(http_request: Optional[Request], user_id: int) -> None:
    if http_request is None:
        return
    limit, window = CRAWL_LIMIT
    check_rate_limit(f"crawl:user:{user_id}", limit, window)


def check_chat_rate_limit(http_request: Optional[Request], user_id: int) -> None:
    if http_request is None:
        return
    limit, window = CHAT_LIMIT
    check_rate_limit(f"chat:user:{user_id}", limit, window)


def clear_rate_limits() -> None:
    with _mem_lock:
        _mem.clear()
    redis = _get_redis()
    if redis is not None:
        try:
            for key in redis.scan_iter("ratelimit:*"):
                redis.delete(key)
        except Exception:
            pass
