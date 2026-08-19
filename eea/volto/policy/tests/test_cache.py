"""Tests for the global plone.memoize cache policy."""

import os
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from plone.memoize.interfaces import ICacheChooser
from plone.memoize.ram import RAMCacheAdapter
from zope.interface.verify import verifyObject
from zope.ramcache.ram import RAMCache

from eea.volto.policy.cache import CacheChooser
from eea.volto.policy.cache import MemcacheAdapter
from eea.volto.policy.cache import RAMCacheTTLAdapter
from eea.volto.policy.cache import RedisCacheAdapter


class FakeRedisClient:
    """Minimal Redis client used by RedisCacheAdapter tests."""

    def __init__(self):
        self.values = {}
        self.expirations = {}

    def exists(self, key):
        return key in self.values

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value
        self.expirations[key] = ttl

    def delete(self, key):
        self.values.pop(key, None)


class FakeMemcacheClient:
    """Minimal Memcached client used by MemcacheAdapter tests."""

    def __init__(self):
        self.values = {}
        self.expirations = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, time=0):
        self.values[key] = value
        self.expirations[key] = time

    def delete(self, key):
        self.values.pop(key, None)


class FakeClock:
    """Controllable monotonic clock for RAM TTL tests."""

    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class CacheAdapterTest(unittest.TestCase):
    """Verify cache adapters preserve values and TTLs."""

    def test_redis_adapter_roundtrip(self):
        client = FakeRedisClient()
        cache = RedisCacheAdapter(client, "example.function", ttl=60)

        cache["key"] = {"value": [1, 2]}

        self.assertIn("key", cache)
        self.assertEqual(cache["key"], {"value": [1, 2]})
        self.assertEqual(client.expirations["example.function:key"], 60)
        del cache["key"]
        self.assertNotIn("key", cache)

    def test_memcache_adapter_roundtrip(self):
        client = FakeMemcacheClient()
        cache = MemcacheAdapter(client, "example.function", ttl=120)

        cache["key"] = {"value": [1, 2]}

        self.assertIn("key", cache)
        self.assertEqual(cache["key"], {"value": [1, 2]})
        self.assertEqual(next(iter(client.expirations.values())), 120)
        del cache["key"]
        self.assertNotIn("key", cache)

    def test_redis_adapter_skips_non_serializable_values(self):
        """Non-JSON-serializable values must not raise; they are skipped."""
        client = FakeRedisClient()
        cache = RedisCacheAdapter(client, "example.function", ttl=60)

        cache["datetime"] = datetime(2026, 1, 1)
        cache["set"] = {1, 2, 3}
        cache["bytes"] = b"hello"

        # Nothing was stored — retrieval raises KeyError
        self.assertNotIn("datetime", cache)
        self.assertNotIn("set", cache)
        self.assertNotIn("bytes", cache)
        with self.assertRaises(KeyError):
            cache["datetime"]

    def test_memcache_adapter_skips_non_serializable_values(self):
        """Non-JSON-serializable values must not raise; they are skipped."""
        client = FakeMemcacheClient()
        cache = MemcacheAdapter(client, "example.function", ttl=120)

        cache["datetime"] = datetime(2026, 1, 1)
        cache["set"] = {1, 2, 3}
        cache["bytes"] = b"hello"

        # Nothing was stored — retrieval raises KeyError
        self.assertNotIn("datetime", cache)
        self.assertNotIn("set", cache)
        self.assertNotIn("bytes", cache)
        with self.assertRaises(KeyError):
            cache["datetime"]

    def test_redis_adapter_serializable_after_skipped_value(self):
        """Cache remains usable after a skipped non-serializable value."""
        client = FakeRedisClient()
        cache = RedisCacheAdapter(client, "example.function", ttl=60)

        cache["bad"] = {1, 2, 3}  # skipped (set is not JSON-serializable)
        cache["good"] = {"value": 1}  # stored normally

        self.assertNotIn("bad", cache)
        self.assertIn("good", cache)
        self.assertEqual(cache["good"], {"value": 1})

    def test_memcache_adapter_serializable_after_skipped_value(self):
        """Cache remains usable after a skipped non-serializable value."""
        client = FakeMemcacheClient()
        cache = MemcacheAdapter(client, "example.function", ttl=120)

        cache["bad"] = {1, 2, 3}  # skipped (set is not JSON-serializable)
        cache["good"] = {"value": 1}  # stored normally

        self.assertNotIn("bad", cache)
        self.assertIn("good", cache)
        self.assertEqual(cache["good"], {"value": 1})

    def test_ram_adapter_expires_from_write_time(self):
        clock = FakeClock()
        cache = RAMCacheTTLAdapter(
            RAMCache(),
            "example.function",
            ttl=10,
            clock=clock,
        )
        cache["key"] = {"value": [1, 2]}

        clock.advance(9)
        self.assertEqual(cache["key"], {"value": [1, 2]})
        clock.advance(1)
        self.assertIsNone(cache.get("key"))

    def test_ram_adapter_rewrite_resets_expiration(self):
        clock = FakeClock()
        cache = RAMCacheTTLAdapter(
            RAMCache(),
            "example.function",
            ttl=10,
            clock=clock,
        )
        cache["key"] = "first"
        clock.advance(9)
        cache["key"] = "second"
        clock.advance(9)

        self.assertEqual(cache["key"], "second")

    def test_ram_adapter_ignores_entries_without_ttl_metadata(self):
        ramcache = RAMCache()
        legacy = RAMCacheAdapter(ramcache, "example.function")
        cache = RAMCacheTTLAdapter(
            ramcache,
            "example.function",
            ttl=10,
            clock=FakeClock(),
        )
        legacy["key"] = "legacy"

        self.assertIsNone(cache.get("key"))
        self.assertEqual(legacy.get("key"), "legacy")


