"""
Database Migration Manager
Handles versioned schema migrations with rollback support
"""
import os
import sqlite3
import json
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime


class MigrationManager:
    """
    Simple but robust database migration system

    Features:
    - Version tracking
    - Automatic migration discovery
    - Transaction-based migrations
    - Rollback support
    - Migration history tracking
    """

    def __init__(self, db_path: str, migrations_dir: str = "migrations"):
        """
        Initialize migration manager

        Args:
            db_path: Path to SQLite database file
            migrations_dir: Directory containing migration SQL files
        """
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_migrations_table()

    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def _close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def _create_migrations_table(self):
        """Create table to track applied migrations"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                status TEXT DEFAULT 'success'
            )
        """)
        self.conn.commit()

    def get_applied_migrations(self) -> List[int]:
        """
        Get list of applied migration versions

        Returns:
            List of migration version numbers
        """
        result = self.cursor.execute(
            "SELECT version FROM schema_migrations WHERE status = 'success' ORDER BY version"
        ).fetchall()
        return [row[0] for row in result]

    def get_pending_migrations(self) -> List[Tuple[int, str]]:
        """
        Get list of pending migrations from migrations directory

        Returns:
            List of tuples (version, filename)
        """
        applied = self.get_applied_migrations()
        pending = []

        # Check if migrations directory exists
        migrations_path = Path(self.migrations_dir)
        if not migrations_path.exists():
            print(f"Warning: Migrations directory '{self.migrations_dir}' does not exist")
            return pending

        # Find all .sql files
        for filepath in sorted(migrations_path.glob("*.sql")):
            filename = filepath.name
            try:
                # Extract version from filename: 001_add_indexes.sql -> 1
                version = int(filename.split('_')[0])
                if version not in applied:
                    pending.append((version, filename))
            except (ValueError, IndexError):
                print(f"Warning: Skipping invalid migration filename: {filename}")
                continue

        return sorted(pending, key=lambda x: x[0])

    def apply_migration(self, version: int, filename: str) -> bool:
        """
        Apply a single migration

        Args:
            version: Migration version number
            filename: Migration SQL filename

        Returns:
            True if successful, False otherwise
        """
        filepath = Path(self.migrations_dir) / filename

        if not filepath.exists():
            print(f"Error: Migration file not found: {filepath}")
            return False

        print(f"Applying migration {version}: {filename}")

        try:
            # Read migration SQL
            with open(filepath, 'r') as f:
                sql = f.read()

            # Time the migration
            start_time = datetime.now()

            # Execute migration in transaction
            self.cursor.executescript(sql)

            # Calculate execution time
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Record migration
            self.cursor.execute("""
                INSERT INTO schema_migrations (version, name, execution_time_ms, status)
                VALUES (?, ?, ?, 'success')
            """, (version, filename, execution_time))

            self.conn.commit()

            print(f"✓ Applied migration {version}: {filename} ({execution_time}ms)")

            # Handle post-migration data migrations
            self._handle_post_migration(version)

            return True

        except Exception as e:
            self.conn.rollback()
            print(f"✗ Failed to apply migration {version}: {e}")

            # Record failed migration
            try:
                self.cursor.execute("""
                    INSERT INTO schema_migrations (version, name, status)
                    VALUES (?, ?, 'failed')
                """, (version, filename))
                self.conn.commit()
            except (sqlite3.OperationalError, sqlite3.Error) as e:
                # Database error during failure logging - ignore
                print(f"Warning: Could not log migration failure: {e}")

            return False

    def _handle_post_migration(self, version: int):
        """
        Handle post-migration data transformations

        Args:
            version: Migration version that was just applied
        """
        if version == 2:
            # Migration 002: Migrate keywords data from TEXT to normalized table
            self._migrate_keywords_data()

    def _migrate_keywords_data(self):
        """
        Migrate keywords from TEXT field in job_descriptions to keywords table

        This handles the data migration for the keywords normalization
        """
        print("  → Migrating keywords data to normalized table...")

        try:
            # Get all job descriptions with keywords
            self.cursor.execute("""
                SELECT id, keywords
                FROM job_descriptions
                WHERE keywords IS NOT NULL AND keywords != ''
            """)

            jobs = self.cursor.fetchall()
            migrated_count = 0

            for job in jobs:
                job_id = job[0]
                keywords_str = job[1]

                if not keywords_str:
                    continue

                # Parse keywords (handle both JSON array and comma-separated)
                keywords = self._parse_keywords(keywords_str)

                # Insert each keyword
                for keyword in keywords:
                    if keyword.strip():
                        try:
                            self.cursor.execute("""
                                INSERT INTO keywords (job_description_id, keyword)
                                VALUES (?, ?)
                                ON CONFLICT(job_description_id, keyword)
                                DO UPDATE SET frequency = frequency + 1
                            """, (job_id, keyword.strip()))
                            migrated_count += 1
                        except Exception as e:
                            print(f"    Warning: Failed to insert keyword '{keyword}' for job {job_id}: {e}")

            self.conn.commit()
            print(f"  ✓ Migrated {migrated_count} keywords from {len(jobs)} jobs")

        except Exception as e:
            print(f"  ✗ Failed to migrate keywords data: {e}")
            self.conn.rollback()

    def _parse_keywords(self, keywords_str: str) -> List[str]:
        """
        Parse keywords from various formats

        Args:
            keywords_str: Keywords string (JSON array or comma-separated)

        Returns:
            List of keyword strings
        """
        if not keywords_str:
            return []

        # Try JSON array format
        if keywords_str.strip().startswith('['):
            try:
                return json.loads(keywords_str)
            except (json.JSONDecodeError, ValueError):
                # Invalid JSON - fall through to comma-separated parsing
                pass

        # Fall back to comma-separated
        return [k.strip() for k in keywords_str.split(',') if k.strip()]

    def migrate(self, target_version: Optional[int] = None) -> bool:
        """
        Apply all pending migrations up to target version

        Args:
            target_version: Stop at this version (None = apply all)

        Returns:
            True if all migrations successful, False otherwise
        """
        pending = self.get_pending_migrations()

        if not pending:
            print("No pending migrations")
            return True

        # Filter by target version if specified
        if target_version is not None:
            pending = [(v, f) for v, f in pending if v <= target_version]

        if not pending:
            print(f"No pending migrations up to version {target_version}")
            return True

        print(f"\nApplying {len(pending)} migration(s)...")
        print("=" * 60)

        success = True
        for version, filename in pending:
            if not self.apply_migration(version, filename):
                success = False
                break

        print("=" * 60)

        if success:
            print(f"✓ All migrations applied successfully\n")
        else:
            print(f"✗ Migration failed. Database may be in inconsistent state.\n")

        return success

    def rollback(self, target_version: int) -> bool:
        """
        Rollback migrations to target version

        Args:
            target_version: Version to rollback to

        Returns:
            True if successful, False otherwise
        """
        applied = self.get_applied_migrations()

        # Find migrations to rollback
        to_rollback = [v for v in applied if v > target_version]

        if not to_rollback:
            print(f"No migrations to rollback to version {target_version}")
            return True

        print(f"\nRolling back {len(to_rollback)} migration(s) to version {target_version}...")
        print("=" * 60)

        # Rollback in reverse order
        for version in sorted(to_rollback, reverse=True):
            rollback_file = f"{version:03d}_rollback.sql"
            rollback_path = Path(self.migrations_dir) / rollback_file

            if rollback_path.exists():
                print(f"Rolling back migration {version}...")
                try:
                    with open(rollback_path, 'r') as f:
                        sql = f.read()

                    self.cursor.executescript(sql)

                    # Remove from migrations table
                    self.cursor.execute(
                        "DELETE FROM schema_migrations WHERE version = ?",
                        (version,)
                    )

                    self.conn.commit()
                    print(f"✓ Rolled back migration {version}")

                except Exception as e:
                    print(f"✗ Failed to rollback migration {version}: {e}")
                    self.conn.rollback()
                    return False
            else:
                print(f"Warning: No rollback script found for migration {version}")
                print(f"  Expected: {rollback_file}")
                print(f"  Manual intervention may be required")

        print("=" * 60)
        print(f"✓ Rollback to version {target_version} complete\n")
        return True

    def status(self) -> dict:
        """
        Get migration status

        Returns:
            Dictionary with migration status information
        """
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        # Get migration history
        self.cursor.execute("""
            SELECT version, name, applied_at, execution_time_ms, status
            FROM schema_migrations
            ORDER BY version DESC
            LIMIT 10
        """)
        history = [dict(row) for row in self.cursor.fetchall()]

        return {
            'applied_count': len(applied),
            'pending_count': len(pending),
            'current_version': applied[-1] if applied else 0,
            'latest_available': pending[-1][0] if pending else (applied[-1] if applied else 0),
            'pending_migrations': pending,
            'recent_history': history
        }

    def print_status(self):
        """Print formatted migration status"""
        status = self.status()

        print("\n" + "=" * 60)
        print("DATABASE MIGRATION STATUS")
        print("=" * 60)
        print(f"Current version:     {status['current_version']}")
        print(f"Latest available:    {status['latest_available']}")
        print(f"Applied migrations:  {status['applied_count']}")
        print(f"Pending migrations:  {status['pending_count']}")

        if status['pending_migrations']:
            print("\nPending migrations:")
            for version, filename in status['pending_migrations']:
                print(f"  {version:03d}: {filename}")

        if status['recent_history']:
            print("\nRecent migration history:")
            for migration in status['recent_history']:
                status_icon = "✓" if migration['status'] == 'success' else "✗"
                exec_time = f"{migration['execution_time_ms']}ms" if migration['execution_time_ms'] else "N/A"
                print(f"  {status_icon} {migration['version']:03d}: {migration['name']} ({exec_time})")

        print("=" * 60 + "\n")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self._close()
