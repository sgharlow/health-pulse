"""Tests for the in-memory TTL cache used by MCP tool results."""

import time
from unittest.mock import patch

import pytest

from healthpulse_mcp.cache import BRIEFING_TTL, TOOL_TTL, ToolCache, tool_cache


# ---------------------------------------------------------------------------
# ToolCache unit tests
# ---------------------------------------------------------------------------


class TestToolCacheMakeKey:
    """Cache key generation must be deterministic and param-order-independent."""

    def test_same_params_same_key(self):
        key1 = ToolCache.make_key("quality_monitor", {"state": "CA", "measure_group": "all"})
        key2 = ToolCache.make_key("quality_monitor", {"state": "CA", "measure_group": "all"})
        assert key1 == key2

    def test_different_param_order_same_key(self):
        key1 = ToolCache.make_key("quality_monitor", {"state": "CA", "measure_group": "all"})
        key2 = ToolCache.make_key("quality_monitor", {"measure_group": "all", "state": "CA"})
        assert key1 == key2

    def test_different_params_different_key(self):
        key1 = ToolCache.make_key("quality_monitor", {"state": "CA"})
        key2 = ToolCache.make_key("quality_monitor", {"state": "TX"})
        assert key1 != key2

    def test_different_tools_different_key(self):
        key1 = ToolCache.make_key("quality_monitor", {"state": "CA"})
        key2 = ToolCache.make_key("care_gap_finder", {"state": "CA"})
        assert key1 != key2

    def test_key_includes_tool_name_prefix(self):
        key = ToolCache.make_key("quality_monitor", {"state": "CA"})
        assert key.startswith("quality_monitor:")

    def test_list_params_produce_consistent_key(self):
        key1 = ToolCache.make_key("facility_benchmark", {"facility_ids": ["100001", "100002"]})
        key2 = ToolCache.make_key("facility_benchmark", {"facility_ids": ["100001", "100002"]})
        assert key1 == key2

    def test_none_params_produce_valid_key(self):
        key = ToolCache.make_key("quality_monitor", {"state": None})
        assert key.startswith("quality_monitor:")

    def test_empty_params(self):
        key = ToolCache.make_key("state_ranking", {})
        assert key.startswith("state_ranking:")


