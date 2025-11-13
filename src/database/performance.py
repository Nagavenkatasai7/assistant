"""
Database Query Performance Monitoring
Provides decorators and utilities for tracking query performance
"""
import time
import logging
from functools import wraps
from typing import Callable, Dict, List, Optional
from collections import defaultdict
from datetime import datetime
import statistics


# Configure logging
logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """
    Monitor and track database query performance

    Features:
    - Query execution time tracking
    - Slow query detection and logging
    - Query statistics aggregation
    - Performance degradation alerts
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        """
        Initialize performance monitor

        Args:
            slow_query_threshold_ms: Threshold in ms to consider query slow
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_queries: List[Dict] = []
        self.total_queries = 0

    def record_query(
        self,
        query_name: str,
        execution_time_ms: float,
        query_text: Optional[str] = None,
        params: Optional[tuple] = None
    ) -> None:
        """
        Record query execution time

        Args:
            query_name: Name/identifier of the query
            execution_time_ms: Execution time in milliseconds
            query_text: Optional SQL query text
            params: Optional query parameters
        """
        self.total_queries += 1
        self.query_stats[query_name].append(execution_time_ms)

        # Log slow queries
        if execution_time_ms > self.slow_query_threshold_ms:
            slow_query_info = {
                'query_name': query_name,
                'execution_time_ms': execution_time_ms,
                'timestamp': datetime.now().isoformat(),
                'query_text': query_text,
                'params': str(params) if params else None
            }
            self.slow_queries.append(slow_query_info)

            logger.warning(
                f"Slow query detected: {query_name} took {execution_time_ms:.2f}ms "
                f"(threshold: {self.slow_query_threshold_ms}ms)"
            )

    def get_stats(self) -> dict:
        """
        Get aggregated query statistics

        Returns:
            Dictionary with query performance statistics
        """
        stats = {
            'total_queries': self.total_queries,
            'unique_queries': len(self.query_stats),
            'slow_queries_count': len(self.slow_queries),
            'queries': {}
        }

        # Calculate statistics for each query
        for query_name, times in self.query_stats.items():
            if times:
                stats['queries'][query_name] = {
                    'count': len(times),
                    'min_ms': min(times),
                    'max_ms': max(times),
                    'avg_ms': statistics.mean(times),
                    'median_ms': statistics.median(times),
                    'p95_ms': self._percentile(times, 95),
                    'p99_ms': self._percentile(times, 99),
                    'total_time_ms': sum(times)
                }

        return stats

    def _percentile(self, data: List[float], percentile: int) -> float:
        """
        Calculate percentile of data

        Args:
            data: List of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """
        Get recent slow queries

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of slow query dictionaries
        """
        return sorted(
            self.slow_queries,
            key=lambda x: x['execution_time_ms'],
            reverse=True
        )[:limit]

    def get_slowest_queries(self, limit: int = 10) -> List[tuple]:
        """
        Get queries with worst average performance

        Args:
            limit: Number of queries to return

        Returns:
            List of (query_name, avg_time_ms) tuples
        """
        avg_times = [
            (name, statistics.mean(times))
            for name, times in self.query_stats.items()
            if times
        ]

        return sorted(avg_times, key=lambda x: x[1], reverse=True)[:limit]

    def print_stats(self) -> None:
        """Print formatted performance statistics"""
        stats = self.get_stats()

        print("\n" + "=" * 80)
        print("DATABASE QUERY PERFORMANCE STATISTICS")
        print("=" * 80)
        print(f"Total queries:       {stats['total_queries']:,}")
        print(f"Unique queries:      {stats['unique_queries']}")
        print(f"Slow queries:        {stats['slow_queries_count']} (>{self.slow_query_threshold_ms}ms)")

        if stats['queries']:
            print("\nTop queries by average execution time:")
            print("-" * 80)
            print(f"{'Query Name':<40} {'Count':>8} {'Avg':>10} {'P95':>10} {'P99':>10}")
            print("-" * 80)

            # Sort by average time
            sorted_queries = sorted(
                stats['queries'].items(),
                key=lambda x: x[1]['avg_ms'],
                reverse=True
            )

            for query_name, query_stats in sorted_queries[:10]:
                print(
                    f"{query_name[:40]:<40} "
                    f"{query_stats['count']:>8,} "
                    f"{query_stats['avg_ms']:>9.2f}ms "
                    f"{query_stats['p95_ms']:>9.2f}ms "
                    f"{query_stats['p99_ms']:>9.2f}ms"
                )

        if self.slow_queries:
            print("\nRecent slow queries:")
            print("-" * 80)
            for query in self.get_slow_queries(5):
                print(f"  {query['query_name']}: {query['execution_time_ms']:.2f}ms at {query['timestamp']}")

        print("=" * 80 + "\n")

    def reset(self) -> None:
        """Reset all statistics"""
        self.query_stats.clear()
        self.slow_queries.clear()
        self.total_queries = 0


# Global monitor instance
_global_monitor: Optional[QueryPerformanceMonitor] = None


def get_global_monitor(slow_query_threshold_ms: float = 100.0) -> QueryPerformanceMonitor:
    """
    Get or create global performance monitor

    Args:
        slow_query_threshold_ms: Threshold for slow queries (only used on first call)

    Returns:
        Global QueryPerformanceMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = QueryPerformanceMonitor(slow_query_threshold_ms)
    return _global_monitor


