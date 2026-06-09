"""
Comprehensive cache implementation tests.

Tests the fixes for:
1. Thread safety with locks
2. TTL expiration handling
3. Duplicate endpoint removal
4. Cache statistics and eviction
"""

import sys
import time
import threading
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.cache import InMemoryCache, make_file_cache_key, make_function_cache_key
from app.routers.analysis import full_analysis, CodePayload
from pydantic import BaseModel


class TestCacheBasics:
    """Test basic cache operations."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = InMemoryCache()
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1", f"Expected 'value1', got {result}"
        print("✓ test_set_and_get passed")

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = InMemoryCache()
        result = cache.get("nonexistent")

        assert result is None, f"Expected None, got {result}"
        print("✓ test_get_nonexistent_key passed")

    def test_delete(self):
        """Test deleting a key."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.delete("key1")

        result = cache.get("key1")
        assert result is None, f"Expected None after delete, got {result}"
        print("✓ test_delete passed")

    def test_clear(self):
        """Test clearing the entire cache."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        print("✓ test_clear passed")


class TestCacheTTL:
    """Test TTL (time-to-live) functionality."""

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = InMemoryCache()
        cache.set("key1", "value1", ttl_seconds=1)

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for TTL to expire
        time.sleep(1.1)

        # Should now be None (expired)
        result = cache.get("key1")
        assert result is None, f"Expected None after TTL expiration, got {result}"
        print("✓ test_ttl_expiration passed")

    def test_ttl_not_expired(self):
        """Test that entries don't expire before TTL."""
        cache = InMemoryCache()
        cache.set("key1", "value1", ttl_seconds=2)

        # Check after short delay
        time.sleep(0.5)

        result = cache.get("key1")
        assert result == "value1", f"Expected 'value1', got {result}"
        print("✓ test_ttl_not_expired passed")

    def test_ttl_invalid_value(self):
        """Test that non-positive ttl_seconds raises ValueError."""
        cache = InMemoryCache()
        try:
            cache.set("key1", "value1", ttl_seconds=0)
            raise AssertionError("Expected ValueError for ttl_seconds=0")
        except ValueError:
            pass

        try:
            cache.set("key2", "value2", ttl_seconds=-5)
            raise AssertionError("Expected ValueError for ttl_seconds=-5")
        except ValueError:
            pass

        print("✓ test_ttl_invalid_value passed")


class TestCacheStats:
    """Test cache statistics tracking."""

    def test_hit_miss_counting(self):
        """Test that hits and misses are counted correctly."""
        cache = InMemoryCache()
        cache.set("key1", "value1")

        # Hit
        cache.get("key1")

        # Miss
        cache.get("nonexistent")

        stats = cache.stats()
        assert stats["hits"] == 1, f"Expected 1 hit, got {stats['hits']}"
        assert stats["misses"] == 1, f"Expected 1 miss, got {stats['misses']}"
        assert stats["hit_rate"] == 50.0, f"Expected 50% hit rate, got {stats['hit_rate']}"
        print("✓ test_hit_miss_counting passed")

    def test_stats_total_keys(self):
        """Test that stats reports correct number of keys."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        stats = cache.stats()
        assert stats["total_keys"] == 3, f"Expected 3 keys, got {stats['total_keys']}"
        print("✓ test_stats_total_keys passed")


class TestCacheEviction:
    """Test cache eviction of expired entries."""

    def test_evict_expired(self):
        """Test that evict_expired removes expired entries."""
        cache = InMemoryCache()
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=10)

        time.sleep(1.1)

        evicted_count = cache.evict_expired()
        assert evicted_count == 1, f"Expected 1 evicted entry, got {evicted_count}"

        # key1 should be gone, key2 should still exist
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        print("✓ test_evict_expired passed")

    def test_evict_with_no_expired(self):
        """Test evict_expired when there are no expired entries."""
        cache = InMemoryCache()
        cache.set("key1", "value1", ttl_seconds=10)

        evicted_count = cache.evict_expired()
        assert evicted_count == 0, f"Expected 0 evicted entries, got {evicted_count}"
        print("✓ test_evict_with_no_expired passed")


class TestThreadSafety:
    """Test thread safety with concurrent access."""

    def test_concurrent_reads(self):
        """Test concurrent read operations."""
        cache = InMemoryCache()
        cache.set("key1", "value1")

        results = []

        def read_cache():
            for _ in range(100):
                val = cache.get("key1")
                results.append(val)

        threads = [threading.Thread(target=read_cache) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == "value1" for r in results), "Some reads failed"
        assert len(results) == 500, f"Expected 500 reads, got {len(results)}"
        print("✓ test_concurrent_reads passed")

    def test_concurrent_writes(self):
        """Test concurrent write operations."""
        cache = InMemoryCache()

        def write_cache(thread_id):
            for i in range(50):
                cache.set(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")

        threads = [threading.Thread(target=write_cache, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = cache.stats()
        assert stats["total_keys"] == 250, f"Expected 250 keys, got {stats['total_keys']}"
        print("✓ test_concurrent_writes passed")

    def test_concurrent_read_write(self):
        """Test concurrent read and write operations."""
        cache = InMemoryCache()
        cache.set("counter", 0)

        errors = []

        def mixed_operations():
            try:
                for i in range(50):
                    cache.set(f"key_{i}", f"value_{i}")
                    val = cache.get(f"key_{i}")
                    if val != f"value_{i}":
                        errors.append(f"Read mismatch: {val}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=mixed_operations) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"
        print("✓ test_concurrent_read_write passed")


class TestFileCacheKey:
    """Test file cache key generation."""

    def test_same_code_same_key(self):
        """Test that same code produces same cache key."""
        code1 = "def hello():\n    return 'world'"
        code2 = "def hello():\n    return 'world'"

        key1 = make_file_cache_key(code1)
        key2 = make_file_cache_key(code2)

        assert key1 == key2, "Same code should produce same key"
        print("✓ test_same_code_same_key passed")

    def test_different_code_different_key(self):
        """Test that different code produces different cache keys."""
        code1 = "def hello():\n    return 'world'"
        code2 = "def hello():\n    return 'universe'"

        key1 = make_file_cache_key(code1)
        key2 = make_file_cache_key(code2)

        assert key1 != key2, "Different code should produce different keys"
        print("✓ test_different_code_different_key passed")

    def test_function_cache_key_invalid_inputs(self):
        """Test that invalid inputs raise TypeError."""
        try:
            make_function_cache_key(None, "code")
            raise AssertionError("Expected TypeError for func_name None")
        except TypeError:
            pass

        try:
            make_function_cache_key("fn", None)
            raise AssertionError("Expected TypeError for source_code None")
        except TypeError:
            pass

        print("✓ test_function_cache_key_invalid_inputs passed")


class TestAnalysisEndpoint:
    """Test the /analysis/full endpoint caching."""

    def test_analysis_adds_cached_flag(self):
        """Test that analysis response includes cached flag."""
        simple_code = """
