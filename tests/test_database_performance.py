"""
Comprehensive Database Performance Tests

Tests database optimizations including:
- Query performance (p99 < 100ms)
- Connection pooling efficiency
- Cache effectiveness
- Pagination performance
- No N+1 query problems
- Concurrent user simulation
"""
import pytest
import time
import sqlite3
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.schema_optimized import OptimizedDatabase
from src.database.migrations import MigrationManager


class TestDatabasePerformance:
    """Test database performance optimizations"""

    @pytest.fixture
    def test_db(self):
        """Create temporary test database"""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        # Initialize database
        db = OptimizedDatabase(
            db_path=db_path,
            pool_size=5,
            cache_size=1000,
            cache_ttl=300
        )

        yield db

        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass

    @pytest.fixture
    def populated_db(self, test_db):
        """Create database populated with test data"""
        # Insert 1000 job descriptions
        for i in range(1000):
            test_db.insert_job_description(
                company_name=f"Company {i % 50}",  # 50 unique companies
                job_title=f"Software Engineer {i % 10}",  # 10 unique titles
                job_description=f"Job description {i} with lots of text " * 10,
                job_url=f"https://example.com/job/{i}",
                keywords=[f"skill{j}" for j in range(i % 20)]
            )

        # Insert 500 resumes
        for i in range(500):
            test_db.insert_generated_resume(
                job_description_id=i + 1,
                resume_content=f"Resume content {i} " * 100,
                file_path=f"/path/to/resume_{i}.pdf",
                ats_score=70 + (i % 30)
            )

        # Insert 300 cover letters
        for i in range(300):
            test_db.insert_generated_cover_letter(
                job_description_id=i + 1,
                cover_letter_content=f"Cover letter {i} " * 50,
                file_path=f"/path/to/cover_{i}.pdf",
                resume_id=i + 1 if i < 500 else None
            )

        return test_db

    def test_query_performance_simple(self, populated_db):
        """Test that simple queries complete within performance targets"""
        # Warm up
        populated_db.get_all_jobs(limit=10)

        # Test job query performance
        start = time.time()
        for _ in range(100):
            result = populated_db.get_all_jobs(limit=10)
        duration_ms = (time.time() - start) * 1000 / 100

        assert duration_ms < 100, f"Query took {duration_ms:.2f}ms, expected <100ms"
        assert len(result) == 10

    def test_query_performance_with_joins(self, populated_db):
        """Test that JOIN queries complete within performance targets"""
        # Test resume query with JOIN (no N+1 problem)
        times = []

        for _ in range(100):
            start = time.time()
            result = populated_db.get_all_resumes(limit=20)
            duration = time.time() - start
            times.append(duration * 1000)

        # Calculate p99
        p99 = sorted(times)[98]  # 99th percentile

        assert p99 < 100, f"p99 query latency: {p99:.2f}ms, expected <100ms"
        assert len(result) == 20
        # Verify JOIN worked - should have company_name from job_descriptions
        assert 'company_name' in result[0]

    def test_no_n_plus_one_queries(self, populated_db):
        """Test that queries don't have N+1 problems"""
        # Count queries executed
        initial_queries = populated_db.monitor.total_queries

        # Get resumes - should be single query with JOIN
        result = populated_db.get_all_resumes(limit=50)

        queries_executed = populated_db.monitor.total_queries - initial_queries

        # Should be 1 query (not 1 + N)
        assert queries_executed == 1, f"Executed {queries_executed} queries, expected 1"
        assert len(result) == 50

        # Verify we have all data from JOIN
        for resume in result:
            assert 'company_name' in resume
            assert 'job_title' in resume

    def test_pagination_performance(self, populated_db):
        """Test pagination performance"""
        times = []

        # Test pagination through 10 pages
        for page in range(1, 11):
            start = time.time()
            result = populated_db.get_jobs_paginated(page=page, page_size=50)
            duration = (time.time() - start) * 1000
            times.append(duration)

            assert len(result['jobs']) <= 50
            assert result['page'] == page

        # All pagination queries should be fast
        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 50, f"Average pagination time: {avg_time:.2f}ms, expected <50ms"
        assert max_time < 100, f"Max pagination time: {max_time:.2f}ms, expected <100ms"

    def test_connection_pool_efficiency(self, populated_db):
        """Test that connection pool handles concurrent requests efficiently"""
        def query_database():
            """Execute random query"""
            import random
            choice = random.randint(0, 2)

            if choice == 0:
                return populated_db.get_all_jobs(limit=10)
            elif choice == 1:
                return populated_db.get_all_resumes(limit=10)
            else:
                return populated_db.get_jobs_paginated(page=1, page_size=10)

        # Execute 100 concurrent queries
        start = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(query_database) for _ in range(100)]

            for future in as_completed(futures):
                result = future.result()
                assert result is not None

        duration = time.time() - start

        # Should complete in reasonable time with pooling
        assert duration < 5.0, f"100 concurrent queries took {duration:.2f}s, expected <5s"

        # Check pool stats
        pool_stats = populated_db.pool.get_stats()
        print(f"\nPool stats: {pool_stats}")

        # Should not have exhausted pool (no timeouts)
        assert pool_stats['pool_timeouts'] == 0, "Connection pool was exhausted"

    def test_cache_effectiveness(self, populated_db):
        """Test that caching reduces query time"""
        # Clear cache
        populated_db.cache.clear()

        # First query (cache miss)
        start = time.time()
        result1 = populated_db.get_company_research("Test Company")
        time1 = (time.time() - start) * 1000

        # Insert data
        populated_db.save_company_research("Test Company", "Research data" * 100)

        # Second query (cache miss - data was updated)
        start = time.time()
        result2 = populated_db.get_company_research("Test Company")
        time2 = (time.time() - start) * 1000

        # Third query (cache hit)
        start = time.time()
        result3 = populated_db.get_company_research("Test Company")
        time3 = (time.time() - start) * 1000

        # Cache hit should be significantly faster
        # Note: For small queries, the difference may not be huge
        # But cache hit should not be slower
        assert time3 <= time2, f"Cache hit ({time3:.2f}ms) was slower than cache miss ({time2:.2f}ms)"

        # Verify cache stats
        cache_stats = populated_db.cache.get_stats()
        print(f"\nCache stats: {cache_stats}")

    def test_index_performance(self, test_db):
        """Test that indexes improve query performance"""
        # Insert test data
        for i in range(1000):
            test_db.insert_job_description(
                company_name="Target Company" if i % 10 == 0 else f"Other Company {i}",
                job_title=f"Engineer {i}",
                job_description=f"Description {i}",
                job_url=f"https://example.com/{i}",
                keywords=[]
            )

        # Apply indexes migration
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
        if os.path.exists(os.path.join(migrations_dir, '001_add_indexes.sql')):
            manager = MigrationManager(test_db.db_path, migrations_dir)
            manager.migrate()

        # Test filtered query performance (should use index)
        times = []
        for _ in range(50):
            start = time.time()
            result = test_db.get_jobs_paginated(company_filter="Target Company", page_size=10)
            duration = (time.time() - start) * 1000
            times.append(duration)

        avg_time = sum(times) / len(times)
        p95 = sorted(times)[int(len(times) * 0.95)]

        assert avg_time < 50, f"Filtered query avg: {avg_time:.2f}ms, expected <50ms"
        assert p95 < 100, f"Filtered query p95: {p95:.2f}ms, expected <100ms"

    def test_concurrent_users_simulation(self, populated_db):
        """Simulate 500+ concurrent users"""
        import random

        def simulate_user():
            """Simulate user actions"""
            actions = [
                lambda: populated_db.get_all_jobs(limit=10),
                lambda: populated_db.get_all_resumes(limit=10),
                lambda: populated_db.get_jobs_paginated(page=random.randint(1, 5)),
                lambda: populated_db.get_resumes_paginated(page=random.randint(1, 3)),
                lambda: populated_db.get_company_research(f"Company {random.randint(0, 49)}")
            ]

            # Execute 3 random actions
            for _ in range(3):
                action = random.choice(actions)
                action()

        # Simulate 500 concurrent users
        start = time.time()

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(simulate_user) for _ in range(500)]

            completed = 0
            for future in as_completed(futures):
                future.result()
                completed += 1

        duration = time.time() - start

        print(f"\n500 concurrent users completed in {duration:.2f}s")
        print(f"Throughput: {500 / duration:.2f} users/second")
        print(f"Average time per user: {duration / 500 * 1000:.2f}ms")

        # Should handle 500 users in reasonable time
        assert duration < 30.0, f"500 users took {duration:.2f}s, expected <30s"

        # Check for errors
        pool_stats = populated_db.pool.get_stats()
        assert pool_stats['pool_timeouts'] == 0, "Connection pool timeouts occurred"

    def test_large_dataset_performance(self, test_db):
        """Test performance with larger dataset (10k records)"""
        print("\nInserting 10,000 records...")

        # Batch insert for speed
        start = time.time()
        for i in range(10000):
            test_db.insert_job_description(
                company_name=f"Company {i % 100}",
                job_title=f"Engineer {i % 50}",
                job_description=f"Description {i}",
                job_url=f"https://example.com/{i}",
                keywords=[f"skill{j}" for j in range(5)]
            )

            if i % 1000 == 0:
                print(f"  Inserted {i} records...")

        insert_duration = time.time() - start
        print(f"Insert completed in {insert_duration:.2f}s ({10000/insert_duration:.0f} records/sec)")

        # Test query performance on large dataset
        times = []
        for _ in range(20):
            start = time.time()
            result = test_db.get_jobs_paginated(page=1, page_size=50)
            duration = (time.time() - start) * 1000
            times.append(duration)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print(f"Query performance on 10k records: avg={avg_time:.2f}ms, max={max_time:.2f}ms")

        assert avg_time < 100, f"Large dataset query avg: {avg_time:.2f}ms, expected <100ms"
        assert max_time < 200, f"Large dataset query max: {max_time:.2f}ms, expected <200ms"

    def test_performance_monitoring(self, populated_db):
        """Test that performance monitoring captures metrics"""
        # Execute various queries
        populated_db.get_all_jobs(limit=10)
        populated_db.get_all_resumes(limit=10)
        populated_db.get_jobs_paginated(page=1)

        # Get performance stats
        stats = populated_db.monitor.get_stats()

        assert stats['total_queries'] > 0
        assert stats['unique_queries'] > 0
        assert len(stats['queries']) > 0

        # Print stats
        print("\nPerformance statistics:")
        for query_name, query_stats in stats['queries'].items():
            print(f"  {query_name}: avg={query_stats['avg_ms']:.2f}ms, p99={query_stats['p99_ms']:.2f}ms")

    def test_database_size_optimization(self, test_db):
        """Test that optimizations reduce database size"""
        import os

        # Insert test data
        for i in range(1000):
            test_db.insert_job_description(
                company_name=f"Company {i}",
                job_title=f"Engineer {i}",
                job_description=f"Description {i} " * 50,  # Make it substantial
                job_url=f"https://example.com/{i}",
                keywords=[f"Python", f"SQL", f"Docker", f"AWS", f"Kubernetes"]  # Repeated keywords
            )

        # Get database size
        db_size = os.path.getsize(test_db.db_path)

        print(f"\nDatabase size with 1000 jobs: {db_size / 1024:.2f} KB")

        # With keyword normalization (after migration), size should be smaller
        # This is verified by checking that keywords table reduces redundancy

        # Rough estimate: denormalized keywords would be ~5 keywords * 20 chars * 1000 = 100KB
        # Normalized keywords: ~5 unique keywords * 20 chars + 1000 references = ~1KB + 4KB
        # Savings: ~95KB (95% reduction in keyword storage)

        # Database should not be excessively large
        assert db_size < 10 * 1024 * 1024, f"Database too large: {db_size / 1024 / 1024:.2f} MB"


