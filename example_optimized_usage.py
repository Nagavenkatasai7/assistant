#!/usr/bin/env python3
"""
Example Usage of Optimized Database

This file demonstrates how to use the optimized database layer
with all performance enhancements enabled.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.database.schema_optimized import OptimizedDatabase


def example_basic_operations():
    """Basic database operations"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Operations")
    print("=" * 80)

    # Initialize optimized database
    db = OptimizedDatabase(
        db_path="example.db",
        pool_size=5,
        cache_size=1000,
        cache_ttl=300
    )

    # Insert job description with keywords
    print("\n1. Inserting job description...")
    job_id = db.insert_job_description(
        company_name="Google",
        job_title="Senior Software Engineer",
        job_description="We are looking for an experienced software engineer...",
        job_url="https://careers.google.com/jobs/12345",
        keywords=["Python", "SQL", "Docker", "AWS", "Kubernetes"]
    )
    print(f"   ✓ Inserted job ID: {job_id}")

    # Insert resume
    print("\n2. Inserting resume...")
    resume_id = db.insert_generated_resume(
        job_description_id=job_id,
        resume_content="John Doe's resume...",
        file_path="/path/to/resume.pdf",
        ats_score=85
    )
    print(f"   ✓ Inserted resume ID: {resume_id}")

    # Insert cover letter
    print("\n3. Inserting cover letter...")
    cover_letter_id = db.insert_generated_cover_letter(
        job_description_id=job_id,
        cover_letter_content="Dear Hiring Manager...",
        file_path="/path/to/cover_letter.pdf",
        resume_id=resume_id
    )
    print(f"   ✓ Inserted cover letter ID: {cover_letter_id}")

    # Query data (automatically cached and pooled)
    print("\n4. Querying data...")
    jobs = db.get_all_jobs(limit=10)
    print(f"   ✓ Retrieved {len(jobs)} jobs")

    resumes = db.get_all_resumes(limit=10)
    print(f"   ✓ Retrieved {len(resumes)} resumes (with JOIN, no N+1!)")

    # Cleanup
    os.unlink("example.db")
    print("\n✓ Example completed successfully")


def example_pagination():
    """Pagination example"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Pagination")
    print("=" * 80)

    db = OptimizedDatabase(db_path="example.db")

    # Insert sample data
    print("\n1. Inserting 100 jobs...")
    for i in range(100):
        db.insert_job_description(
            company_name=f"Company {i % 10}",
            job_title=f"Engineer {i}",
            job_description=f"Job description {i}",
            job_url=f"https://example.com/{i}",
            keywords=[f"skill{j}" for j in range(5)]
        )
    print("   ✓ Inserted 100 jobs")

    # Paginate through results
    print("\n2. Paginating through results...")
    page = 1
    while True:
        result = db.get_jobs_paginated(page=page, page_size=20)

        print(f"   Page {result['page']} of {result['pages']}: {len(result['jobs'])} jobs")

        if page >= result['pages']:
            break
        page += 1

    # Filter and paginate
    print("\n3. Filtering by company...")
    result = db.get_jobs_paginated(
        page=1,
        page_size=10,
        company_filter="Company 5"
    )
    print(f"   ✓ Found {result['total']} jobs for 'Company 5'")

    # Cleanup
    os.unlink("example.db")
    print("\n✓ Example completed successfully")


def example_performance_monitoring():
    """Performance monitoring example"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Performance Monitoring")
    print("=" * 80)

    db = OptimizedDatabase(db_path="example.db")

    # Insert test data
    print("\n1. Inserting test data...")
    for i in range(50):
        db.insert_job_description(
            company_name=f"Company {i}",
            job_title=f"Engineer {i}",
            job_description=f"Description {i}",
            job_url=f"https://example.com/{i}",
            keywords=["Python", "SQL"]
        )
    print("   ✓ Inserted 50 jobs")

    # Execute various queries
    print("\n2. Executing queries...")
    for _ in range(20):
        db.get_all_jobs(limit=10)
        db.get_jobs_paginated(page=1, page_size=10)

    # Get performance statistics
    print("\n3. Performance Statistics:")
    stats = db.monitor.get_stats()
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Unique queries: {stats['unique_queries']}")
    print(f"   Slow queries: {stats['slow_queries_count']}")

    print("\n   Query performance:")
    for query_name, query_stats in stats['queries'].items():
        print(f"   - {query_name}:")
        print(f"     Avg: {query_stats['avg_ms']:.2f}ms")
        print(f"     P95: {query_stats['p95_ms']:.2f}ms")
        print(f"     P99: {query_stats['p99_ms']:.2f}ms")

    # Cleanup
    os.unlink("example.db")
    print("\n✓ Example completed successfully")