def monitor_query_performance(
    monitor: Optional[QueryPerformanceMonitor] = None,
    query_name: Optional[str] = None
):
    """
    Decorator to monitor query execution performance

    Usage:
        @monitor_query_performance()
        def get_user(self, user_id):
            return self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    Args:
        monitor: QueryPerformanceMonitor instance (uses global if None)
        query_name: Custom query name (uses function name if None)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get monitor instance
            perf_monitor = monitor or get_global_monitor()

            # Use custom query name or function name
            q_name = query_name or func.__name__

            # Time the query
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time_ms = (time.time() - start_time) * 1000

                # Record performance
                perf_monitor.record_query(q_name, execution_time_ms)

                # Log if slow
                if execution_time_ms > perf_monitor.slow_query_threshold_ms:
                    logger.warning(
                        f"Slow query: {q_name} took {execution_time_ms:.2f}ms"
                    )
                else:
                    logger.debug(
                        f"Query: {q_name} took {execution_time_ms:.2f}ms"
                    )

        return wrapper
    return decorator


def log_query_plan(query: str, params: tuple = ()) -> Callable:
    """
    Decorator to log EXPLAIN QUERY PLAN for a query

    Usage:
        @log_query_plan("SELECT * FROM users WHERE id = ?")
        def get_user(self, user_id):
            return self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    Args:
        query: SQL query to explain
        params: Query parameters

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function normally
            result = func(*args, **kwargs)

            # Log query plan (only in debug mode)
            if logger.isEnabledFor(logging.DEBUG):
                try:
                    # Get connection from self (assumes instance method)
                    if args and hasattr(args[0], 'cursor'):
                        cursor = args[0].cursor
                        explain_query = f"EXPLAIN QUERY PLAN {query}"
                        plan = cursor.execute(explain_query, params).fetchall()

                        logger.debug(f"Query plan for {func.__name__}:")
                        for row in plan:
                            logger.debug(f"  {row}")
                except Exception as e:
                    logger.debug(f"Failed to get query plan: {e}")

            return result
        return wrapper
    return decorator


class QueryBenchmark:
    """
    Benchmark utility for comparing query performance

    Usage:
        benchmark = QueryBenchmark(cursor)
        benchmark.add_query("Original", "SELECT * FROM users WHERE name = ?", ("John",))
        benchmark.add_query("Indexed", "SELECT * FROM users WHERE id = ?", (123,))
        benchmark.run(iterations=1000)
        benchmark.print_results()
    """

    def __init__(self, cursor: Optional[object] = None):
        """
        Initialize benchmark

        Args:
            cursor: Database cursor (optional, can be set per query)
        """
        self.cursor = cursor
        self.queries: List[Dict] = []

    def add_query(
        self,
        name: str,
        query: str,
        params: tuple = (),
        cursor: Optional[object] = None
    ) -> None:
        """
        Add query to benchmark

        Args:
            name: Query identifier
            query: SQL query
            params: Query parameters
            cursor: Database cursor (uses instance cursor if None)
        """
        self.queries.append({
            'name': name,
            'query': query,
            'params': params,
            'cursor': cursor or self.cursor,
            'times': []
        })

    def run(self, iterations: int = 100) -> None:
        """
        Run benchmark

        Args:
            iterations: Number of times to execute each query
        """
        print(f"\nRunning benchmark with {iterations} iterations per query...")

        for query_info in self.queries:
            cursor = query_info['cursor']
            query = query_info['query']
            params = query_info['params']

            print(f"  Benchmarking: {query_info['name']}...", end=" ", flush=True)

            for _ in range(iterations):
                start_time = time.time()
                cursor.execute(query, params)
                cursor.fetchall()  # Ensure query completes
                execution_time_ms = (time.time() - start_time) * 1000
                query_info['times'].append(execution_time_ms)

            print("Done")

    def print_results(self) -> None:
        """Print benchmark results"""
        print("\n" + "=" * 80)
        print("QUERY BENCHMARK RESULTS")
        print("=" * 80)
        print(f"{'Query':<30} {'Min':>12} {'Avg':>12} {'Median':>12} {'P95':>12} {'P99':>12}")
        print("-" * 80)

        for query_info in self.queries:
            times = query_info['times']
            if times:
                print(
                    f"{query_info['name'][:30]:<30} "
                    f"{min(times):>11.3f}ms "
                    f"{statistics.mean(times):>11.3f}ms "
                    f"{statistics.median(times):>11.3f}ms "
                    f"{self._percentile(times, 95):>11.3f}ms "
                    f"{self._percentile(times, 99):>11.3f}ms"
                )

        print("=" * 80 + "\n")

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
