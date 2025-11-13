"""
Optimized Database Schema with Performance Enhancements

This is the optimized version of the database layer with:
- Connection pooling
- Query caching
- Performance monitoring
- Pagination support
- Optimized queries (no N+1 problems)
- Keyword normalization support
"""
import sqlite3
import json
import time  # SECURITY FIX: Missing import for retry logic with exponential backoff
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# P1-8 FIX: Helper function to check if a database error is retryable
def _is_retryable_db_error(error: Exception) -> bool:
    """
    Check if a database error is transient and should be retried.

    Retryable errors include:
    - database is locked
    - disk I/O error
    - database disk image is malformed (sometimes transient)
    - attempt to write a readonly database

    Args:
        error: The exception to check

    Returns:
        True if the error should be retried, False otherwise
    """
    if not isinstance(error, sqlite3.OperationalError):
        return False

    error_msg = str(error).lower()
    retryable_patterns = [
        "database is locked",
        "disk i/o error",
        "database disk image is malformed",
        "attempt to write a readonly database"
    ]

    return any(pattern in error_msg for pattern in retryable_patterns)

from .pool import SingletonPool
from .cache import DatabaseCache, cached_query, invalidate_on_write
from .performance import QueryPerformanceMonitor, monitor_query_performance


class OptimizedDatabase:
    """
    Optimized database class with connection pooling, caching, and performance monitoring

    Features:
    - Connection pooling for resource efficiency
    - LRU caching for frequently accessed data
    - Performance monitoring for slow query detection
    - Optimized queries with proper JOINs (no N+1 problems)
    - Pagination support for large datasets
    - Keyword normalization support
    """

    def __init__(
        self,
        db_path: str = "resume_generator.db",
        pool_size: int = 5,
        cache_size: int = 1000,
        cache_ttl: int = 300
    ):
        """
        Initialize optimized database

        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections in pool
            cache_size: Maximum number of cached queries
            cache_ttl: Cache TTL in seconds
        """
        self.db_path = db_path

        # Initialize connection pool
        self.pool = SingletonPool.get_pool(
            db_path=db_path,
            pool_size=pool_size,
            max_overflow=10,
            timeout=30.0
        )

        # Initialize cache
        self.cache = DatabaseCache(max_size=cache_size, default_ttl=cache_ttl)

        # Initialize performance monitor
        self.monitor = QueryPerformanceMonitor(slow_query_threshold_ms=100.0)

        # Initialize database schema
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()

            # Job descriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    job_title TEXT,
                    job_description TEXT NOT NULL,
                    job_url TEXT,
                    keywords TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_name, job_description)
                )
            """)

            # Generated resumes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_description_id INTEGER NOT NULL,
                    resume_content TEXT NOT NULL,
                    ats_score INTEGER,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id),
                    UNIQUE(job_description_id)
                )
            """)

            # Company research cache (from Perplexity)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_research (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT UNIQUE NOT NULL,
                    research_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Generated cover letters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_cover_letters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_description_id INTEGER NOT NULL,
                    resume_id INTEGER,
                    cover_letter_content TEXT NOT NULL,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id),
                    FOREIGN KEY (resume_id) REFERENCES generated_resumes(id),
                    UNIQUE(job_description_id)
                )
            """)

            conn.commit()

    # ============================================================================
    # JOB DESCRIPTIONS - OPTIMIZED
    # ============================================================================

    @monitor_query_performance()
    def insert_job_description(
        self,
        company_name: str,
        job_description: str,
        job_title: Optional[str] = None,
        job_url: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> int:
        """
        Insert or get existing job description

        Args:
            company_name: Company name
            job_description: Job description text
            job_title: Job title
            job_url: Job posting URL
            keywords: List of keywords

        Returns:
            Job ID
        """
        # Invalidate cache on write
        if self.cache:
            self.cache.invalidate('job')

        # Convert keywords list to JSON string for storage
        keywords_str = json.dumps(keywords) if keywords else None

        # Retry logic with exponential backoff for database lock issues
        max_retries = 5
        retry_delay = 0.1  # Start with 100ms

        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.cursor()

                    try:
                        # Use BEGIN IMMEDIATE for write transactions to acquire lock immediately
                        cursor.execute("BEGIN IMMEDIATE")
                        cursor.execute("""
                            INSERT INTO job_descriptions (company_name, job_title, job_description, job_url, keywords)
                            VALUES (?, ?, ?, ?, ?)
                        """, (company_name, job_title, job_description, job_url, keywords_str))
                        job_id = cursor.lastrowid

                        # Insert keywords into normalized table if it exists
                        if keywords:
                            self._insert_keywords(cursor, job_id, keywords)

                        conn.commit()

                    except sqlite3.IntegrityError:
                        # Job description already exists
                        conn.rollback()
                        cursor.execute("""
                            SELECT id FROM job_descriptions
                            WHERE company_name = ? AND job_description = ?
                        """, (company_name, job_description))
                        job_id = cursor.fetchone()[0]

                    return job_id

            except sqlite3.OperationalError as e:
                # P1-8 FIX: Broadened retry logic to catch more transient errors
                if _is_retryable_db_error(e) and attempt < max_retries - 1:
                    # Wait with exponential backoff before retrying
                    print(f"Retryable database error ({str(e)[:50]}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Double the delay for next attempt
                    continue
                else:
                    # Max retries exceeded or non-retryable error
                    raise

    def _insert_keywords(self, cursor, job_id: int, keywords: List[str]) -> None:
        """
        Insert keywords into normalized keywords table

        Args:
            cursor: Database cursor
            job_id: Job description ID
            keywords: List of keywords
        """
        # Check if keywords table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='keywords'
        """)

        if not cursor.fetchone():
            return  # Keywords table doesn't exist yet

        # Insert each keyword
        for keyword in keywords:
            if keyword.strip():
                try:
                    cursor.execute("""
                        INSERT INTO keywords (job_description_id, keyword)
                        VALUES (?, ?)
                        ON CONFLICT(job_description_id, keyword)
                        DO UPDATE SET frequency = frequency + 1
                    """, (job_id, keyword.strip()))
                except sqlite3.Error:
                    pass  # Ignore conflicts

    @monitor_query_performance()
    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """
        Get job description by ID

        Args:
            job_id: Job ID

        Returns:
            Job dictionary or None
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, company_name, job_title, job_description, job_url, keywords, created_at
                FROM job_descriptions
                WHERE id = ?
            """, (job_id,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    @monitor_query_performance()
    def get_all_jobs(self, limit: int = 100) -> List[Dict]:
        """
        Get all job descriptions (optimized with limit)

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of job dictionaries
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, company_name, job_title, job_url, created_at
                FROM job_descriptions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    @monitor_query_performance()
    def get_jobs_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        company_filter: Optional[str] = None
    ) -> Dict:
        """
        Get paginated job descriptions

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            company_filter: Optional company name filter

        Returns:
            Dictionary with jobs, pagination info, and total count
        """
        offset = (page - 1) * page_size

        with self.pool.get_connection() as conn:
            cursor = conn.cursor()

            # Build query with optional filter
            query = """
                SELECT id, company_name, job_title, job_url, created_at
                FROM job_descriptions
            """
            count_query = "SELECT COUNT(*) as count FROM job_descriptions"
            params = []

            if company_filter:
                query += " WHERE company_name LIKE ?"
                count_query += " WHERE company_name LIKE ?"
                params.append(f"%{company_filter}%")

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            # Get jobs
            cursor.execute(query, params)
            jobs = [dict(row) for row in cursor.fetchall()]

            # Get total count
            count_params = [f"%{company_filter}%"] if company_filter else []
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['count']

            return {
                'jobs': jobs,
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': (total + page_size - 1) // page_size
            }

    # ============================================================================
    # GENERATED RESUMES - OPTIMIZED (NO N+1 QUERIES)
    # ============================================================================

    @monitor_query_performance()
    def check_resume_exists(self, job_description_id: int) -> Optional[Dict]:
        """
        Check if resume already generated for this job

        Args:
            job_description_id: Job ID

        Returns:
            Resume info dictionary or None
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, file_path, created_at
                FROM generated_resumes
                WHERE job_description_id = ?
            """, (job_description_id,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    @monitor_query_performance()
    def insert_generated_resume(
        self,
        job_description_id: int,
        resume_content: str,
        file_path: str,
        ats_score: Optional[int] = None
    ) -> int:
        """
        Insert generated resume

        Args:
            job_description_id: Job ID
            resume_content: Resume content
            file_path: Path to resume file
            ats_score: ATS score

        Returns:
            Resume ID
        """
        # Invalidate cache
        if self.cache:
            self.cache.invalidate('resume')

        # Retry logic with exponential backoff for database lock issues
        max_retries = 5
        retry_delay = 0.1  # Start with 100ms

        for attempt in range(max_retries):
            try:
                with self.pool.get_connection() as conn:
                    cursor = conn.cursor()

                    try:
                        # Use BEGIN IMMEDIATE for write transactions to acquire lock immediately
                        cursor.execute("BEGIN IMMEDIATE")
                        cursor.execute("""
                            INSERT INTO generated_resumes (job_description_id, resume_content, file_path, ats_score)
                            VALUES (?, ?, ?, ?)
                        """, (job_description_id, resume_content, file_path, ats_score))
                        resume_id = cursor.lastrowid
                        conn.commit()
                    except sqlite3.IntegrityError:
                        # Resume already exists, update it
                        conn.rollback()
                        cursor.execute("BEGIN IMMEDIATE")
                        cursor.execute("""
                            UPDATE generated_resumes
                            SET resume_content = ?, file_path = ?, ats_score = ?
                            WHERE job_description_id = ?
                        """, (resume_content, file_path, ats_score, job_description_id))
                        cursor.execute("""
                            SELECT id FROM generated_resumes WHERE job_description_id = ?
                        """, (job_description_id,))
                        resume_id = cursor.fetchone()[0]
                        conn.commit()

                    return resume_id

            except sqlite3.OperationalError as e:
                # P1-8 FIX: Broadened retry logic to catch more transient errors
                if _is_retryable_db_error(e) and attempt < max_retries - 1:
                    # Wait with exponential backoff before retrying
                    print(f"Retryable database error ({str(e)[:50]}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Double the delay for next attempt
                    continue
                else:
                    # Max retries exceeded or non-retryable error
                    raise

    @monitor_query_performance()
    def get_all_resumes(self, limit: int = 100) -> List[Dict]:
        """
        Get all generated resumes with job info (OPTIMIZED - single query with JOIN)

        This eliminates the N+1 query problem by using a JOIN

        Args:
            limit: Maximum number of resumes to return

        Returns:
            List of resume dictionaries with job info
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    r.id,
                    r.resume_content,
                    r.ats_score,
                    r.file_path,
                    r.created_at,
                    j.id as job_id,
                    j.company_name,
                    j.job_title,
                    j.job_description
                FROM generated_resumes r
                INNER JOIN job_descriptions j ON r.job_description_id = j.id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    @monitor_query_performance()
    def get_resumes_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        min_ats_score: Optional[int] = None
    ) -> Dict:
        """
        Get paginated resumes with job information

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            min_ats_score: Optional minimum ATS score filter

        Returns:
            Dictionary with resumes, pagination info, and total count
        """
        offset = (page - 1) * page_size

        with self.pool.get_connection() as conn:
            cursor = conn.cursor()

            # Build query with optional filter
            query = """
                SELECT
                    r.id,
                    r.ats_score,
                    r.file_path,
                    r.created_at,
                    j.company_name,
                    j.job_title
                FROM generated_resumes r
                INNER JOIN job_descriptions j ON r.job_description_id = j.id
            """
            count_query = """
                SELECT COUNT(*) as count FROM generated_resumes r
            """
            params = []

            if min_ats_score is not None:
                where_clause = " WHERE r.ats_score >= ?"
                query += where_clause
                count_query += where_clause
                params.append(min_ats_score)

            query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            # Get resumes
            cursor.execute(query, params)
            resumes = [dict(row) for row in cursor.fetchall()]

            # Get total count
            count_params = [min_ats_score] if min_ats_score is not None else []
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['count']

            return {
                'resumes': resumes,
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': (total + page_size - 1) // page_size
            }

    # ============================================================================
    # COMPANY RESEARCH - CACHED
    # ============================================================================

    @monitor_query_performance()
    def get_company_research(self, company_name: str) -> Optional[str]:
        """
        Get cached company research

        Args:
            company_name: Company name

        Returns:
            Research data or None
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT research_data FROM company_research
                WHERE company_name = ?
            """, (company_name,))

            row = cursor.fetchone()
            return row['research_data'] if row else None

    @monitor_query_performance()
    def save_company_research(self, company_name: str, research_data: str) -> None:
        """
        Save company research to cache

        Args:
            company_name: Company name
            research_data: Research data to cache
        """
        # Invalidate cache
        if self.cache:
            self.cache.invalidate('company_research')

        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO company_research (company_name, research_data)
                VALUES (?, ?)
            """, (company_name, research_data))
            conn.commit()

    # ============================================================================
    # COVER LETTERS - OPTIMIZED
    # ============================================================================

    @monitor_query_performance()
    def check_cover_letter_exists(self, job_description_id: int) -> Optional[Dict]:
        """
        Check if cover letter already generated for this job

        Args:
            job_description_id: Job ID

        Returns:
            Cover letter info dictionary or None
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, file_path, created_at
                FROM generated_cover_letters
                WHERE job_description_id = ?
            """, (job_description_id,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    @monitor_query_performance()
    def insert_generated_cover_letter(
        self,
        job_description_id: int,
        cover_letter_content: str,
        file_path: str,
        resume_id: Optional[int] = None
    ) -> int:
        """
        Insert generated cover letter

        Args:
            job_description_id: Job ID
            cover_letter_content: Cover letter content
            file_path: Path to cover letter file
            resume_id: Optional resume ID

        Returns:
            Cover letter ID
        """
        # Invalidate cache
        if self.cache:
            self.cache.invalidate('cover_letter')

        with self.pool.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO generated_cover_letters (job_description_id, resume_id, cover_letter_content, file_path)
                    VALUES (?, ?, ?, ?)
                """, (job_description_id, resume_id, cover_letter_content, file_path))
                conn.commit()
                cover_letter_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                # Cover letter already exists, update it
                cursor.execute("""
                    UPDATE generated_cover_letters
                    SET cover_letter_content = ?, file_path = ?, resume_id = ?
                    WHERE job_description_id = ?
                """, (cover_letter_content, file_path, resume_id, job_description_id))
                conn.commit()
                cursor.execute("""
                    SELECT id FROM generated_cover_letters WHERE job_description_id = ?
                """, (job_description_id,))
                cover_letter_id = cursor.fetchone()[0]

            return cover_letter_id

    # ============================================================================
    # ANALYTICS & STATISTICS
    # ============================================================================

    def get_statistics(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dictionary with database statistics
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Count tables
            cursor.execute("SELECT COUNT(*) as count FROM job_descriptions")
            stats['total_jobs'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM generated_resumes")
            stats['total_resumes'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM generated_cover_letters")
            stats['total_cover_letters'] = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM company_research")
            stats['cached_companies'] = cursor.fetchone()['count']

            # Average ATS score
            cursor.execute("SELECT AVG(ats_score) as avg_score FROM generated_resumes WHERE ats_score IS NOT NULL")
            avg_score = cursor.fetchone()['avg_score']
            stats['average_ats_score'] = round(avg_score, 2) if avg_score else None

            # Get cache stats
            stats['cache'] = self.cache.get_stats()

            # Get pool stats
            stats['pool'] = self.pool.get_stats()

            # Get performance stats
            stats['performance'] = self.monitor.get_stats()

            return stats

    def print_statistics(self) -> None:
        """Print formatted database statistics"""
        stats = self.get_statistics()

        print("\n" + "=" * 80)
        print("DATABASE STATISTICS")
        print("=" * 80)
        print(f"Total jobs:            {stats['total_jobs']:,}")
        print(f"Total resumes:         {stats['total_resumes']:,}")
        print(f"Total cover letters:   {stats['total_cover_letters']:,}")
        print(f"Cached companies:      {stats['cached_companies']:,}")
        print(f"Average ATS score:     {stats['average_ats_score']}")
        print("=" * 80 + "\n")

        # Print cache stats
        self.cache.print_stats()

        # Print pool stats
        self.pool.print_stats()

        # Print performance stats
        self.monitor.print_stats()


# Backward compatibility: alias to original name
Database = OptimizedDatabase
