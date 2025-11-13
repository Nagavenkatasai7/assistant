"""
File Cleanup Utility

Handles cleanup of temporary and orphaned files to prevent disk space issues.
"""

import os
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta


class FileCleanupManager:
    """
    Manages cleanup of generated files to prevent disk space issues

    Features:
    - Remove orphaned files (not referenced in database)
    - Remove old temporary files
    - Configurable age thresholds
    - Safe deletion with logging
    """

    def __init__(self, db_connection=None, max_age_days: int = 30):
        """
        Initialize file cleanup manager

        Args:
            db_connection: Database connection to check file references
            max_age_days: Maximum age in days before files are considered old
        """
        self.db = db_connection
        self.max_age_days = max_age_days
        self.stats = {
            'files_scanned': 0,
            'files_deleted': 0,
            'space_freed_bytes': 0,
            'errors': 0
        }

    def get_files_from_database(self) -> set:
        """
        Get all file paths referenced in database

        Returns:
            Set of file paths that should be kept
        """
        if not self.db:
            return set()

        referenced_files = set()

        try:
            cursor = self.db.cursor()

            # Get file paths from generated_resumes table
            cursor.execute("SELECT file_path FROM generated_resumes WHERE file_path IS NOT NULL")
            for (file_path,) in cursor.fetchall():
                if file_path:
                    referenced_files.add(os.path.abspath(file_path))

            # Get file paths from cover_letters table if it exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='cover_letters'
            """)
            if cursor.fetchone():
                cursor.execute("SELECT pdf_path FROM cover_letters WHERE pdf_path IS NOT NULL")
                for (file_path,) in cursor.fetchall():
                    if file_path:
                        referenced_files.add(os.path.abspath(file_path))

        except Exception as e:
            print(f"Warning: Could not query database for file references: {e}")

        return referenced_files

    def cleanup_orphaned_files(
        self,
        directories: List[str],
        extensions: List[str] = ['.pdf', '.docx']
    ) -> Dict[str, int]:
        """
        Remove files not referenced in database

        Args:
            directories: List of directories to scan
            extensions: File extensions to check

        Returns:
            Dictionary with cleanup statistics
        """
        referenced_files = self.get_files_from_database()
        deleted_count = 0
        freed_bytes = 0

        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for ext in extensions:
                for file_path in dir_path.glob(f"*{ext}"):
                    self.stats['files_scanned'] += 1
                    abs_path = os.path.abspath(str(file_path))

                    # Skip if file is referenced in database
                    if abs_path in referenced_files:
                        continue

                    # Skip Profile.pdf (special case - user's profile)
                    if file_path.name == "Profile.pdf":
                        continue

                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        freed_bytes += file_size
                        print(f"Deleted orphaned file: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                        self.stats['errors'] += 1

        self.stats['files_deleted'] += deleted_count
        self.stats['space_freed_bytes'] += freed_bytes

        return {
            'deleted_count': deleted_count,
            'freed_bytes': freed_bytes,
            'freed_mb': round(freed_bytes / (1024 * 1024), 2)
        }

    def cleanup_old_files(
        self,
        directories: List[str],
        extensions: List[str] = ['.pdf', '.docx'],
        max_age_days: int = None
    ) -> Dict[str, int]:
        """
        Remove files older than specified age

        Args:
            directories: List of directories to scan
            extensions: File extensions to check
            max_age_days: Override default max age

        Returns:
            Dictionary with cleanup statistics
        """
        max_age = max_age_days or self.max_age_days
        cutoff_time = time.time() - (max_age * 24 * 60 * 60)
        referenced_files = self.get_files_from_database()

        deleted_count = 0
        freed_bytes = 0

        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for ext in extensions:
                for file_path in dir_path.glob(f"*{ext}"):
                    self.stats['files_scanned'] += 1

                    # Skip Profile.pdf
                    if file_path.name == "Profile.pdf":
                        continue

                    # Skip if still referenced in database
                    abs_path = os.path.abspath(str(file_path))
                    if abs_path in referenced_files:
                        continue

                    try:
                        file_age = file_path.stat().st_mtime
                        if file_age < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            deleted_count += 1
                            freed_bytes += file_size
                            age_days = (time.time() - file_age) / (24 * 60 * 60)
                            print(f"Deleted old file ({age_days:.0f} days): {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                        self.stats['errors'] += 1

        self.stats['files_deleted'] += deleted_count
        self.stats['space_freed_bytes'] += freed_bytes

        return {
            'deleted_count': deleted_count,
            'freed_bytes': freed_bytes,
            'freed_mb': round(freed_bytes / (1024 * 1024), 2)
        }

    def cleanup_test_files(self, base_dir: str = ".") -> Dict[str, int]:
        """
        Remove test files that may have been left behind

        Args:
            base_dir: Base directory to search

        Returns:
            Dictionary with cleanup statistics
        """
        test_patterns = [
            "test*.pdf",
            "test*.docx",
            "*_test.pdf",
            "*_test.docx",
            "sample*.pdf",
            "example*.pdf"
        ]

        base_path = Path(base_dir)
        deleted_count = 0
        freed_bytes = 0

        for pattern in test_patterns:
            for file_path in base_path.glob(pattern):
                self.stats['files_scanned'] += 1

                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    freed_bytes += file_size
                    print(f"Deleted test file: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
                    self.stats['errors'] += 1

        self.stats['files_deleted'] += deleted_count
        self.stats['space_freed_bytes'] += freed_bytes

        return {
            'deleted_count': deleted_count,
            'freed_bytes': freed_bytes,
            'freed_mb': round(freed_bytes / (1024 * 1024), 2)
        }

    def run_full_cleanup(
        self,
        directories: List[str] = ["."],
        cleanup_old: bool = True,
        cleanup_orphaned: bool = True,
        cleanup_tests: bool = True
    ) -> Dict[str, any]:
        """
        Run all cleanup operations

        Args:
            directories: Directories to clean
            cleanup_old: Remove old files
            cleanup_orphaned: Remove orphaned files
            cleanup_tests: Remove test files

        Returns:
            Combined cleanup statistics
        """
        results = {
            'old_files': {},
            'orphaned_files': {},
            'test_files': {},
            'total': {'deleted_count': 0, 'freed_mb': 0}
        }

        if cleanup_orphaned:
            results['orphaned_files'] = self.cleanup_orphaned_files(directories)
            results['total']['deleted_count'] += results['orphaned_files']['deleted_count']
            results['total']['freed_mb'] += results['orphaned_files']['freed_mb']

        if cleanup_old:
            results['old_files'] = self.cleanup_old_files(directories)
            results['total']['deleted_count'] += results['old_files']['deleted_count']
            results['total']['freed_mb'] += results['old_files']['freed_mb']

        if cleanup_tests:
            results['test_files'] = self.cleanup_test_files(directories[0] if directories else ".")
            results['total']['deleted_count'] += results['test_files']['deleted_count']
            results['total']['freed_mb'] += results['test_files']['freed_mb']

        return results

    def get_stats(self) -> Dict[str, int]:
        """Get cleanup statistics"""
        return self.stats.copy()


def main():
    """Test file cleanup"""
    import sqlite3

    # Connect to database
    conn = sqlite3.connect('resume_generator.db')

    # Create cleanup manager
    cleanup = FileCleanupManager(db_connection=conn, max_age_days=30)

    print("Running file cleanup...")
    print("=" * 60)

    # Run full cleanup
    results = cleanup.run_full_cleanup(
        directories=["."],
        cleanup_old=False,  # Don't delete old files in test
        cleanup_orphaned=True,
        cleanup_tests=True
    )

    print("\n" + "=" * 60)
    print("CLEANUP RESULTS")
    print("=" * 60)
    print(f"Orphaned files: {results['orphaned_files']['deleted_count']} deleted, "
          f"{results['orphaned_files']['freed_mb']} MB freed")
    print(f"Test files: {results['test_files']['deleted_count']} deleted, "
          f"{results['test_files']['freed_mb']} MB freed")
    print(f"\nTotal: {results['total']['deleted_count']} files, "
          f"{results['total']['freed_mb']:.2f} MB freed")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