class CacheChooserTest(unittest.TestCase):
    """Verify the policy utility contract and environment configuration."""

    def test_implements_cache_chooser(self):
        self.assertTrue(verifyObject(ICacheChooser, CacheChooser()))

    def test_cache_redis_db_defaults_to_1(self):
        """Redis DB defaults to 1 to avoid collision with eea.api.redirector."""
        with patch.dict(os.environ, {}, clear=True):
            chooser = CacheChooser()
            self.assertEqual(chooser.redis_db, 1)

    def test_reads_backend_order_and_ttl(self):
        environment = {
            "CACHE_BACKEND_ORDER": "memcached, redis, ram",
            "CACHE_TTL": "90",
        }
        with patch.dict(os.environ, environment, clear=True):
            chooser = CacheChooser()
            self.assertEqual(
                chooser.backend_order,
                ["memcached", "redis", "ram"],
            )
            self.assertEqual(chooser.ttl, 90)

    def test_invalid_or_non_positive_ttl_uses_default(self):
        for value in ("invalid", "0", "-10"):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"CACHE_TTL": value}, clear=True):
                    self.assertEqual(CacheChooser().ttl, 300)

    @patch("eea.volto.policy.cache.component.queryUtility")
    def test_ram_backend_receives_configured_ttl(self, query_utility):
        query_utility.return_value = RAMCache()
        environment = {
            "CACHE_BACKEND_ORDER": "ram",
            "CACHE_TTL": "90",
        }

        with patch.dict(os.environ, environment, clear=True):
            cache = CacheChooser()("example.function")

        self.assertIsInstance(cache, RAMCacheTTLAdapter)
        self.assertEqual(cache.ttl, 90)

    def test_policy_registers_global_cache_chooser_override(self):
        overrides = Path(__file__).parents[1] / "overrides.zcml"
        root = ElementTree.parse(overrides).getroot()
        utilities = root.findall("{http://namespaces.zope.org/zope}utility")

        self.assertIn(
            ".cache.CacheChooser",
            [utility.attrib.get("factory") for utility in utilities],
        )


def test_suite():
    """Test suite."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