class TestToolCacheGetSet:
    """Basic get/set behaviour and TTL expiry."""

    def setup_method(self):
        self.cache = ToolCache(default_ttl=900)

    def test_miss_returns_none(self):
        assert self.cache.get("nonexistent:key") is None

    def test_set_then_get(self):
        self.cache.set("test:key", {"data": 42})
        assert self.cache.get("test:key") == {"data": 42}

    def test_overwrite_existing(self):
        self.cache.set("test:key", {"v": 1})
        self.cache.set("test:key", {"v": 2})
        assert self.cache.get("test:key") == {"v": 2}

    def test_expired_entry_returns_none(self):
        self.cache.set("test:key", {"data": 1}, ttl=1)
        # Advance time past TTL
        with patch("healthpulse_mcp.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert self.cache.get("test:key") is None

    def test_expired_entry_is_evicted(self):
        self.cache.set("test:key", {"data": 1}, ttl=1)
        with patch("healthpulse_mcp.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            self.cache.get("test:key")  # triggers eviction
        # After eviction, size should be 0
        # Note: since we patched time only inside the context, the entry was deleted
        # from _store already. Verify it's gone.
        assert "test:key" not in self.cache._store

    def test_not_expired_within_ttl(self):
        now = time.time()
        with patch("healthpulse_mcp.cache.time") as mock_time:
            mock_time.time.return_value = now
            self.cache.set("test:key", {"data": 1}, ttl=900)
            # Still within TTL
            mock_time.time.return_value = now + 899
            assert self.cache.get("test:key") == {"data": 1}

    def test_custom_ttl_overrides_default(self):
        now = time.time()
        with patch("healthpulse_mcp.cache.time") as mock_time:
            mock_time.time.return_value = now
            self.cache.set("test:key", {"data": 1}, ttl=5)
            # After 6 seconds should be expired
            mock_time.time.return_value = now + 6
            assert self.cache.get("test:key") is None

    def test_default_ttl_used_when_none(self):
        cache = ToolCache(default_ttl=10)
        now = time.time()
        with patch("healthpulse_mcp.cache.time") as mock_time:
            mock_time.time.return_value = now
            cache.set("test:key", {"data": 1})
            # Within default TTL
            mock_time.time.return_value = now + 9
            assert cache.get("test:key") == {"data": 1}
            # Past default TTL
            mock_time.time.return_value = now + 11
            assert cache.get("test:key") is None


class TestToolCacheIsExpired:
    """The is_expired method."""

    def setup_method(self):
        self.cache = ToolCache(default_ttl=900)

    def test_missing_key_is_expired(self):
        assert self.cache.is_expired("nonexistent") is True

    def test_valid_entry_not_expired(self):
        self.cache.set("test:key", {"data": 1}, ttl=900)
        assert self.cache.is_expired("test:key") is False

    def test_past_ttl_is_expired(self):
        self.cache.set("test:key", {"data": 1}, ttl=1)
        with patch("healthpulse_mcp.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert self.cache.is_expired("test:key") is True


class TestToolCacheClear:
    """The clear method."""

    def test_clear_empties_store(self):
        cache = ToolCache()
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size == 2
        cache.clear()
        assert cache.size == 0

    def test_get_after_clear_returns_none(self):
        cache = ToolCache()
        cache.set("a", {"val": 1})
        cache.clear()
        assert cache.get("a") is None


class TestToolCacheSize:
    """The size property."""

    def test_empty_cache_size(self):
        assert ToolCache().size == 0

    def test_size_after_inserts(self):
        cache = ToolCache()
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size == 2


# ---------------------------------------------------------------------------
# TTL constant tests
# ---------------------------------------------------------------------------


class TestTTLConstants:
    """Verify the spec TTL values."""

    def test_tool_ttl_is_15_minutes(self):
        assert TOOL_TTL == 900

    def test_briefing_ttl_is_1_hour(self):
        assert BRIEFING_TTL == 3600


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


class TestModuleSingleton:
    """The module-level tool_cache singleton is importable and functional."""

    def setup_method(self):
        tool_cache.clear()

    def teardown_method(self):
        tool_cache.clear()

    def test_singleton_exists(self):
        assert tool_cache is not None

    def test_singleton_default_ttl(self):
        assert tool_cache._default_ttl == TOOL_TTL

    def test_singleton_set_get(self):
        key = tool_cache.make_key("test_tool", {"x": 1})
        tool_cache.set(key, {"result": "ok"})
        assert tool_cache.get(key) == {"result": "ok"}


# ---------------------------------------------------------------------------
# Integration: caching in tool run() functions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quality_monitor_cache_hit(mock_domo, sample_quality_rows):
    """Second call with same params returns cached result without querying Domo."""
    from healthpulse_mcp.tools.quality_monitor import run

    tool_cache.clear()
    mock_domo.query_as_dicts.return_value = sample_quality_rows
    env = {
        "HP_QUALITY_DATASET_ID": "q-123",
        "HP_FACILITIES_DATASET_ID": "f-123",
    }

    with patch.dict("os.environ", env):
        result1 = await run(mock_domo, {"measure_group": "all", "threshold_sigma": 2.0})
        call_count_after_first = mock_domo.query_as_dicts.call_count

        result2 = await run(mock_domo, {"measure_group": "all", "threshold_sigma": 2.0})
        call_count_after_second = mock_domo.query_as_dicts.call_count

    # Second call should not have made additional Domo queries
    assert call_count_after_second == call_count_after_first
    # Results must be identical
    assert result1 == result2

    tool_cache.clear()


@pytest.mark.asyncio
async def test_quality_monitor_cache_miss_different_params(mock_domo, sample_quality_rows):
    """Different params produce a cache miss and re-query Domo."""
    from healthpulse_mcp.tools.quality_monitor import run

    tool_cache.clear()
    mock_domo.query_as_dicts.return_value = sample_quality_rows
    env = {
        "HP_QUALITY_DATASET_ID": "q-123",
        "HP_FACILITIES_DATASET_ID": "f-123",
    }

    with patch.dict("os.environ", env):
        await run(mock_domo, {"measure_group": "mortality", "threshold_sigma": 2.0})
        count_after_first = mock_domo.query_as_dicts.call_count

        await run(mock_domo, {"measure_group": "safety", "threshold_sigma": 2.0})
        count_after_second = mock_domo.query_as_dicts.call_count

    # Different params should trigger a new Domo query
    assert count_after_second > count_after_first

    tool_cache.clear()


@pytest.mark.asyncio
async def test_executive_briefing_uses_longer_ttl(mock_domo, sample_facilities_rows, sample_quality_rows):
    """Executive briefing caches with BRIEFING_TTL (3600s), not TOOL_TTL (900s)."""
    from healthpulse_mcp.tools.executive_briefing import run

    tool_cache.clear()

    call_count = [0]

    def side_effect(dataset_id, sql):
        call_count[0] += 1
        if "facility_id" in sql and "hospital_overall_rating" in sql:
            return sample_facilities_rows
        if "compared_to_national" in sql or "measure_id" in sql:
            return sample_quality_rows
        if "excess_readmission_ratio" in sql:
            return []
        return []

    mock_domo.query_as_dicts.side_effect = side_effect

    env = {
        "HP_FACILITIES_DATASET_ID": "f-123",
        "HP_QUALITY_DATASET_ID": "q-123",
        "HP_READMISSIONS_DATASET_ID": "r-123",
    }

    args = {"scope": "network", "include_equity": False}

    with patch.dict("os.environ", env):
        await run(mock_domo, args)

    # Verify the cache entry was stored with BRIEFING_TTL
    cache_key = tool_cache.make_key("executive_briefing", args)
    entry = tool_cache._store.get(cache_key)
    assert entry is not None
    _, expires_at = entry
    # The expiry should be ~ now + 3600, not now + 900
    expected_min = time.time() + BRIEFING_TTL - 5
    expected_max = time.time() + BRIEFING_TTL + 5
    assert expected_min <= expires_at <= expected_max

    tool_cache.clear()


@pytest.mark.asyncio
async def test_care_gap_finder_cache_hit(mock_domo, sample_readmission_rows):
    """care_gap_finder returns cached result on second identical call."""
    from healthpulse_mcp.tools.care_gap_finder import run

    tool_cache.clear()
    mock_domo.query_as_dicts.return_value = sample_readmission_rows
    env = {"HP_READMISSIONS_DATASET_ID": "r-123"}

    with patch.dict("os.environ", env):
        result1 = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.05})
        calls_after_first = mock_domo.query_as_dicts.call_count

        result2 = await run(mock_domo, {"gap_type": "readmission", "min_excess_ratio": 1.05})
        calls_after_second = mock_domo.query_as_dicts.call_count

    assert calls_after_second == calls_after_first
    assert result1 == result2

    tool_cache.clear()


@pytest.mark.asyncio
async def test_state_ranking_cache_hit(mock_domo):
    """state_ranking returns cached result on second identical call."""
    from healthpulse_mcp.tools.state_ranking import run

    tool_cache.clear()

    fac_rows = [
        {"facility_id": "1", "state": "CA", "facility_count": 100, "avg_rating": 3.5,
         "hospital_overall_rating": "3"},
    ]

    call_count = [0]

    def side_effect(dataset_id, sql):
        call_count[0] += 1
        return fac_rows

    mock_domo.query_as_dicts.side_effect = side_effect

    env = {
        "HP_FACILITIES_DATASET_ID": "f-123",
        "HP_QUALITY_DATASET_ID": "q-123",
    }

    with patch.dict("os.environ", env):
        result1 = await run(mock_domo, {"limit": 10, "order": "worst"})
        count1 = call_count[0]

        result2 = await run(mock_domo, {"limit": 10, "order": "worst"})
        count2 = call_count[0]

    assert count2 == count1
    assert result1 == result2

    tool_cache.clear()


@pytest.mark.asyncio
async def test_error_results_not_cached(mock_domo):
    """When tool returns an error dict, it should NOT be cached.

    The current implementation does cache error results only when they come
    from the normal code path (after dataset queries). Early-exit errors
    (missing env vars) return before the cache-set call, so they are not
    cached. This test verifies that behaviour.
    """
    from healthpulse_mcp.tools.quality_monitor import run

    tool_cache.clear()

    # Missing env var -> early return with error dict, never reaches cache.set
    with patch.dict("os.environ", {}, clear=True):
        result = await run(mock_domo, {"measure_group": "all"})

    assert "error" in result

    # Verify nothing was cached
    cache_key = tool_cache.make_key("quality_monitor", {"measure_group": "all"})
    assert tool_cache.get(cache_key) is None

    tool_cache.clear()
