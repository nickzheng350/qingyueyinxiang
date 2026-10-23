"""缓存模块测试"""

import time

from src.cache.manager import MemoryCache


def test_set_and_get():
    cache = MemoryCache()
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_missing_key_returns_none():
    cache = MemoryCache()
    assert cache.get("nope") is None


def test_delete_removes_entry():
    cache = MemoryCache()
    cache.set("k", "v")
    assert cache.delete("k") is True
    assert cache.get("k") is None


def test_clear_empties_cache():
    cache = MemoryCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.keys() == []


def test_ttl_expiration():
    cache = MemoryCache()
    cache.set("k", "v", ttl=1)
    assert cache.get("k") == "v"
    time.sleep(1.1)
    assert cache.get("k") is None


def test_lru_eviction_respects_max_size():
    cache = MemoryCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert len(cache.keys()) <= 2


def test_stats_record_hits_and_misses():
    cache = MemoryCache()
    cache.get("miss")
    cache.set("k", "v")
    cache.get("k")
    stats = cache.get_stats()
    assert stats["misses"] >= 1
    assert stats["hits"] >= 1


def test_namespace_isolation(cache_manager):
    cache_manager.set("k", "v1", namespace="ns1")
    cache_manager.set("k", "v2", namespace="ns2")
    assert cache_manager.get("k", "ns1") == "v1"
    assert cache_manager.get("k", "ns2") == "v2"


def test_clear_namespace_only_affects_target(cache_manager):
    cache_manager.set("k", "v1", namespace="ns1")
    cache_manager.set("k", "v2", namespace="ns2")
    cache_manager.clear_namespace("ns1")
    assert cache_manager.get("k", "ns1") is None
    assert cache_manager.get("k", "ns2") == "v2"
