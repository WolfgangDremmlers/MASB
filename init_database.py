#!/usr/bin/env python3
"""Database initialization script for MASB."""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.database import DatabaseManager, DatabaseConfig, db_manager
from src.storage.migrations import MigrationManager
from src.utils.logger import logger


def init_database(database_url: str = None, verbose: bool = False):
    """Initialize the MASB database.
    
    Args:
        database_url: Custom database URL
        verbose: Enable verbose logging
    """
    try:
        print("🚀 Initializing MASB Database...")
        
        # Configure database
        if database_url:
            config = DatabaseConfig(database_url=database_url, echo=verbose)
            db_manager_instance = DatabaseManager(config)
        else:
            db_manager_instance = db_manager
            if verbose:
                db_manager_instance.config.echo = True
        
        # Initialize database
        print("📊 Creating database tables...")
        db_manager_instance.initialize()
        print("✅ Database tables created successfully")
        
        # Run migrations
        print("🔄 Running database migrations...")
        migration_manager = MigrationManager(db_manager_instance)
        migration_manager.run_migrations()
        print("✅ Database migrations completed")
        
        # Verify database
        with db_manager_instance.get_session() as session:
            # Simple test query
            from src.storage.database import EvaluationBatch
            count = session.query(EvaluationBatch).count()
            print(f"📈 Database ready - {count} evaluation batches found")
        
        print("\n🎉 MASB Database initialization completed successfully!")
        print(f"📍 Database location: {db_manager_instance.config.database_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize MASB Database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize with default SQLite database
  python init_database.py
  
  # Initialize with custom database URL
  python init_database.py --database-url "sqlite:///custom_masb.db"
  
  # Initialize with PostgreSQL
  python init_database.py --database-url "postgresql://user:pass@localhost/masb"
  
  # Initialize with verbose output
  python init_database.py --verbose
        """
    )
    
    parser.add_argument(
        '--database-url',
        type=str,
        help='Database URL (default: sqlite:///masb_results.db)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    success = init_database(
        database_url=args.database_url,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()