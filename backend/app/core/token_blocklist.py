import os
import time
from threading import Lock
from typing import Dict, Optional

# Server-side revocation for JWTs (logout). Redis-backed with memory fallback.
# Entries auto-expire with the token so the set stays bounded.

_mem: Dict[str, float] = {}
_mem_lock = Lock()
_redis = None
_redis_tried = False


def _get_redis():
    global _redis, _redis_tried
    if not _redis_tried:
        _redis_tried = True
        try:
            from redis import Redis

            client = Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                socket_timeout=2,
            )
            client.ping()
            _redis = client
        except Exception:
            _redis = None
    return _redis


def revoke_token(jti: str, exp_timestamp: Optional[float] = None) -> None:
    if not jti:
        return
    ttl = 3600
    if exp_timestamp is not None:
        try:
            ttl = max(1, int(float(exp_timestamp) - time.time()))
        except (TypeError, ValueError):
            ttl = 3600
    key = f"tokenblock:{jti}"
    redis = _get_redis()
    if redis is not None:
        try:
            redis.setex(key, ttl, "1")
            return
        except Exception:
            pass
    with _mem_lock:
        _mem[key] = time.time() + ttl


def is_token_revoked(jti: Optional[str]) -> bool:
    if not jti:
        return False
    key = f"tokenblock:{jti}"
    redis = _get_redis()
    if redis is not None:
        try:
            return bool(redis.exists(key))
        except Exception:
            pass
    with _mem_lock:
        exp = _mem.get(key)
        if exp is None:
            return False
        if exp < time.time():
            _mem.pop(key, None)
            return False
        return True


def clear_token_blocklist() -> None:
    with _mem_lock:
        _mem.clear()
    redis = _get_redis()
    if redis is not None:
        try:
            for key in redis.scan_iter("tokenblock:*"):
                redis.delete(key)
        except Exception:
            pass
