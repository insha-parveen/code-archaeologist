import hashlib
import time
import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)


class InMemoryCache:
    """
    Simple in-memory cache with TTL (time-to-live) support.

    Designed to be a drop-in replacement for Redis later.
    The interface is intentionally simple — get, set, delete.

    In production you'd swap this for:
        import redis
        cache = redis.Redis(host='localhost', port=6379)
    And the rest of your code stays identical.
    """

    def __init__(self):
        # {key: {"value": ..., "expires_at": float}}
        self._store: dict[str, dict] = {}
        self._hits   = 0
        self._misses = 0
        self._lock   = threading.Lock()  # Thread safety for concurrent access

    def get(self, key: str) -> Any | None:
        """
        Retrieve a value. Returns None if missing or expired.
        This is called a cache miss when None is returned.
        """
        with self._lock:
            entry = self._store.get(key)

            if entry is None:
                self._misses += 1
                return None

            # Check TTL — remove if expired
            if entry["expires_at"] < time.time():
                del self._store[key]
                self._misses += 1
                logger.debug("Cache expired: %s", key[:16])
                return None

            self._hits += 1
            logger.debug("Cache hit: %s", key[:16])
            return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """
        Store a value with a TTL.
        Default TTL is 1 hour (3600 seconds).
        """
        with self._lock:
            self._store[key] = {
                "value":      value,
                "expires_at": time.time() + ttl_seconds,
            }
            logger.debug("Cache set: %s (TTL: %ds)", key[:16], ttl_seconds)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0
        logger.info("Cache cleared")

    def stats(self) -> dict:
        """
        Return cache performance statistics.
        Hit rate = hits / (hits + misses) — higher is better.
        In production, you'd expose this via a /metrics endpoint.
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
                "hits":        self._hits,
                "misses":      self._misses,
                "hit_rate":    round(hit_rate, 1),
                "total_keys":  len(self._store),
            }

    def evict_expired(self) -> int:
        """
        Remove all expired entries. Call periodically to free memory.
        Returns count of evicted entries.
        """
        with self._lock:
            now     = time.time()
            expired = [
                k for k, v in self._store.items()
                if v["expires_at"] < now
            ]
            for key in expired:
                del self._store[key]

        if expired:
            logger.info("Evicted %d expired cache entries", len(expired))

        return len(expired)


# ── Cache key generation ───────────────────────────────────────────

def make_file_cache_key(source_code: str) -> str:
    """
    Generate a cache key for a complete file analysis.
    MD5 of the source code — same code = same key.

    Why MD5? It's fast and collision-resistant enough for caching.
    We're not using it for security — just identity.
    """
    return "file:" + hashlib.md5(
        source_code.encode("utf-8")
    ).hexdigest()


def make_function_cache_key(func_name: str, source_code: str) -> str:
    """
    Generate a cache key for a single function's LLM analysis.
    Includes function name in key to avoid collisions between
    different functions with identical code.
    """
    content = f"{func_name}:{source_code}"
    return "fn:" + hashlib.md5(
        content.encode("utf-8")
    ).hexdigest()


# ── Module-level cache instances ──────────────────────────────────

# One cache for full file results — 1 hour TTL
file_cache = InMemoryCache()

# One cache for LLM function summaries — 24 hour TTL
# Function summaries change less often than full analyses
llm_cache = InMemoryCache()
