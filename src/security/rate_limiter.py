"""
Rate Limiting Module

Provides rate limiting functionality to prevent abuse and control API costs.
Supports both in-memory and Redis-based storage.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import threading


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """
    Rate limiter with sliding window algorithm

    Supports:
    - Multiple time windows (e.g., 10/hour, 3/10min)
    - Per-IP and per-user rate limiting
    - In-memory storage (can be extended to Redis)
    - Thread-safe operations
    """

    def __init__(self, use_redis: bool = False, redis_client=None):
        """
        Initialize rate limiter

        Args:
            use_redis: Whether to use Redis for distributed rate limiting
            redis_client: Redis client instance (required if use_redis=True)
        """
        self.use_redis = use_redis
        self.redis_client = redis_client

        # In-memory storage: {identifier: [timestamps]}
        self.requests: Dict[str, List[float]] = defaultdict(list)

        # Lock for thread safety
        self.lock = threading.Lock()

        # MEMORY LEAK FIX: Track last cleanup time and cleanup counter
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # Clean every hour
        self.max_keys = 10000  # Limit total number of keys
        self.requests_since_cleanup = 0

        # Configuration
        self.limits = {
            'hourly': {'max_requests': 10, 'window_minutes': 60},
            'burst': {'max_requests': 3, 'window_minutes': 10},
            'daily': {'max_requests': 50, 'window_minutes': 1440},
        }

    def check_rate_limit(
        self,
        identifier: str,
        limit_type: str = 'hourly'
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if request is within rate limit

        Args:
            identifier: User identifier (IP, user_id, etc.)
            limit_type: Type of limit to check ('hourly', 'burst', 'daily')

        Returns:
            Tuple of (allowed, error_message, seconds_until_reset)
        """
        if limit_type not in self.limits:
            raise ValueError(f"Invalid limit type: {limit_type}")

        config = self.limits[limit_type]
        max_requests = config['max_requests']
        window_minutes = config['window_minutes']

        if self.use_redis and self.redis_client:
            return self._check_rate_limit_redis(identifier, limit_type, max_requests, window_minutes)
        else:
            return self._check_rate_limit_memory(identifier, limit_type, max_requests, window_minutes)

    def _check_rate_limit_memory(
        self,
        identifier: str,
        limit_type: str,
        max_requests: int,
        window_minutes: int
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check rate limit using in-memory storage

        Returns:
            Tuple of (allowed, error_message, seconds_until_reset)
        """
        with self.lock:
            now = time.time()
            window_start = now - (window_minutes * 60)

            # Create unique key for this limit type
            key = f"{identifier}:{limit_type}"

            # Clean old requests outside the window
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]

            # MEMORY LEAK FIX: Remove empty keys and trigger periodic cleanup
            if not self.requests[key]:
                del self.requests[key]
                return True, None, None

            # Periodic cleanup to prevent unbounded growth
            # More aggressive: cleanup every 50 requests OR every 30 minutes
            self.requests_since_cleanup += 1
            time_since_cleanup = time.time() - self.last_cleanup
            if (self.requests_since_cleanup >= 50 or time_since_cleanup >= 1800):  # 1800s = 30 min
                self._cleanup_old_keys()

            # Get current request count
            request_count = len(self.requests[key])

            # Check if limit exceeded
            if request_count >= max_requests:
                # Calculate when the oldest request will expire
                oldest_request = min(self.requests[key])
                seconds_until_reset = int((oldest_request + window_minutes * 60) - now)

                error_msg = (
                    f"Rate limit exceeded. "
                    f"Maximum {max_requests} requests per {window_minutes} minutes. "
                    f"Please try again in {seconds_until_reset} seconds."
                )

                return False, error_msg, seconds_until_reset

            # Add current request
            self.requests[key].append(now)

            # Calculate remaining requests
            remaining = max_requests - request_count - 1

            return True, None, None

    def _check_rate_limit_redis(
        self,
        identifier: str,
        limit_type: str,
        max_requests: int,
        window_minutes: int
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check rate limit using Redis (for distributed systems)

        Returns:
            Tuple of (allowed, error_message, seconds_until_reset)
        """
        if not self.redis_client:
            raise ValueError("Redis client not provided")

        now = time.time()
        window_seconds = window_minutes * 60
        window_start = now - window_seconds

        key = f"rate_limit:{identifier}:{limit_type}"

        try:
            # Use Redis sorted set with timestamps as scores
            pipe = self.redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            pipe.zcard(key)

            # Execute pipeline
            _, count = pipe.execute()

            if count >= max_requests:
                # Get oldest request
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    seconds_until_reset = int((oldest_time + window_seconds) - now)
                else:
                    seconds_until_reset = window_seconds

                error_msg = (
                    f"Rate limit exceeded. "
                    f"Maximum {max_requests} requests per {window_minutes} minutes. "
                    f"Please try again in {seconds_until_reset} seconds."
                )

                return False, error_msg, seconds_until_reset

            # Add current request
            self.redis_client.zadd(key, {str(now): now})

            # Set expiry on the key
            self.redis_client.expire(key, window_seconds)

            return True, None, None

        except Exception as e:
            # If Redis fails, allow the request but log error
            print(f"Redis error in rate limiter: {e}")
            return True, None, None

    def check_all_limits(self, identifier: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check all rate limits for an identifier

        Args:
            identifier: User identifier

        Returns:
            Tuple of (allowed, error_message, seconds_until_reset)
        """
        # Check burst limit first (strictest)
        allowed, msg, reset = self.check_rate_limit(identifier, 'burst')
        if not allowed:
            return False, msg, reset

        # Check hourly limit
        allowed, msg, reset = self.check_rate_limit(identifier, 'hourly')
        if not allowed:
            return False, msg, reset

        # Check daily limit
        allowed, msg, reset = self.check_rate_limit(identifier, 'daily')
        if not allowed:
            return False, msg, reset

        return True, None, None

    def get_remaining_quota(self, identifier: str, limit_type: str = 'hourly') -> int:
        """
        Get remaining requests for an identifier

        Args:
            identifier: User identifier
            limit_type: Type of limit to check

        Returns:
            Number of remaining requests
        """
        if limit_type not in self.limits:
            raise ValueError(f"Invalid limit type: {limit_type}")

        config = self.limits[limit_type]
        max_requests = config['max_requests']
        window_minutes = config['window_minutes']

        with self.lock:
            now = time.time()
            window_start = now - (window_minutes * 60)

            key = f"{identifier}:{limit_type}"

            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]

            request_count = len(self.requests[key])
            remaining = max(0, max_requests - request_count)

            return remaining

    def reset_limits(self, identifier: str):
        """
        Reset all limits for an identifier (admin function)

        Args:
            identifier: User identifier to reset
        """
        with self.lock:
            # Remove all keys for this identifier
            keys_to_remove = [key for key in self.requests.keys() if key.startswith(f"{identifier}:")]
            for key in keys_to_remove:
                del self.requests[key]

    def _cleanup_old_keys(self):
        """
        MEMORY LEAK FIX: Clean up inactive keys to prevent unbounded growth

        Removes keys with:
        - Empty timestamp lists
        - All timestamps older than the longest window (daily)
        - Keys beyond max_keys limit (keeps most recently accessed)
        """
        now = time.time()
        longest_window = max(config['window_minutes'] for config in self.limits.values()) * 60
        window_start = now - longest_window

        # Find keys to remove (old or empty)
        keys_to_remove = []
        for key, timestamps in self.requests.items():
            if not timestamps or all(t < window_start for t in timestamps):
                keys_to_remove.append(key)

        # Remove old keys
        for key in keys_to_remove:
            del self.requests[key]

        # If still over limit, remove least recently used keys
        if len(self.requests) > self.max_keys:
            # Sort by most recent timestamp
            sorted_keys = sorted(
                self.requests.items(),
                key=lambda x: max(x[1]) if x[1] else 0
            )

            # Remove oldest keys
            keys_to_keep = len(self.requests) - self.max_keys
            for key, _ in sorted_keys[:keys_to_keep]:
                del self.requests[key]

        # Update cleanup tracking
        self.last_cleanup = now
        self.requests_since_cleanup = 0

    def configure_limits(
        self,
        hourly: Optional[int] = None,
        burst: Optional[int] = None,
        daily: Optional[int] = None
    ):
        """
        Configure rate limits

        Args:
            hourly: Max requests per hour
            burst: Max requests per 10 minutes
            daily: Max requests per day
        """
        if hourly is not None:
            self.limits['hourly']['max_requests'] = hourly

        if burst is not None:
            self.limits['burst']['max_requests'] = burst

        if daily is not None:
            self.limits['daily']['max_requests'] = daily

    def get_client_identifier(self, request=None, user_id: Optional[str] = None) -> str:
        """
        Get unique identifier for rate limiting

        Args:
            request: Streamlit request object (if available)
            user_id: User ID (if authenticated)

        Returns:
            Unique identifier string
        """
        # Prefer user_id if available
        if user_id:
            return f"user:{user_id}"

        # Try to get IP from request
        if request:
            # Streamlit doesn't easily expose client IP
            # This is a placeholder - in production, you'd extract from headers
            try:
                # Get IP from X-Forwarded-For or similar
                ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
                if ip:
                    return f"ip:{ip}"
            except (AttributeError, KeyError, IndexError):
                # Request doesn't have headers or IP extraction failed
                pass

        # Fallback to session-based identifier
        import streamlit as st
        if hasattr(st, 'session_state') and hasattr(st.session_state, 'session_id'):
            return f"session:{st.session_state.session_id}"

        # Last resort: use a default identifier (not ideal for production)
        return "default_user"


class RateLimitDecorator:
    """
    Decorator for rate limiting functions
    """

    def __init__(self, rate_limiter: RateLimiter, limit_type: str = 'hourly'):
        self.rate_limiter = rate_limiter
        self.limit_type = limit_type

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # Get identifier from kwargs or use default
            identifier = kwargs.get('identifier', 'default_user')

            # Check rate limit
            allowed, error_msg, reset_time = self.rate_limiter.check_rate_limit(
                identifier, self.limit_type
            )

            if not allowed:
                raise RateLimitExceeded(error_msg)

            # Execute function
            return func(*args, **kwargs)

        return wrapper


def main():
    """Test rate limiter"""
    limiter = RateLimiter()

    # Configure for testing
    limiter.configure_limits(hourly=5, burst=2, daily=10)

    test_user = "test_user_123"

    print("Testing rate limiter...")

    # Test burst limit (2 per 10 minutes)
    print("\n--- Testing Burst Limit (2 per 10 minutes) ---")
    for i in range(3):
        allowed, msg, reset = limiter.check_rate_limit(test_user, 'burst')
        remaining = limiter.get_remaining_quota(test_user, 'burst')

        if allowed:
            print(f"Request {i+1}: ALLOWED (Remaining: {remaining})")
        else:
            print(f"Request {i+1}: BLOCKED - {msg}")

    # Reset for next test
    limiter.reset_limits(test_user)

    # Test hourly limit (5 per hour)
    print("\n--- Testing Hourly Limit (5 per hour) ---")
    for i in range(6):
        allowed, msg, reset = limiter.check_rate_limit(test_user, 'hourly')
        remaining = limiter.get_remaining_quota(test_user, 'hourly')

        if allowed:
            print(f"Request {i+1}: ALLOWED (Remaining: {remaining})")
        else:
            print(f"Request {i+1}: BLOCKED - {msg}")

    print("\n--- Testing check_all_limits ---")
    limiter.reset_limits("user2")
    allowed, msg, reset = limiter.check_all_limits("user2")
    print(f"All limits check: {'PASSED' if allowed else 'FAILED'}")


if __name__ == "__main__":
    main()
