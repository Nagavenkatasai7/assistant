#!/usr/bin/env python3
"""
Database Migration CLI Tool

Manage database schema migrations for Ultra ATS Resume Generator

Usage:
    python migrate_db.py status              # Show migration status
    python migrate_db.py migrate             # Apply all pending migrations
    python migrate_db.py migrate --to 2      # Migrate to specific version
    python migrate_db.py rollback --to 1     # Rollback to specific version
    python migrate_db.py create "add_field"  # Create new migration template

Examples:
    # Check current migration status
    python migrate_db.py status

    # Apply all pending migrations
    python migrate_db.py migrate

    # Migrate to version 2 only
    python migrate_db.py migrate --to 2

    # Rollback to version 1
    python migrate_db.py rollback --to 1

    # Create new migration
    python migrate_db.py create "add_user_preferences"
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.database.migrations import MigrationManager


class MigrationCLI:
    """Command-line interface for database migrations"""

    def __init__(self, db_path: str = "resume_generator.db", migrations_dir: str = "migrations"):
        """
        Initialize CLI

        Args:
            db_path: Path to database file
            migrations_dir: Directory containing migrations
        """
        self.db_path = db_path
        self.migrations_dir = migrations_dir

    def status(self):
        """Show migration status"""
        with MigrationManager(self.db_path, self.migrations_dir) as manager:
            manager.print_status()

    def migrate(self, target_version: int = None):
        """
        Apply migrations

        Args:
            target_version: Target version to migrate to (None = all)
        """
        print(f"Database: {self.db_path}")
        print(f"Migrations directory: {self.migrations_dir}\n")

        with MigrationManager(self.db_path, self.migrations_dir) as manager:
            # Show current status
            status = manager.status()
            print(f"Current version: {status['current_version']}")

            if target_version:
                print(f"Target version: {target_version}")

            # Confirm
            if status['pending_count'] > 0:
                print(f"\nThis will apply {status['pending_count']} migration(s):")
                for version, filename in status['pending_migrations']:
                    if target_version is None or version <= target_version:
                        print(f"  - {version:03d}: {filename}")

                response = input("\nContinue? [y/N]: ")
                if response.lower() != 'y':
                    print("Migration cancelled")
                    return

            # Apply migrations
            success = manager.migrate(target_version)

            if success:
                print("\n✓ Migration completed successfully")

                # Show new status
                manager.print_status()
            else:
                print("\n✗ Migration failed")
                sys.exit(1)

    def rollback(self, target_version: int):
        """
        Rollback migrations

        Args:
            target_version: Version to rollback to
        """
        print(f"Database: {self.db_path}")
        print(f"Migrations directory: {self.migrations_dir}\n")

        with MigrationManager(self.db_path, self.migrations_dir) as manager:
            status = manager.status()
            current_version = status['current_version']

            if target_version >= current_version:
                print(f"Cannot rollback: target version {target_version} >= current version {current_version}")
                sys.exit(1)

            # Confirm
            applied = manager.get_applied_migrations()
            to_rollback = [v for v in applied if v > target_version]

            print(f"Current version: {current_version}")
            print(f"Target version: {target_version}")
            print(f"\nThis will rollback {len(to_rollback)} migration(s):")
            for version in sorted(to_rollback, reverse=True):
                print(f"  - {version:03d}")

            print("\n⚠️  WARNING: This operation may result in data loss!")
            response = input("Continue? [y/N]: ")
            if response.lower() != 'y':
                print("Rollback cancelled")
                return

            # Rollback
            success = manager.rollback(target_version)

            if success:
                print("\n✓ Rollback completed successfully")
            else:
                print("\n✗ Rollback failed")
                sys.exit(1)

    def create(self, description: str):
        """
        Create new migration template

        Args:
            description: Migration description (e.g., "add_user_table")
        """
        # Get next version number
        migrations_path = Path(self.migrations_dir)
        migrations_path.mkdir(exist_ok=True)

        existing_migrations = sorted(migrations_path.glob("*.sql"))
        if existing_migrations:
            last_migration = existing_migrations[-1].name
            last_version = int(last_migration.split('_')[0])
            next_version = last_version + 1
        else:
            next_version = 1

        # Clean description
        clean_desc = description.lower().replace(' ', '_')
        clean_desc = ''.join(c for c in clean_desc if c.isalnum() or c == '_')

        # Create migration files
        migration_file = migrations_path / f"{next_version:03d}_{clean_desc}.sql"
        rollback_file = migrations_path / f"{next_version:03d}_rollback.sql"

        # Migration template
        migration_template = f"""-- Migration {next_version:03d}: {description}
-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Description: {description}