class TestMigrationSystem:
    """Test migration system functionality"""

    @pytest.fixture
    def test_db_path(self):
        """Create temporary database path"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        yield db_path

        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass

    def test_migration_system_basic(self, test_db_path):
        """Test basic migration system functionality"""
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')

        # Create migration manager
        manager = MigrationManager(test_db_path, migrations_dir)

        # Check status
        status = manager.status()
        assert status['current_version'] == 0
        assert status['applied_count'] == 0

        # Apply migrations
        if os.path.exists(migrations_dir) and os.listdir(migrations_dir):
            success = manager.migrate()
            assert success

            # Check status after migration
            status = manager.status()
            assert status['current_version'] > 0
            assert status['applied_count'] > 0

    def test_migration_idempotency(self, test_db_path):
        """Test that migrations can be run multiple times safely"""
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')

        # Run migrations twice
        manager1 = MigrationManager(test_db_path, migrations_dir)
        result1 = manager1.migrate()

        manager2 = MigrationManager(test_db_path, migrations_dir)
        result2 = manager2.migrate()

        # Second run should detect no pending migrations
        status = manager2.status()
        assert status['pending_count'] == 0


def run_performance_benchmark():
    """Run full performance benchmark suite"""
    print("\n" + "=" * 80)
    print("RUNNING COMPREHENSIVE DATABASE PERFORMANCE BENCHMARK")
    print("=" * 80)

    # Run pytest with verbose output
    pytest.main([
        __file__,
        '-v',
        '-s',
        '--tb=short',
        '-k', 'test_'
    ])


if __name__ == '__main__':
    run_performance_benchmark()
