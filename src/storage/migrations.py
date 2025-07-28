"""Database migration utilities for MASB."""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from sqlalchemy import text
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

from src.storage.database import DatabaseManager, Base
from src.utils.logger import logger


class MigrationManager:
    """Manages database migrations and schema updates."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize migration manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.migrations_dir = Path(__file__).parent / "migrations"
        
    def initialize_alembic(self):
        """Initialize Alembic configuration if not exists."""
        alembic_ini_path = self.migrations_dir / "alembic.ini"
        env_py_path = self.migrations_dir / "env.py"
        
        if not self.migrations_dir.exists():
            self.migrations_dir.mkdir(parents=True, exist_ok=True)
            
        if not alembic_ini_path.exists():
            self._create_alembic_ini(alembic_ini_path)
            
        if not env_py_path.exists():
            self._create_env_py(env_py_path)
            
        versions_dir = self.migrations_dir / "versions"
        if not versions_dir.exists():
            versions_dir.mkdir(exist_ok=True)
    
    def create_migration(self, message: str) -> Optional[str]:
        """Create a new migration.
        
        Args:
            message: Migration message
            
        Returns:
            Migration file path if successful, None otherwise
        """
        try:
            self.initialize_alembic()
            
            alembic_cfg = Config(str(self.migrations_dir / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(self.migrations_dir))
            alembic_cfg.set_main_option("sqlalchemy.url", self.db_manager.config.database_url)
            
            command.revision(alembic_cfg, message=message, autogenerate=True)
            logger.info(f"Created migration: {message}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return None
    
    def run_migrations(self) -> bool:
        """Run pending migrations.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.initialize_alembic()
            
            alembic_cfg = Config(str(self.migrations_dir / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(self.migrations_dir))
            alembic_cfg.set_main_option("sqlalchemy.url", self.db_manager.config.database_url)
            
            command.upgrade(alembic_cfg, "head")
            logger.info("Successfully ran database migrations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return False
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history.
        
        Returns:
            List of migration information
        """
        try:
            with self.db_manager.get_session() as session:
                # Check if alembic_version table exists
                result = session.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
                ))
                
                if not result.fetchone():
                    return []
                
                # Get current version
                result = session.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.scalar()
                
                # Get migration scripts
                alembic_cfg = Config(str(self.migrations_dir / "alembic.ini"))
                alembic_cfg.set_main_option("script_location", str(self.migrations_dir))
                
                script_dir = ScriptDirectory.from_config(alembic_cfg)
                
                migrations = []
                for revision in script_dir.walk_revisions():
                    migrations.append({
                        'revision': revision.revision,
                        'message': revision.doc,
                        'is_current': revision.revision == current_version,
                        'branch_labels': revision.branch_labels,
                        'depends_on': revision.depends_on
                    })
                
                return migrations
                
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def _create_alembic_ini(self, path: Path):
        """Create alembic.ini configuration file."""
        content = """# Alembic configuration for MASB

[alembic]
script_location = %(here)s
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = sqlite:///masb_results.db

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        with open(path, 'w') as f:
            f.write(content)
    
    def _create_env_py(self, path: Path):
        """Create env.py for Alembic."""
        content = '''"""Alembic environment configuration for MASB."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models here
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.storage.database import Base

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        with open(path, 'w') as f:
            f.write(content)


class DataImportExport:
    """Handles data import and export operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize data import/export manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def export_to_json(self, 
                       output_file: Path,
                       model_name: Optional[str] = None,
                       language: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> bool:
        """Export evaluation results to JSON.
        
        Args:
            output_file: Output file path
            model_name: Filter by model name
            language: Filter by language
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get batch results
            batches = self.db_manager.list_batch_results(
                model_name=model_name,
                language=language,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Export all matching results
            )
            
            # Convert to serializable format
            export_data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'filters': {
                    'model_name': model_name,
                    'language': language,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                },
                'total_batches': len(batches),
                'batches': []
            }
            
            for batch in batches:
                batch_data = {
                    'batch_id': batch.batch_id,
                    'model_name': batch.model_name,
                    'language': batch.language.value,
                    'category': batch.category.value if batch.category else None,
                    'start_time': batch.start_time.isoformat(),
                    'end_time': batch.end_time.isoformat() if batch.end_time else None,
                    'duration': batch.duration,
                    'total_prompts': batch.total_prompts,
                    'completed_prompts': batch.completed_prompts,
                    'failed_prompts': batch.failed_prompts,
                    'status': batch.status,
                    'summary': batch.summary,
                    'config': batch.config,
                    'metadata': batch.metadata,
                    'results': []
                }
                
                for result in batch.results:
                    result_data = {
                        'id': result.id,
                        'prompt': {
                            'id': result.prompt.id,
                            'text': result.prompt.text,
                            'language': result.prompt.language.value,
                            'category': result.prompt.category.value,
                            'expected_behavior': result.prompt.expected_behavior,
                            'severity': result.prompt.severity.value
                        },
                        'response': {
                            'response_text': result.response.response_text,
                            'model_name': result.response.model_name,
                            'timestamp': result.response.timestamp.isoformat(),
                            'metadata': result.response.metadata
                        },
                        'scores': [
                            {
                                'category': score.category.value,
                                'score': score.score,
                                'reasoning': score.reasoning,
                                'confidence': score.confidence,
                                'details': score.details
                            }
                            for score in result.scores
                        ],
                        'evaluation_timestamp': result.evaluation_timestamp.isoformat(),
                        'processing_time': result.processing_time
                    }
                    batch_data['results'].append(result_data)
                
                export_data['batches'].append(batch_data)
            
            # Write to file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(batches)} batches to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data to JSON: {e}")
            return False
    
    def export_to_csv(self, 
                      output_file: Path,
                      model_name: Optional[str] = None,
                      language: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> bool:
        """Export evaluation results to CSV.
        
        Args:
            output_file: Output file path
            model_name: Filter by model name
            language: Filter by language
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import pandas as pd
            
            # Get batch results
            batches = self.db_manager.list_batch_results(
                model_name=model_name,
                language=language,
                start_date=start_date,
                end_date=end_date,
                limit=10000
            )
            
            # Flatten data for CSV
            rows = []
            for batch in batches:
                for result in batch.results:
                    for score in result.scores:
                        row = {
                            'batch_id': batch.batch_id,
                            'result_id': result.id,
                            'model_name': batch.model_name,
                            'language': batch.language.value,
                            'batch_category': batch.category.value if batch.category else None,
                            'start_time': batch.start_time.isoformat(),
                            'prompt_id': result.prompt.id,
                            'prompt_text': result.prompt.text,
                            'prompt_category': result.prompt.category.value,
                            'expected_behavior': result.prompt.expected_behavior,
                            'severity': result.prompt.severity.value,
                            'response_text': result.response.response_text,
                            'evaluation_category': score.category.value,
                            'score': score.score,
                            'reasoning': score.reasoning,
                            'confidence': score.confidence,
                            'evaluation_timestamp': result.evaluation_timestamp.isoformat(),
                            'processing_time': result.processing_time
                        }
                        rows.append(row)
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(rows)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            logger.info(f"Exported {len(rows)} result rows to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data to CSV: {e}")
            return False


# Database utilities
def create_backup(db_manager: DatabaseManager, backup_path: Path) -> bool:
    """Create database backup.
    
    Args:
        db_manager: Database manager instance
        backup_path: Backup file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if db_manager.config.database_url.startswith('sqlite'):
            # For SQLite, simply copy the database file
            import shutil
            
            db_path = db_manager.config.database_url.replace('sqlite:///', '')
            if os.path.exists(db_path):
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(db_path, backup_path)
                logger.info(f"Created database backup: {backup_path}")
                return True
            else:
                logger.warning(f"Database file not found: {db_path}")
                return False
        else:
            # For other databases, use SQL dump (implementation depends on database type)
            logger.warning("Backup not implemented for non-SQLite databases")
            return False
            
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")
        return False


def restore_backup(db_manager: DatabaseManager, backup_path: Path) -> bool:
    """Restore database from backup.
    
    Args:
        db_manager: Database manager instance
        backup_path: Backup file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if db_manager.config.database_url.startswith('sqlite'):
            import shutil
            
            db_path = db_manager.config.database_url.replace('sqlite:///', '')
            if backup_path.exists():
                # Create backup of current database
                if os.path.exists(db_path):
                    shutil.copy2(db_path, f"{db_path}.backup")
                
                # Restore from backup
                shutil.copy2(backup_path, db_path)
                logger.info(f"Restored database from backup: {backup_path}")
                return True
            else:
                logger.error(f"Backup file not found: {backup_path}")
                return False
        else:
            logger.warning("Restore not implemented for non-SQLite databases")
            return False
            
    except Exception as e:
        logger.error(f"Failed to restore database backup: {e}")
        return False