-- ============================================================================
-- SCHEMA CHANGES
-- ============================================================================

-- Add your schema changes here
-- Example:
-- ALTER TABLE users ADD COLUMN email TEXT;
-- CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- DATA MIGRATIONS (if needed)
-- ============================================================================

-- Add any data transformation SQL here
-- Example:
-- UPDATE users SET email = 'unknown@example.com' WHERE email IS NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify migration success
-- SELECT COUNT(*) FROM users WHERE email IS NOT NULL;
"""

        # Rollback template
        rollback_template = f"""-- Rollback {next_version:03d}: {description}
-- This script rolls back migration {next_version:03d}

-- ============================================================================
-- ROLLBACK SCHEMA CHANGES
-- ============================================================================

-- Reverse the schema changes from migration {next_version:03d}
-- Example:
-- DROP INDEX IF EXISTS idx_users_email;
-- ALTER TABLE users DROP COLUMN email;

-- ============================================================================
-- ROLLBACK DATA CHANGES (if applicable)
-- ============================================================================

-- Reverse any data transformations
-- Note: Some data changes may not be reversible!

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify rollback success
"""

        # Write files
        with open(migration_file, 'w') as f:
            f.write(migration_template)

        with open(rollback_file, 'w') as f:
            f.write(rollback_template)

        print(f"✓ Created migration files:")
        print(f"  {migration_file}")
        print(f"  {rollback_file}")
        print(f"\nEdit these files and then run: python migrate_db.py migrate")

    def verify(self):
        """Verify database integrity"""
        print(f"Verifying database: {self.db_path}\n")

        import sqlite3

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Run integrity check
            print("Running PRAGMA integrity_check...")
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if result[0] == 'ok':
                print("✓ Database integrity check passed")
            else:
                print(f"✗ Database integrity check failed: {result[0]}")
                sys.exit(1)

            # Check foreign keys
            print("\nRunning PRAGMA foreign_key_check...")
            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()

            if not violations:
                print("✓ Foreign key constraints verified")
            else:
                print(f"✗ Found {len(violations)} foreign key violations:")
                for violation in violations:
                    print(f"  {violation}")
                sys.exit(1)

            # Show table stats
            print("\nTable statistics:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = cursor.fetchall()

            for (table_name,) in tables:
                # SECURITY FIX: Use identifier quoting to prevent SQL injection
                # Even though table names come from sqlite_master, always quote identifiers
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cursor.fetchone()[0]
                print(f"  {table_name}: {count:,} rows")

            # Show index stats
            print("\nIndex statistics:")
            cursor.execute("""
                SELECT name, tbl_name
                FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """)
            indexes = cursor.fetchall()

            current_table = None
            for idx_name, tbl_name in indexes:
                if tbl_name != current_table:
                    print(f"  {tbl_name}:")
                    current_table = tbl_name
                print(f"    - {idx_name}")

            conn.close()

            print("\n✓ Database verification completed successfully")

        except Exception as e:
            print(f"✗ Database verification failed: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Database Migration CLI for Ultra ATS Resume Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    Show migration status
  %(prog)s migrate                   Apply all pending migrations
  %(prog)s migrate --to 2            Migrate to version 2
  %(prog)s rollback --to 1           Rollback to version 1
  %(prog)s create "add_field"        Create new migration
  %(prog)s verify                    Verify database integrity
        """
    )

    parser.add_argument(
        'command',
        choices=['status', 'migrate', 'rollback', 'create', 'verify'],
        help='Command to execute'
    )

    parser.add_argument(
        'description',
        nargs='?',
        help='Migration description (for create command)'
    )

    parser.add_argument(
        '--to',
        type=int,
        help='Target version (for migrate/rollback commands)'
    )

    parser.add_argument(
        '--db',
        default='resume_generator.db',
        help='Database file path (default: resume_generator.db)'
    )

    parser.add_argument(
        '--migrations',
        default='migrations',
        help='Migrations directory (default: migrations)'
    )

    args = parser.parse_args()

    # Create CLI instance
    cli = MigrationCLI(db_path=args.db, migrations_dir=args.migrations)

    # Execute command
    try:
        if args.command == 'status':
            cli.status()

        elif args.command == 'migrate':
            cli.migrate(target_version=args.to)

        elif args.command == 'rollback':
            if not args.to:
                print("Error: --to VERSION is required for rollback")
                sys.exit(1)
            cli.rollback(target_version=args.to)

        elif args.command == 'create':
            if not args.description:
                print("Error: description is required for create command")
                sys.exit(1)
            cli.create(description=args.description)

        elif args.command == 'verify':
            cli.verify()

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
