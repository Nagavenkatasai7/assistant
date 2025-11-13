"""
Database Query Caching Layer
Provides in-memory caching for database queries with TTL and invalidation support
"""
import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from collections import OrderedDict
from datetime import datetime, timedelta


class CacheEntry:
    """Represents a single cache entry with metadata"""

    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.last_accessed = time.time()

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl_seconds <= 0:
            return False  # No expiration
        return (time.time() - self.created_at) > self.ttl_seconds

    def access(self) -> Any:
        """Record access and return value"""
        self.hits += 1
        self.last_accessed = time.time()
        return self.value


class DatabaseCache:
    """
    In-memory LRU cache for database queries

    Features:
    - LRU eviction policy
    - TTL support per entry
    - Pattern-based invalidation
    - Cache statistics
    - Thread-safe operations (for single-threaded SQLite usage)
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache

        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default TTL in seconds (0 = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'invalidations': 0
        }

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate cache key from function name and arguments

        Args:
            func_name: Name of the cached function
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            MD5 hash as cache key
        """
        # Skip 'self' argument for instance methods
        if args and hasattr(args[0], '__class__'):
            args = args[1:]

        # Create deterministic string representation
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': kwargs
        }

        # Use JSON for serialization with sorted keys
        key_string = json.dumps(key_data, sort_keys=True, default=str)

        # Generate hash
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.stats['misses'] += 1
            return None

        entry = self.cache[key]

        # Check expiration
        if entry.is_expired():
            del self.cache[key]
            self.stats['misses'] += 1
            return None

        # Move to end (LRU)
        self.cache.move_to_end(key)

        # Record hit and return value
        self.stats['hits'] += 1
        return entry.access()

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (None = use default)
        """
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl

        # Evict oldest entry if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)
            self.stats['evictions'] += 1

        # Create entry
        entry = CacheEntry(value, ttl_seconds)

        # Add to cache
        self.cache[key] = entry
        self.cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        """
        Delete specific cache entry

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            self.stats['invalidations'] += 1
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        self.stats['invalidations'] += count

    def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern

        Args:
            pattern: String pattern to match in cache keys

        Returns:
            Number of entries invalidated
        """
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]

        for key in keys_to_delete:
            del self.cache[key]

        count = len(keys_to_delete)
        self.stats['invalidations'] += count

        return count

    def invalidate_by_function(self, func_name: str) -> int:
        """
        Invalidate all cache entries for a specific function

        Args:
            func_name: Function name

        Returns:
            Number of entries invalidated
        """
        return self.invalidate(f'"function": "{func_name}"')

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        # Calculate memory usage estimate (rough)
        entry_sizes = []
        for entry in list(self.cache.values())[:100]:  # Sample first 100
            try:
                # Rough estimate: length of JSON representation
                size = len(json.dumps(entry.value, default=str))
                entry_sizes.append(size)
            except (TypeError, ValueError, OverflowError):
                # JSON serialization failed - use default estimate
                entry_sizes.append(1000)  # Default estimate

        avg_entry_size = sum(entry_sizes) / len(entry_sizes) if entry_sizes else 1000
        estimated_memory_kb = (len(self.cache) * avg_entry_size) / 1024

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size * 100,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self.stats['evictions'],
            'invalidations': self.stats['invalidations'],
            'estimated_memory_kb': estimated_memory_kb
        }

    def print_stats(self) -> None:
        """Print formatted cache statistics"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("DATABASE CACHE STATISTICS")
        print("=" * 60)
        print(f"Size:              {stats['size']:,} / {stats['max_size']:,} entries ({stats['utilization']:.1f}%)")
        print(f"Memory (estimate): {stats['estimated_memory_kb']:.1f} KB")
        print(f"Hit rate:          {stats['hit_rate']:.1f}% ({stats['hits']:,} hits / {stats['misses']:,} misses)")
        print(f"Evictions:         {stats['evictions']:,}")
        print(f"Invalidations:     {stats['invalidations']:,}")
        print("=" * 60 + "\n")

    def get_top_entries(self, limit: int = 10) -> list:
        """
        Get top cache entries by hit count

        Args:
            limit: Number of entries to return

        Returns:
            List of (key, hits, age_seconds) tuples
        """
        entries = [
            (key, entry.hits, time.time() - entry.created_at)
            for key, entry in self.cache.items()
        ]

        # Sort by hits descending
        entries.sort(key=lambda x: x[1], reverse=True)

        return entries[:limit]


def cached_query(cache: DatabaseCache, ttl_seconds: Optional[int] = None):
    """
    Decorator for caching database queries

    Usage:
        @cached_query(cache, ttl_seconds=300)
        def get_user(self, user_id):
            return self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    Args:
        cache: DatabaseCache instance
        ttl_seconds: TTL for this query (None = use cache default)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(func.__name__, args, kwargs)

            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute query
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl_seconds)

            return result

        # Add cache management methods to decorated function
        wrapper.invalidate_cache = lambda: cache.invalidate_by_function(func.__name__)
        wrapper.cache = cache

        return wrapper
    return decorator


def invalidate_on_write(cache: DatabaseCache, *patterns: str):
    """
    Decorator to invalidate cache entries on write operations

    Usage:
        @invalidate_on_write(cache, 'get_user', 'get_all_users')
        def update_user(self, user_id, data):
            self.cursor.execute("UPDATE users SET ... WHERE id = ?", ...)

    Args:
        cache: DatabaseCache instance
        patterns: Cache key patterns to invalidate

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute write operation
            result = func(*args, **kwargs)

            # Invalidate related cache entries
            for pattern in patterns:
                cache.invalidate_by_function(pattern)

            return result
        return wrapper
    return decorator


# Global cache instance (singleton pattern)
_global_cache: Optional[DatabaseCache] = None


def get_global_cache(max_size: int = 1000, default_ttl: int = 300) -> DatabaseCache:
    """
    Get or create global cache instance

    Args:
        max_size: Maximum cache size (only used on first call)
        default_ttl: Default TTL in seconds (only used on first call)

    Returns:
        Global DatabaseCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = DatabaseCache(max_size=max_size, default_ttl=default_ttl)
    return _global_cache


def clear_global_cache() -> None:
    """Clear global cache instance"""
    global _global_cache
    if _global_cache:
        _global_cache.clear()