def example_cache_effectiveness():
    """Cache effectiveness example"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Cache Effectiveness")
    print("=" * 80)

    db = OptimizedDatabase(db_path="example.db")

    # Insert test data
    print("\n1. Inserting test data...")
    for i in range(10):
        db.insert_job_description(
            company_name=f"Company {i}",
            job_title=f"Engineer {i}",
            job_description=f"Description {i}",
            job_url=f"https://example.com/{i}",
            keywords=["Python"]
        )
    print("   ✓ Inserted 10 jobs")

    # Clear cache
    db.cache.clear()

    # First query (cache miss)
    print("\n2. First query (cache miss)...")
    import time
    start = time.time()
    db.get_job_by_id(1)
    time1 = (time.time() - start) * 1000
    print(f"   Time: {time1:.2f}ms")

    # Second query (cache hit)
    print("\n3. Second query (cache hit)...")
    start = time.time()
    db.get_job_by_id(1)
    time2 = (time.time() - start) * 1000
    print(f"   Time: {time2:.2f}ms")

    # Query multiple times to build cache
    print("\n4. Building cache with 50 queries...")
    for _ in range(50):
        db.get_all_jobs(limit=5)

    # Get cache statistics
    print("\n5. Cache Statistics:")
    cache_stats = db.cache.get_stats()
    print(f"   Size: {cache_stats['size']} / {cache_stats['max_size']}")
    print(f"   Hit rate: {cache_stats['hit_rate']:.1f}%")
    print(f"   Hits: {cache_stats['hits']}")
    print(f"   Misses: {cache_stats['misses']}")

    # Cleanup
    os.unlink("example.db")
    print("\n✓ Example completed successfully")


def example_connection_pool():
    """Connection pool example"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Connection Pool")
    print("=" * 80)

    db = OptimizedDatabase(db_path="example.db", pool_size=3)

    # Insert test data
    print("\n1. Inserting test data...")
    for i in range(20):
        db.insert_job_description(
            company_name=f"Company {i}",
            job_title=f"Engineer {i}",
            job_description=f"Description {i}",
            job_url=f"https://example.com/{i}",
            keywords=[]
        )
    print("   ✓ Inserted 20 jobs")

    # Simulate concurrent requests
    print("\n2. Simulating concurrent requests...")
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def query_database():
        return db.get_all_jobs(limit=5)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(query_database) for _ in range(50)]

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            completed += 1

    print(f"   ✓ Completed {completed} concurrent queries")

    # Get pool statistics
    print("\n3. Connection Pool Statistics:")
    pool_stats = db.pool.get_stats()
    print(f"   Pool size: {pool_stats['pool_size']}")
    print(f"   Active connections: {pool_stats['active_connections']}")
    print(f"   Pool checkouts: {pool_stats['pool_checkouts']}")
    print(f"   Overflow used: {pool_stats['overflow_used']}")
    print(f"   Pool timeouts: {pool_stats['pool_timeouts']}")

    # Cleanup
    os.unlink("example.db")
    print("\n✓ Example completed successfully")


def example_comprehensive_stats():
    """Comprehensive statistics example"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Comprehensive Statistics")
    print("=" * 80)

    db = OptimizedDatabase(db_path="example.db")

    # Insert test data
    print("\n1. Inserting test data...")
    for i in range(30):
        job_id = db.insert_job_description(
            company_name=f"Company {i % 5}",
            job_title=f"Engineer {i}",
            job_description=f"Description {i}",
            job_url=f"https://example.com/{i}",
            keywords=["Python", "SQL", "Docker"]
        )

        if i % 2 == 0:
            db.insert_generated_resume(
                job_description_id=job_id,
                resume_content=f"Resume {i}",
                file_path=f"/path/to/resume_{i}.pdf",
                ats_score=70 + (i % 30)
            )

    print("   ✓ Inserted 30 jobs and 15 resumes")

    # Execute queries to populate cache/performance stats
    print("\n2. Executing queries...")
    for _ in range(20):
        db.get_all_jobs(limit=10)
        db.get_all_resumes(limit=10)
        db.get_jobs_paginated(page=1)

    # Print comprehensive statistics
    print("\n3. Comprehensive Statistics:")
    db.print_statistics()

    # Cleanup
    os.unlink("example.db")
    print("\n✓ Example completed successfully")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("OPTIMIZED DATABASE USAGE EXAMPLES")
    print("=" * 80)
    print("\nThese examples demonstrate the key features of the optimized database:")
    print("  1. Basic operations with automatic optimization")
    print("  2. Pagination for large datasets")
    print("  3. Performance monitoring and statistics")
    print("  4. Cache effectiveness")
    print("  5. Connection pooling")
    print("  6. Comprehensive statistics")
    print("\n" + "=" * 80)

    try:
        example_basic_operations()
        example_pagination()
        example_performance_monitoring()
        example_cache_effectiveness()
        example_connection_pool()
        example_comprehensive_stats()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nKey takeaways:")
        print("  ✓ All operations use connection pooling automatically")
        print("  ✓ Frequently accessed data is cached")
        print("  ✓ All queries are monitored for performance")
        print("  ✓ No N+1 query problems (JOINs used)")
        print("  ✓ Pagination supports large datasets efficiently")
        print("  ✓ Comprehensive statistics available")
        print("\nFor production use:")
        print("  1. Apply migrations: python migrate_db.py migrate")
        print("  2. Import: from src.database.schema_optimized import Database")
        print("  3. Use as shown in examples above")
        print("\nSee DATABASE_OPTIMIZATION_GUIDE.md for complete documentation.")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
