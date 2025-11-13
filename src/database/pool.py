"""
Database Connection Pooling
Manages a pool of database connections for better resource utilization
"""
import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator, Optional
from queue import Queue, Empty
import time


class DatabasePool:
    """
    Connection pool for SQLite databases

    Features:
    - Connection reuse
    - Automatic connection validation
    - Connection timeout handling
    - Thread-safe operations
    - Connection lifecycle management

    Note: SQLite has limitations with concurrent writes. This pool is optimized
    for read-heavy workloads with occasional writes.
    """

    def __init__(
        self,
        db_path: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        timeout: float = 30.0,
        check_same_thread: bool = False
    ):
        """
        Initialize connection pool

        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum number of connections beyond pool_size
            timeout: Timeout in seconds when waiting for connection
            check_same_thread: SQLite check_same_thread parameter
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self.check_same_thread = check_same_thread

        # Connection pool (queue of available connections)
        self.pool: Queue = Queue(maxsize=pool_size + max_overflow)

        # Tracking
        self.overflow_count = 0
        self.lock = threading.Lock()

        # FIX: Track connection metadata separately since sqlite3.Connection doesn't support attributes
        self.connection_metadata = {}  # {id(conn): {'created_at': float, 'query_count': int}}

        # WAL checkpoint tracking
        self.operation_count = 0
        self.last_checkpoint_time = time.time()
        self.checkpoint_every_n_operations = 1000  # Checkpoint after 1000 operations

        # Statistics
        self.stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'pool_checkouts': 0,
            'pool_timeouts': 0,
            'overflow_used': 0,
            'wal_checkpoints': 0
        }

        # Track if WAL mode is available (will be set during connection creation)
        self.wal_mode_enabled = False

        # Initialize pool
        self._initialize_pool()

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection

        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=self.check_same_thread,
            timeout=self.timeout
        )

        # Set row factory for dictionary-like access
        conn.row_factory = sqlite3.Row

        # Enable foreign keys (wrap in try-except for Streamlit Cloud compatibility)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
        except Exception:
            pass  # Foreign keys not supported or restricted

        # Optimize SQLite for better performance
        # Try WAL mode, but fall back gracefully if not supported (e.g., on Streamlit Cloud)
        try:
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            self.wal_mode_enabled = True  # WAL mode successfully enabled
        except Exception:
            # WAL mode not supported in this environment (e.g., Streamlit Cloud)
            # Fall back to default DELETE mode - no action needed
            self.wal_mode_enabled = False
            pass

        # Wrap all performance PRAGMA statements for Streamlit Cloud compatibility
        try:
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance durability/performance
        except Exception:
            pass  # Not supported in restricted environment

        try:
            conn.execute("PRAGMA busy_timeout = 10000")  # 10 second timeout for locks
        except Exception:
            pass  # Not supported in restricted environment

        try:
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        except Exception:
            pass  # Not supported in restricted environment

        try:
            conn.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
        except Exception:
            pass  # Not supported in restricted environment

        # Try memory-mapped I/O, but fall back if not supported
        try:
            conn.execute("PRAGMA mmap_size = 268435456")  # 256MB memory-mapped I/O
        except Exception:
            # Memory-mapped I/O not supported - continue without it
            pass

        # FIX: Track connection metadata in separate dictionary
        self.connection_metadata[id(conn)] = {
            'created_at': time.time(),
            'query_count': 0
        }

        self.stats['connections_created'] += 1

        return conn

    def _initialize_pool(self):
        """Initialize the connection pool with initial connections"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self.pool.put(conn)

    def _cleanup_connection_metadata(self, conn: sqlite3.Connection):
        """
        FIX: Clean up connection metadata when a connection is closed

        Args:
            conn: Connection being closed
        """
        conn_id = id(conn)
        self.connection_metadata.pop(conn_id, None)

    def _validate_connection(self, conn: sqlite3.Connection) -> bool:
        """
        Validate that a connection is still usable

        Args:
            conn: Connection to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    def _should_recycle_connection(self, conn: sqlite3.Connection) -> bool:
        """
        Check if a connection should be recycled based on age or query count

        Args:
            conn: Connection to check

        Returns:
            True if connection should be recycled, False otherwise
        """
        # FIX: Look up connection metadata from dictionary
        conn_id = id(conn)
        metadata = self.connection_metadata.get(conn_id)

        if not metadata:
            # No metadata found, don't recycle
            return False

        # Recycle connections older than 1 hour
        max_age_seconds = 3600  # 1 hour
        age = time.time() - metadata['created_at']
        if age > max_age_seconds:
            return True

        # Recycle connections after 10,000 queries
        max_queries = 10000
        if metadata['query_count'] > max_queries:
            return True

        return False

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a connection from the pool (context manager)

        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")

        Yields:
            Database connection
        """
        conn = None
        is_overflow = False

        try:
            # Try to get connection from pool
            try:
                conn = self.pool.get(timeout=self.timeout)
                self.stats['pool_checkouts'] += 1

                # Check if connection should be recycled
                if self._should_recycle_connection(conn):
                    self._cleanup_connection_metadata(conn)  # FIX: Clean up metadata
                    conn.close()
                    conn = self._create_connection()
                    self.stats['connections_closed'] += 1
                # Validate connection
                elif not self._validate_connection(conn):
                    self._cleanup_connection_metadata(conn)  # FIX: Clean up metadata
                    conn.close()
                    self.stats['connections_closed'] += 1
                    conn = self._create_connection()

                # FIX: Increment query count in metadata dictionary
                conn_id = id(conn)
                if conn_id in self.connection_metadata:
                    self.connection_metadata[conn_id]['query_count'] += 1

            except Empty:
                # Pool exhausted, check if we can create overflow connection
                with self.lock:
                    if self.overflow_count < self.max_overflow:
                        self.overflow_count += 1
                        is_overflow = True
                        # DEADLOCK FIX: Create connection outside lock to prevent holding lock during slow I/O
                        # Also wrap in try-except to decrement overflow_count if creation fails
                        try:
                            conn = self._create_connection()
                            self.stats['overflow_used'] += 1
                        except Exception:
                            # Connection creation failed, decrement overflow count
                            self.overflow_count -= 1
                            is_overflow = False
                            raise
                    else:
                        self.stats['pool_timeouts'] += 1
                        raise TimeoutError(
                            f"Connection pool exhausted. "
                            f"Pool size: {self.pool_size}, "
                            f"Overflow: {self.overflow_count}/{self.max_overflow}"
                        )

            yield conn

        finally:
            # Return connection to pool or close if overflow
            if conn:
                if is_overflow:
                    self._cleanup_connection_metadata(conn)  # FIX: Clean up metadata
                    conn.close()
                    self.stats['connections_closed'] += 1
                    with self.lock:
                        self.overflow_count -= 1
                else:
                    # Return to pool
                    try:
                        self.pool.put_nowait(conn)
                    except Exception as e:
                        # Pool full (shouldn't happen), close connection
                        print(f"Warning: Failed to return connection to pool: {e}")
                        self._cleanup_connection_metadata(conn)  # FIX: Clean up metadata
                        conn.close()
                        self.stats['connections_closed'] += 1
            elif is_overflow:
                # DEADLOCK FIX: If connection was never created but overflow was incremented
                # (e.g., exception during connection creation outside the try block above)
                # ensure we decrement the counter
                with self.lock:
                    if self.overflow_count > 0:
                        self.overflow_count -= 1

    def execute(self, query: str, params: tuple = ()) -> list:
        """
        Execute a query and return results

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_many(self, query: str, params_list: list) -> None:
        """
        Execute a query with multiple parameter sets

        Args:
            query: SQL query
            params_list: List of parameter tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """
        Execute a write query (INSERT, UPDATE, DELETE)

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Last row ID (for INSERT) or number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

            # Track operations and checkpoint WAL if needed
            self.operation_count += 1
            self._maybe_checkpoint_wal()

            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

    def _maybe_checkpoint_wal(self) -> None:
        """
        Checkpoint WAL file if threshold reached to prevent unbounded growth

        Checkpoints every 1000 operations OR every hour (whichever comes first)
        """
        # Skip if WAL mode is not enabled (e.g., on Streamlit Cloud)
        if not self.wal_mode_enabled:
            return

        current_time = time.time()
        time_since_last = current_time - self.last_checkpoint_time

        # Checkpoint if: 1000 operations passed OR 1 hour passed
        should_checkpoint = (
            self.operation_count >= self.checkpoint_every_n_operations or
            time_since_last >= 3600  # 1 hour in seconds
        )

        if should_checkpoint:
            try:
                with self.get_connection() as conn:
                    # TRUNCATE mode: Checkpoint and truncate WAL file
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    conn.commit()

                self.operation_count = 0
                self.last_checkpoint_time = current_time
                self.stats['wal_checkpoints'] += 1

                print(f"WAL checkpoint completed (operations: {self.operation_count}, "
                      f"time since last: {time_since_last:.0f}s)")
            except Exception as e:
                # Don't fail the operation if checkpoint fails - just log
                print(f"Warning: WAL checkpoint failed: {e}")

    def checkpoint_wal_now(self) -> bool:
        """
        Force an immediate WAL checkpoint

        Returns:
            True if successful, False otherwise
        """
        # Skip if WAL mode is not enabled (e.g., on Streamlit Cloud)
        if not self.wal_mode_enabled:
            return True  # Return True since skipping is expected behavior

        try:
            with self.get_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.commit()

            self.operation_count = 0
            self.last_checkpoint_time = time.time()
            self.stats['wal_checkpoints'] += 1
            return True
        except Exception as e:
            print(f"Error: WAL checkpoint failed: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Get connection pool statistics

        Returns:
            Dictionary with pool statistics
        """
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'current_overflow': self.overflow_count,
            'available_connections': self.pool.qsize(),
            'connections_created': self.stats['connections_created'],
            'connections_closed': self.stats['connections_closed'],
            'active_connections': (
                self.stats['connections_created'] - self.stats['connections_closed']
            ),
            'pool_checkouts': self.stats['pool_checkouts'],
            'pool_timeouts': self.stats['pool_timeouts'],
            'overflow_used': self.stats['overflow_used'],
            'wal_checkpoints': self.stats['wal_checkpoints']
        }

    def print_stats(self) -> None:
        """Print formatted pool statistics"""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("DATABASE CONNECTION POOL STATISTICS")
        print("=" * 60)
        print(f"Pool size:             {stats['pool_size']}")
        print(f"Max overflow:          {stats['max_overflow']}")
        print(f"Available:             {stats['available_connections']}")
        print(f"Current overflow:      {stats['current_overflow']}")
        print(f"Active connections:    {stats['active_connections']}")
        print(f"Total created:         {stats['connections_created']}")
        print(f"Total closed:          {stats['connections_closed']}")
        print(f"Pool checkouts:        {stats['pool_checkouts']:,}")
        print(f"Pool timeouts:         {stats['pool_timeouts']}")
        print(f"Overflow used:         {stats['overflow_used']}")
        print("=" * 60 + "\n")

    def close_all(self) -> None:
        """Close all connections in the pool"""
        closed_count = 0

        # Close all connections in pool
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                self._cleanup_connection_metadata(conn)  # FIX: Clean up metadata
                conn.close()
                closed_count += 1
            except Empty:
                break

        self.stats['connections_closed'] += closed_count
        # FIX: Clear any remaining metadata
        self.connection_metadata.clear()
        print(f"Closed {closed_count} connections")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_all()


class SingletonPool:
    """
    Singleton pattern for database pool

    Ensures only one pool instance exists per database path
    """

    _instances: dict = {}
    _lock = threading.Lock()

    @classmethod
    def get_pool(
        cls,
        db_path: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        timeout: float = 30.0
    ) -> DatabasePool:
        """
        Get or create pool for database path

        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections in pool
            max_overflow: Maximum overflow connections
            timeout: Connection timeout in seconds

        Returns:
            DatabasePool instance
        """
        with cls._lock:
            if db_path not in cls._instances:
                cls._instances[db_path] = DatabasePool(
                    db_path=db_path,
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    timeout=timeout,
                    check_same_thread=False
                )
            return cls._instances[db_path]

    @classmethod
    def close_all_pools(cls) -> None:
        """Close all pool instances"""
        with cls._lock:
            for pool in cls._instances.values():
                pool.close_all()
            cls._instances.clear()
