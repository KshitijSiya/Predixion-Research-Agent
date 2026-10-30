import time
from typing import Any, Dict, Optional

class SimpleTTLCache:
    """
    Lightweight, in-memory TTL cache to reduce redundant API calls,
    lower latency, and stay resilient against rate-limiting.
    """
    def __init__(self, default_ttl_seconds: int = 86400):  # 24 hours default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        item = self._cache[key]
        if time.time() > item["expires_at"]:
            del self._cache[key]
            return None
        return item["value"]

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds or self.default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

    def clear(self) -> None:
        self._cache.clear()

    def size(self) -> int:
        return len(self._cache)

# Global singleton cache instances
search_cache = SimpleTTLCache(default_ttl_seconds=86400)
scraper_cache = SimpleTTLCache(default_ttl_seconds=86400)
