"""In-memory TTL cache for MCP tool results.

CMS data updates quarterly, so a 15-minute cache is more than sufficient
for tool results.  Executive briefings use a 1-hour TTL since they
aggregate across multiple datasets and are expensive to compute.

No external dependencies -- uses only stdlib (time, hashlib, json).
"""

import hashlib
import json
import time
from typing import Any


# Default TTLs (seconds)
TOOL_TTL = 900       # 15 minutes for regular tools
BRIEFING_TTL = 3600  # 1 hour for executive briefing


class ToolCache:
    """Simple dict-based cache with per-entry TTL expiration.

    Each entry is keyed by (tool_name, params) and stores
    (result, expiry_timestamp).
    """

    def __init__(self, default_ttl: int = TOOL_TTL):
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    @staticmethod
    def make_key(tool_name: str, params: dict[str, Any]) -> str:
        """Generate a deterministic cache key from tool name and params.

        Params are JSON-serialised with sorted keys so that
        ``{"state": "CA", "limit": 10}`` and ``{"limit": 10, "state": "CA"}``
        produce the same key.
        """
        canonical = json.dumps(params, sort_keys=True, default=str)
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
        return f"{tool_name}:{digest}"

    def is_expired(self, key: str) -> bool:
        """Return True if the key is missing or past its expiry time."""
        entry = self._store.get(key)
        if entry is None:
            return True
        _, expires_at = entry
        return time.time() >= expires_at

    def get(self, key: str) -> Any | None:
        """Return cached result if present and not expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        result, expires_at = entry
        if time.time() >= expires_at:
            # Expired -- evict lazily
            del self._store[key]
            return None
        return result

    def set(self, key: str, result: Any, ttl: int | None = None) -> None:
        """Store *result* under *key* with the given TTL (or default)."""
        ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = (result, time.time() + ttl)

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()

    @property
    def size(self) -> int:
        """Number of entries (including possibly-expired ones)."""
        return len(self._store)


# Module-level singleton used by all tools
tool_cache = ToolCache(default_ttl=TOOL_TTL)
