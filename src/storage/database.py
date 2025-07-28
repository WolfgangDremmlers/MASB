"""Database models and operations for MASB evaluation results."""

import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import asdict
import threading

from sqlalchemy import (
    create_engine, Column, String, DateTime, Float, Integer, 
    Text, Boolean, ForeignKey, Index, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
from pydantic import BaseModel

from src.models.data_models import (
    EvaluationResult, BatchEvaluationResult, TestPrompt, 
    ModelResponse, EvaluationScore, Language, Category, Severity
)
from src.utils.logger import logger

Base = declarative_base()


class DatabaseConfig(BaseModel):
    """Database configuration."""
    database_url: str = "sqlite:///masb_results.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    echo: bool = False


class EvaluationBatch(Base):
    """Database model for evaluation batches."""
    __tablename__ = "evaluation_batches"
    
    id = Column(String, primary_key=True)
    model_name = Column(String, nullable=False, index=True)
    language = Column(String, nullable=False, index=True)  # Language enum value
    category = Column(String, nullable=True, index=True)  # Category enum value
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    total_prompts = Column(Integer, nullable=False)
    completed_prompts = Column(Integer, nullable=False)
    failed_prompts = Column(Integer, nullable=False)
    status = Column(String, nullable=False, index=True)  # 'running', 'completed', 'failed'
    
    # Summary statistics as JSON
    summary = Column(JSON, nullable=True)
    
    # Configuration and metadata
    config = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    # Relationships
    results = relationship("EvaluationResultDB", back_populates="batch", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_batch_model_lang', 'model_name', 'language'),
        Index('idx_batch_status_time', 'status', 'start_time'),
        Index('idx_batch_model_time', 'model_name', 'start_time'),
    )


class EvaluationResultDB(Base):
    """Database model for individual evaluation results."""
    __tablename__ = "evaluation_results"
    
    id = Column(String, primary_key=True)
    batch_id = Column(String, ForeignKey('evaluation_batches.id'), nullable=False, index=True)
    prompt_id = Column(String, nullable=False, index=True)
    
    # Prompt information
    prompt_text = Column(Text, nullable=False)
    prompt_language = Column(String, nullable=False)
    prompt_category = Column(String, nullable=False, index=True)
    expected_behavior = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    
    # Model response
    response_text = Column(Text, nullable=False)
    response_model = Column(String, nullable=False)
    response_timestamp = Column(DateTime, nullable=False)
    response_metadata = Column(JSON, nullable=True)
    
    # Evaluation scores as JSON
    scores = Column(JSON, nullable=False)
    
    # Processing metadata
    evaluation_timestamp = Column(DateTime, nullable=False, index=True)
    processing_time = Column(Float, nullable=True)
    
    # Relationships
    batch = relationship("EvaluationBatch", back_populates="results")
    
    # Indexes
    __table_args__ = (
        Index('idx_result_category_time', 'prompt_category', 'evaluation_timestamp'),
        Index('idx_result_batch_category', 'batch_id', 'prompt_category'),
    )


class DatabaseManager:
    """Manages database operations for MASB evaluation results."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize database manager.
        
        Args:
            config: Database configuration
        """
        self.config = config or DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        self._lock = threading.Lock()
        self._initialized = False
        
    def initialize(self):
        """Initialize database connection and create tables."""
        with self._lock:
            if self._initialized:
                return
                
            try:
                # Create engine
                connect_args = {}
                if self.config.database_url.startswith('sqlite'):
                    connect_args = {
                        'check_same_thread': False,
                        'poolclass': StaticPool
                    }
                
                self.engine = create_engine(
                    self.config.database_url,
                    connect_args=connect_args,
                    echo=self.config.echo,
                    pool_pre_ping=self.config.pool_pre_ping
                )
                
                # Create session factory
                self.SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
                
                # Create tables
                Base.metadata.create_all(bind=self.engine)
                
                self._initialized = True
                logger.info(f"Database initialized: {self.config.database_url}")
                
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
    
    def get_session(self) -> Session:
        """Get database session."""
        if not self._initialized:
            self.initialize()
        return self.SessionLocal()
    
    def save_batch_result(self, batch_result: BatchEvaluationResult) -> bool:
        """Save a complete batch evaluation result.
        
        Args:
            batch_result: Batch evaluation result to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with self.get_session() as session:
                # Check if batch already exists
                existing_batch = session.query(EvaluationBatch).filter(
                    EvaluationBatch.id == batch_result.batch_id
                ).first()
                
                if existing_batch:
                    # Update existing batch
                    self._update_batch(session, existing_batch, batch_result)
                else:
                    # Create new batch
                    batch_db = self._create_batch_db(batch_result)
                    session.add(batch_db)
                
                # Save individual results
                for result in batch_result.results:
                    existing_result = session.query(EvaluationResultDB).filter(
                        EvaluationResultDB.id == result.id
                    ).first()
                    
                    if not existing_result:
                        result_db = self._create_result_db(result, batch_result.batch_id)
                        session.add(result_db)
                
                session.commit()
                logger.info(f"Saved batch result: {batch_result.batch_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save batch result {batch_result.batch_id}: {e}")
            return False
    
    def get_batch_result(self, batch_id: str) -> Optional[BatchEvaluationResult]:
        """Retrieve a batch evaluation result.
        
        Args:
            batch_id: ID of the batch to retrieve
            
        Returns:
            Batch evaluation result or None if not found
        """
        try:
            with self.get_session() as session:
                batch_db = session.query(EvaluationBatch).filter(
                    EvaluationBatch.id == batch_id
                ).first()
                
                if not batch_db:
                    return None
                
                return self._convert_batch_from_db(batch_db)
                
        except Exception as e:
            logger.error(f"Failed to get batch result {batch_id}: {e}")
            return None
    
    def list_batch_results(self,
                          model_name: Optional[str] = None,
                          language: Optional[str] = None,
                          category: Optional[str] = None,
                          status: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[BatchEvaluationResult]:
        """List batch evaluation results with filtering.
        
        Args:
            model_name: Filter by model name
            language: Filter by language
            category: Filter by category
            status: Filter by status
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of batch evaluation results
        """
        try:
            with self.get_session() as session:
                query = session.query(EvaluationBatch)
                
                # Apply filters
                if model_name:
                    query = query.filter(EvaluationBatch.model_name == model_name)
                if language:
                    query = query.filter(EvaluationBatch.language == language)
                if category:
                    query = query.filter(EvaluationBatch.category == category)
                if status:
                    query = query.filter(EvaluationBatch.status == status)
                if start_date:
                    query = query.filter(EvaluationBatch.start_time >= start_date)
                if end_date:
                    query = query.filter(EvaluationBatch.start_time <= end_date)
                
                # Order by start time (most recent first)
                query = query.order_by(EvaluationBatch.start_time.desc())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                batches = query.all()
                return [self._convert_batch_from_db(batch) for batch in batches]
                
        except Exception as e:
            logger.error(f"Failed to list batch results: {e}")
            return []
    
    def get_evaluation_statistics(self,
                                model_name: Optional[str] = None,
                                language: Optional[str] = None,
                                days: int = 30) -> Dict[str, Any]:
        """Get evaluation statistics.
        
        Args:
            model_name: Filter by model name
            language: Filter by language
            days: Number of days to include in statistics
            
        Returns:
            Dictionary containing statistics
        """
        try:
            with self.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Base query
                query = session.query(EvaluationBatch).filter(
                    EvaluationBatch.start_time >= cutoff_date
                )
                
                if model_name:
                    query = query.filter(EvaluationBatch.model_name == model_name)
                if language:
                    query = query.filter(EvaluationBatch.language == language)
                
                batches = query.all()
                
                # Calculate statistics
                total_batches = len(batches)
                total_prompts = sum(b.total_prompts for b in batches)
                completed_prompts = sum(b.completed_prompts for b in batches)
                
                # Status breakdown
                status_counts = {}
                for batch in batches:
                    status_counts[batch.status] = status_counts.get(batch.status, 0) + 1
                
                # Model breakdown
                model_counts = {}
                for batch in batches:
                    model_counts[batch.model_name] = model_counts.get(batch.model_name, 0) + 1
                
                # Language breakdown
                language_counts = {}
                for batch in batches:
                    language_counts[batch.language] = language_counts.get(batch.language, 0) + 1
                
                # Average scores by category
                category_scores = {}
                for batch in batches:
                    if batch.summary:
                        for category, stats in batch.summary.items():
                            if category not in category_scores:
                                category_scores[category] = []
                            category_scores[category].append(stats.get('mean', 0))
                
                # Calculate averages
                category_averages = {}
                for category, scores in category_scores.items():
                    if scores:
                        category_averages[category] = {
                            'mean': sum(scores) / len(scores),
                            'count': len(scores)
                        }
                
                return {
                    'period_days': days,
                    'total_batches': total_batches,
                    'total_prompts': total_prompts,
                    'completed_prompts': completed_prompts,
                    'completion_rate': completed_prompts / total_prompts if total_prompts > 0 else 0,
                    'status_breakdown': status_counts,
                    'model_breakdown': model_counts,
                    'language_breakdown': language_counts,
                    'category_averages': category_averages,
                    'query_timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get evaluation statistics: {e}")
            return {}
    
    def delete_batch_result(self, batch_id: str) -> bool:
        """Delete a batch evaluation result.
        
        Args:
            batch_id: ID of the batch to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            with self.get_session() as session:
                batch = session.query(EvaluationBatch).filter(
                    EvaluationBatch.id == batch_id
                ).first()
                
                if batch:
                    session.delete(batch)
                    session.commit()
                    logger.info(f"Deleted batch result: {batch_id}")
                    return True
                else:
                    logger.warning(f"Batch not found for deletion: {batch_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete batch result {batch_id}: {e}")
            return False
    
    def cleanup_old_results(self, days_to_keep: int = 90) -> int:
        """Clean up old evaluation results.
        
        Args:
            days_to_keep: Number of days to keep results
            
        Returns:
            Number of batches deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with self.get_session() as session:
                old_batches = session.query(EvaluationBatch).filter(
                    EvaluationBatch.start_time < cutoff_date
                ).all()
                
                count = len(old_batches)
                
                for batch in old_batches:
                    session.delete(batch)
                
                session.commit()
                logger.info(f"Cleaned up {count} old batch results (older than {days_to_keep} days)")
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old results: {e}")
            return 0
    
    def _create_batch_db(self, batch_result: BatchEvaluationResult) -> EvaluationBatch:
        """Create database model from batch result."""
        return EvaluationBatch(
            id=batch_result.batch_id,
            model_name=batch_result.model_name,
            language=batch_result.language.value,
            category=batch_result.category.value if batch_result.category else None,
            start_time=batch_result.start_time,
            end_time=batch_result.end_time,
            duration=batch_result.duration,
            total_prompts=batch_result.total_prompts,
            completed_prompts=batch_result.completed_prompts,
            failed_prompts=batch_result.failed_prompts,
            status=batch_result.status,
            summary=batch_result.summary,
            config=batch_result.config,
            metadata_json=batch_result.metadata
        )
    
    def _create_result_db(self, result: EvaluationResult, batch_id: str) -> EvaluationResultDB:
        """Create database model from evaluation result."""
        return EvaluationResultDB(
            id=result.id,
            batch_id=batch_id,
            prompt_id=result.prompt.id,
            prompt_text=result.prompt.text,
            prompt_language=result.prompt.language.value,
            prompt_category=result.prompt.category.value,
            expected_behavior=result.prompt.expected_behavior,
            severity=result.prompt.severity.value,
            response_text=result.response.response_text,
            response_model=result.response.model_name,
            response_timestamp=result.response.timestamp,
            response_metadata=result.response.metadata,
            scores=[asdict(score) for score in result.scores],
            evaluation_timestamp=result.evaluation_timestamp,
            processing_time=result.processing_time
        )
    
    def _update_batch(self, session: Session, batch_db: EvaluationBatch, batch_result: BatchEvaluationResult):
        """Update existing batch with new data."""
        batch_db.end_time = batch_result.end_time
        batch_db.duration = batch_result.duration
        batch_db.completed_prompts = batch_result.completed_prompts
        batch_db.failed_prompts = batch_result.failed_prompts
        batch_db.status = batch_result.status
        batch_db.summary = batch_result.summary
        batch_db.metadata_json = batch_result.metadata
    
    def _convert_batch_from_db(self, batch_db: EvaluationBatch) -> BatchEvaluationResult:
        """Convert database model to batch result."""
        # Convert individual results
        results = []
        for result_db in batch_db.results:
            results.append(self._convert_result_from_db(result_db))
        
        return BatchEvaluationResult(
            batch_id=batch_db.id,
            model_name=batch_db.model_name,
            language=Language(batch_db.language),
            category=Category(batch_db.category) if batch_db.category else None,
            start_time=batch_db.start_time,
            end_time=batch_db.end_time,
            duration=batch_db.duration or 0,
            total_prompts=batch_db.total_prompts,
            completed_prompts=batch_db.completed_prompts,
            failed_prompts=batch_db.failed_prompts,
            status=batch_db.status,
            results=results,
            summary=batch_db.summary or {},
            config=batch_db.config or {},
            metadata=batch_db.metadata_json or {}
        )
    
    def _convert_result_from_db(self, result_db: EvaluationResultDB) -> EvaluationResult:
        """Convert database model to evaluation result."""
        # Reconstruct prompt
        prompt = TestPrompt(
            id=result_db.prompt_id,
            text=result_db.prompt_text,
            language=Language(result_db.prompt_language),
            category=Category(result_db.prompt_category),
            expected_behavior=result_db.expected_behavior,
            severity=Severity(result_db.severity)
        )
        
        # Reconstruct response
        response = ModelResponse(
            response_text=result_db.response_text,
            model_name=result_db.response_model,
            timestamp=result_db.response_timestamp,
            metadata=result_db.response_metadata or {}
        )
        
        # Reconstruct scores
        scores = []
        for score_data in result_db.scores:
            scores.append(EvaluationScore(
                category=Category(score_data['category']),
                score=score_data['score'],
                reasoning=score_data.get('reasoning', ''),
                confidence=score_data.get('confidence', 1.0),
                details=score_data.get('details', {})
            ))
        
        return EvaluationResult(
            id=result_db.id,
            prompt=prompt,
            response=response,
            scores=scores,
            evaluation_timestamp=result_db.evaluation_timestamp,
            processing_time=result_db.processing_time or 0
        )


# Global database manager instance
db_manager = DatabaseManager()