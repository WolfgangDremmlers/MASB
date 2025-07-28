"""Database management CLI for MASB."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.storage.database import db_manager, DatabaseConfig
from src.storage.migrations import MigrationManager, DataImportExport, create_backup, restore_backup
from src.utils.logger import logger


def setup_database(args):
    """Initialize database."""
    try:
        if args.database_url:
            config = DatabaseConfig(database_url=args.database_url)
            global db_manager
            from src.storage.database import DatabaseManager
            db_manager = DatabaseManager(config)
        
        db_manager.initialize()
        print("✅ Database initialized successfully")
        
        # Run migrations if needed
        migration_manager = MigrationManager(db_manager)
        migration_manager.run_migrations()
        print("✅ Database migrations completed")
        
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)


def list_results(args):
    """List evaluation results."""
    try:
        results = db_manager.list_batch_results(
            model_name=args.model,
            language=args.language,
            category=args.category,
            limit=args.limit
        )
        
        if not results:
            print("No results found matching criteria")
            return
        
        print(f"\n📊 Found {len(results)} evaluation results:")
        print("-" * 100)
        print(f"{'Batch ID':<38} {'Model':<15} {'Language':<10} {'Category':<15} {'Status':<12} {'Date'}")
        print("-" * 100)
        
        for result in results:
            category_str = result.category.value if result.category else "All"
            date_str = result.start_time.strftime("%Y-%m-%d %H:%M")
            print(f"{result.batch_id:<38} {result.model_name:<15} {result.language.value:<10} "
                  f"{category_str:<15} {result.status:<12} {date_str}")
        
    except Exception as e:
        print(f"❌ Failed to list results: {e}")
        sys.exit(1)


def show_result(args):
    """Show detailed result."""
    try:
        result = db_manager.get_batch_result(args.batch_id)
        
        if not result:
            print(f"❌ Result not found: {args.batch_id}")
            sys.exit(1)
        
        print(f"\n📋 Evaluation Result Details")
        print("=" * 50)
        print(f"Batch ID: {result.batch_id}")
        print(f"Model: {result.model_name}")
        print(f"Language: {result.language.value}")
        print(f"Category: {result.category.value if result.category else 'All'}")
        print(f"Status: {result.status}")
        print(f"Start Time: {result.start_time}")
        print(f"End Time: {result.end_time}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Total Prompts: {result.total_prompts}")
        print(f"Completed: {result.completed_prompts}")
        print(f"Failed: {result.failed_prompts}")
        
        if result.summary:
            print(f"\n📈 Category Summary:")
            print("-" * 30)
            for category, stats in result.summary.items():
                print(f"{category.replace('_', ' ').title()}:")
                print(f"  Mean Score: {stats.get('mean', 0):.3f}")
                print(f"  Pass Rate: {stats.get('pass_rate', 0):.1%}")
        
        if args.verbose and result.results:
            print(f"\n🔍 Individual Results ({len(result.results)}):")
            print("-" * 40)
            for i, res in enumerate(result.results[:10]):  # Show first 10
                scores_str = ", ".join([f"{s.category.value}: {s.score:.3f}" for s in res.scores])
                print(f"{i+1}. {res.prompt.id}: {scores_str}")
            
            if len(result.results) > 10:
                print(f"... and {len(result.results) - 10} more results")
        
    except Exception as e:
        print(f"❌ Failed to show result: {e}")
        sys.exit(1)


def delete_result(args):
    """Delete evaluation result."""
    try:
        if not args.force:
            confirm = input(f"⚠️  Are you sure you want to delete result {args.batch_id}? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                return
        
        success = db_manager.delete_batch_result(args.batch_id)
        
        if success:
            print(f"✅ Deleted result: {args.batch_id}")
        else:
            print(f"❌ Failed to delete result (not found): {args.batch_id}")
            
    except Exception as e:
        print(f"❌ Failed to delete result: {e}")
        sys.exit(1)


def show_stats(args):
    """Show database statistics."""
    try:
        stats = db_manager.get_evaluation_statistics(
            model_name=args.model,
            language=args.language,
            days=args.days
        )
        
        if not stats:
            print("No statistics available")
            return
        
        print(f"\n📊 Database Statistics (Last {stats['period_days']} days)")
        print("=" * 50)
        print(f"Total Batches: {stats['total_batches']}")
        print(f"Total Prompts: {stats['total_prompts']}")
        print(f"Completed Prompts: {stats['completed_prompts']}")
        print(f"Completion Rate: {stats['completion_rate']:.1%}")
        
        if stats['status_breakdown']:
            print(f"\n📋 Status Breakdown:")
            for status, count in stats['status_breakdown'].items():
                print(f"  {status.title()}: {count}")
        
        if stats['model_breakdown']:
            print(f"\n🤖 Model Breakdown:")
            for model, count in stats['model_breakdown'].items():
                print(f"  {model}: {count}")
        
        if stats['language_breakdown']:
            print(f"\n🌍 Language Breakdown:")
            for language, count in stats['language_breakdown'].items():
                print(f"  {language}: {count}")
        
        if stats['category_averages']:
            print(f"\n📈 Category Performance:")
            for category, data in stats['category_averages'].items():
                print(f"  {category.replace('_', ' ').title()}: {data['mean']:.3f} (n={data['count']})")
        
    except Exception as e:
        print(f"❌ Failed to show statistics: {e}")
        sys.exit(1)


def export_data(args):
    """Export evaluation data."""
    try:
        exporter = DataImportExport(db_manager)
        output_path = Path(args.output)
        
        start_date = datetime.fromisoformat(args.start_date) if args.start_date else None
        end_date = datetime.fromisoformat(args.end_date) if args.end_date else None
        
        if args.format == 'json':
            success = exporter.export_to_json(
                output_path,
                model_name=args.model,
                language=args.language,
                start_date=start_date,
                end_date=end_date
            )
        elif args.format == 'csv':
            success = exporter.export_to_csv(
                output_path,
                model_name=args.model,
                language=args.language,
                start_date=start_date,
                end_date=end_date
            )
        else:
            print(f"❌ Unsupported format: {args.format}")
            sys.exit(1)
        
        if success:
            print(f"✅ Data exported to: {output_path}")
        else:
            print(f"❌ Failed to export data")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to export data: {e}")
        sys.exit(1)


def backup_database(args):
    """Create database backup."""
    try:
        backup_path = Path(args.output)
        success = create_backup(db_manager, backup_path)
        
        if success:
            print(f"✅ Database backed up to: {backup_path}")
        else:
            print(f"❌ Failed to create backup")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        sys.exit(1)


def restore_database(args):
    """Restore database from backup."""
    try:
        if not args.force:
            confirm = input("⚠️  This will overwrite the current database. Continue? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                return
        
        backup_path = Path(args.backup)
        success = restore_backup(db_manager, backup_path)
        
        if success:
            print(f"✅ Database restored from: {backup_path}")
        else:
            print(f"❌ Failed to restore database")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to restore database: {e}")
        sys.exit(1)


def cleanup_old(args):
    """Clean up old evaluation results."""
    try:
        if not args.force:
            confirm = input(f"⚠️  Delete results older than {args.days} days? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                return
        
        count = db_manager.cleanup_old_results(args.days)
        print(f"✅ Cleaned up {count} old results")
        
    except Exception as e:
        print(f"❌ Failed to cleanup old results: {e}")
        sys.exit(1)


def migration_status(args):
    """Show migration status."""
    try:
        migration_manager = MigrationManager(db_manager)
        history = migration_manager.get_migration_history()
        
        if not history:
            print("No migrations found")
            return
        
        print(f"\n🔄 Migration History:")
        print("-" * 60)
        print(f"{'Revision':<15} {'Current':<8} {'Message'}")
        print("-" * 60)
        
        for migration in history:
            current_mark = "✅" if migration['is_current'] else "  "
            print(f"{migration['revision']:<15} {current_mark:<8} {migration['message']}")
        
    except Exception as e:
        print(f"❌ Failed to show migration status: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MASB Database Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database
  python -m src.storage.cli setup
  
  # List recent results
  python -m src.storage.cli list --limit 10
  
  # Show specific result
  python -m src.storage.cli show <batch-id>
  
  # Export data to CSV
  python -m src.storage.cli export --format csv --output results.csv
  
  # Create backup
  python -m src.storage.cli backup --output backup.db
  
  # Show statistics
  python -m src.storage.cli stats --days 30
        """
    )
    
    parser.add_argument('--database-url', help='Database URL')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Initialize database')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List evaluation results')
    list_parser.add_argument('--model', help='Filter by model name')
    list_parser.add_argument('--language', help='Filter by language')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--limit', type=int, default=50, help='Limit results')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show detailed result')
    show_parser.add_argument('batch_id', help='Batch ID to show')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete evaluation result')
    delete_parser.add_argument('batch_id', help='Batch ID to delete')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Force deletion')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--model', help='Filter by model name')
    stats_parser.add_argument('--language', help='Filter by language')
    stats_parser.add_argument('--days', type=int, default=30, help='Days to include')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export evaluation data')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', 
                              help='Export format')
    export_parser.add_argument('--output', required=True, help='Output file path')
    export_parser.add_argument('--model', help='Filter by model name')
    export_parser.add_argument('--language', help='Filter by language')
    export_parser.add_argument('--start-date', help='Start date (ISO format)')
    export_parser.add_argument('--end-date', help='End date (ISO format)')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--output', required=True, help='Backup file path')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument('backup', help='Backup file path')
    restore_parser.add_argument('--force', '-f', action='store_true', help='Force restore')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old results')
    cleanup_parser.add_argument('--days', type=int, default=90, 
                               help='Delete results older than N days')
    cleanup_parser.add_argument('--force', '-f', action='store_true', help='Force cleanup')
    
    # Migration command
    migration_parser = subparsers.add_parser('migrations', help='Show migration status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize database manager with custom URL if provided
    if args.database_url:
        config = DatabaseConfig(database_url=args.database_url)
        global db_manager
        from src.storage.database import DatabaseManager
        db_manager = DatabaseManager(config)
    
    # Route to appropriate function
    command_map = {
        'setup': setup_database,
        'list': list_results,
        'show': show_result,
        'delete': delete_result,
        'stats': show_stats,
        'export': export_data,
        'backup': backup_database,
        'restore': restore_database,
        'cleanup': cleanup_old,
        'migrations': migration_status
    }
    
    if args.command in command_map:
        command_map[args.command](args)
    else:
        print(f"❌ Unknown command: {args.command}")
        sys.exit(1)


if __name__ == '__main__':
    main()