def greet(name):
    return f"Hello, {name}!"
"""
        payload = CodePayload(
            source_code=simple_code,
            filename="test.py"
        )

        # First call - should not be cached
        response = full_analysis(payload)
        assert "cached" in response, "Response should have 'cached' field"
        assert response["cached"] == False, "First call should not be cached"
        print("✓ Analysis response has cached field")

    def test_analysis_cache_hit(self):
        """Test that second call with same code is cached."""
        simple_code = """
def add(a, b):
    return a + b
"""
        payload = CodePayload(
            source_code=simple_code,
            filename="test.py"
        )

        # First call
        response1 = full_analysis(payload)
        assert response1["cached"] == False

        # Second call with same code - should hit cache
        response2 = full_analysis(payload)
        assert response2["cached"] == True, "Second call should hit cache"
        print("✓ test_analysis_cache_hit passed")

    def test_analysis_filename_updated_on_cache_hit(self):
        """Test that filename is updated on cache hit."""
        simple_code = "def test(): pass"

        # First upload with filename1
        payload1 = CodePayload(source_code=simple_code, filename="file1.py")
        response1 = full_analysis(payload1)

        # Second upload with different filename but same code
        payload2 = CodePayload(source_code=simple_code, filename="file2.py")
        response2 = full_analysis(payload2)

        assert response2["cached"] == True
        assert response2["filename"] == "file2.py", "Should update filename on cache hit"
        print("✓ test_analysis_filename_updated_on_cache_hit passed")


def run_all_tests():
    """Run all tests and report results."""
    test_classes = [
        TestCacheBasics,
        TestCacheTTL,
        TestCacheStats,
        TestCacheEviction,
        TestThreadSafety,
        TestFileCacheKey,
        TestAnalysisEndpoint,
    ]

    print("=" * 60)
    print("RUNNING COMPREHENSIVE CACHE TESTS")
    print("=" * 60)

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 40)

        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                passed_tests += 1
            except Exception as e:
                failed_tests.append((test_class.__name__, method_name, str(e)))
                print(f"✗ {method_name} FAILED: {e}")

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Total tests:  {total_tests}")
    print(f"Passed:       {passed_tests}")
    print(f"Failed:       {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for class_name, method_name, error in failed_tests:
            print(f"  - {class_name}.{method_name}: {error}")
        return False
    else:
        print("\n🎉 ALL TESTS PASSED!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
