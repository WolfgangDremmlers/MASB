"""Caching system for MASB evaluation results."""

import hashlib
import json
import pickle
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass

from src.models.data_models import ModelResponse, EvaluationResult, TestPrompt
from src.config import settings
from src.utils.logger import logger
from src.utils.exceptions import CacheError


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    timestamp: float
    ttl: Optional[float] = None
    access_count: int = 0
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def is_valid(self) -> bool:
        """Check if cache entry is valid."""
        return not self.is_expired()


class CacheManager:
    """Manages caching for MASB evaluation results."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: int = 1000):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = cache_dir or (settings.data_dir / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.RLock()
        
        # Initialize persistent storage
        self.db_path = self.cache_dir / "cache.db"
        self._init_database()
        
        # Load cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size": 0
        }
        
        logger.info(f"Cache manager initialized with max size: {max_size_mb}MB")
    
    def _init_database(self):
        """Initialize SQLite database for persistent cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value BLOB,
                        timestamp REAL,
                        ttl REAL,
                        access_count INTEGER DEFAULT 0,
                        size_bytes INTEGER
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON cache_entries(timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ttl 
                    ON cache_entries(ttl)
                """)
                
                conn.commit()
                
        except Exception as e:
            raise CacheError(f"Failed to initialize cache database: {e}")
    
    def _generate_key(self, 
                     prompt_id: str, 
                     model_name: str, 
                     model_config: Dict[str, Any] = None) -> str:
        """Generate cache key for evaluation result.
        
        Args:
            prompt_id: Prompt identifier
            model_name: Model name
            model_config: Model configuration
            
        Returns:
            Cache key
        """
        config_str = json.dumps(model_config or {}, sort_keys=True)
        key_data = f"{prompt_id}:{model_name}:{config_str}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get_cached_response(self, 
                           prompt_id: str, 
                           model_name: str,
                           model_config: Dict[str, Any] = None) -> Optional[ModelResponse]:
        """Get cached model response.
        
        Args:
            prompt_id: Prompt identifier
            model_name: Model name
            model_config: Model configuration
            
        Returns:
            Cached response or None
        """
        key = self._generate_key(prompt_id, model_name, model_config)
        return self._get_from_cache(key, "response")
    
    def cache_response(self, 
                      prompt_id: str, 
                      model_name: str, 
                      response: ModelResponse,
                      model_config: Dict[str, Any] = None,
                      ttl: Optional[float] = None):
        """Cache model response.
        
        Args:
            prompt_id: Prompt identifier
            model_name: Model name
            response: Model response to cache
            model_config: Model configuration
            ttl: Time to live in seconds
        """
        key = self._generate_key(prompt_id, model_name, model_config)
        self._store_in_cache(key, response, "response", ttl)
    
    def get_cached_evaluation(self, 
                             prompt_id: str, 
                             model_name: str,
                             evaluator_version: str = "1.0.0",
                             model_config: Dict[str, Any] = None) -> Optional[EvaluationResult]:
        """Get cached evaluation result.
        
        Args:
            prompt_id: Prompt identifier
            model_name: Model name
            evaluator_version: Evaluator version
            model_config: Model configuration
            
        Returns:
            Cached evaluation result or None
        """
        key = f"eval:{self._generate_key(prompt_id, model_name, model_config)}:{evaluator_version}"
        return self._get_from_cache(key, "evaluation")
    
    def cache_evaluation(self, 
                        prompt_id: str, 
                        model_name: str, 
                        result: EvaluationResult,
                        evaluator_version: str = "1.0.0",
                        model_config: Dict[str, Any] = None,
                        ttl: Optional[float] = None):
        """Cache evaluation result.
        
        Args:
            prompt_id: Prompt identifier
            model_name: Model name
            result: Evaluation result to cache
            evaluator_version: Evaluator version
            model_config: Model configuration
            ttl: Time to live in seconds
        """
        key = f"eval:{self._generate_key(prompt_id, model_name, model_config)}:{evaluator_version}"
        self._store_in_cache(key, result, "evaluation", ttl)
    
    def _get_from_cache(self, key: str, cache_type: str) -> Optional[Any]:
        """Get item from cache.
        
        Args:
            key: Cache key
            cache_type: Type of cached item
            
        Returns:
            Cached item or None
        """
        with self.cache_lock:
            # Try memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if entry.is_valid():
                    entry.access_count += 1
                    self.stats["hits"] += 1
                    logger.debug(f"Cache hit (memory): {key}")
                    return entry.value
                else:
                    # Remove expired entry
                    del self.memory_cache[key]
            
            # Try persistent cache
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT value, timestamp, ttl, access_count FROM cache_entries WHERE key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        value_blob, timestamp, ttl, access_count = row
                        
                        # Check if expired
                        if ttl and time.time() - timestamp > ttl:
                            # Remove expired entry
                            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                            conn.commit()
                            self.stats["misses"] += 1
                            return None
                        
                        # Deserialize value
                        try:
                            value = pickle.loads(value_blob)
                            
                            # Update access count
                            conn.execute(
                                "UPDATE cache_entries SET access_count = access_count + 1 WHERE key = ?",
                                (key,)
                            )
                            conn.commit()
                            
                            # Add to memory cache
                            entry = CacheEntry(
                                key=key,
                                value=value,
                                timestamp=timestamp,
                                ttl=ttl,
                                access_count=access_count + 1,
                                size_bytes=len(value_blob)
                            )
                            self.memory_cache[key] = entry
                            
                            self.stats["hits"] += 1
                            logger.debug(f"Cache hit (persistent): {key}")
                            return value
                            
                        except Exception as e:
                            logger.warning(f"Failed to deserialize cached value: {e}")
                            # Remove corrupted entry
                            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                            conn.commit()
            
            except Exception as e:
                logger.error(f"Error accessing persistent cache: {e}")
            
            self.stats["misses"] += 1
            logger.debug(f"Cache miss: {key}")
            return None
    
    def _store_in_cache(self, key: str, value: Any, cache_type: str, ttl: Optional[float] = None):
        """Store item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cached item
            ttl: Time to live in seconds
        """
        with self.cache_lock:
            try:
                # Serialize value
                value_blob = pickle.dumps(value)
                size_bytes = len(value_blob)
                timestamp = time.time()
                
                # Check cache size limits
                if size_bytes > self.max_size_bytes // 10:  # Max 10% of cache for single item
                    logger.warning(f"Item too large for cache: {size_bytes} bytes")
                    return
                
                # Store in memory cache
                entry = CacheEntry(
                    key=key,
                    value=value,
                    timestamp=timestamp,
                    ttl=ttl,
                    size_bytes=size_bytes
                )
                self.memory_cache[key] = entry
                
                # Store in persistent cache
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """INSERT OR REPLACE INTO cache_entries 
                           (key, value, timestamp, ttl, access_count, size_bytes) 
                           VALUES (?, ?, ?, ?, 0, ?)""",
                        (key, value_blob, timestamp, ttl, size_bytes)
                    )
                    conn.commit()
                
                # Update statistics
                self.stats["total_size"] += size_bytes
                
                # Cleanup if needed
                if self.stats["total_size"] > self.max_size_bytes:
                    self._cleanup_cache()
                
                logger.debug(f"Cached {cache_type}: {key} ({size_bytes} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to cache item: {e}")
                raise CacheError(f"Failed to cache item: {e}")
    
    def _cleanup_cache(self):
        """Clean up cache by removing old/least used entries."""
        try:
            # Remove expired entries from memory
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self.stats["total_size"] -= self.memory_cache[key].size_bytes
                del self.memory_cache[key]
                self.stats["evictions"] += 1
            
            # Clean up persistent cache
            with sqlite3.connect(self.db_path) as conn:
                # Remove expired entries
                current_time = time.time()
                conn.execute(
                    "DELETE FROM cache_entries WHERE ttl IS NOT NULL AND ? - timestamp > ttl",
                    (current_time,)
                )
                
                # If still over limit, remove least recently used entries
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                total_size = cursor.fetchone()[0] or 0
                
                if total_size > self.max_size_bytes:
                    # Remove 20% of entries (least recently used)
                    conn.execute("""
                        DELETE FROM cache_entries WHERE key IN (
                            SELECT key FROM cache_entries 
                            ORDER BY access_count ASC, timestamp ASC 
                            LIMIT (SELECT COUNT(*) FROM cache_entries) / 5
                        )
                    """)
                    
                    # Update statistics
                    removed_count = conn.total_changes
                    self.stats["evictions"] += removed_count
                
                conn.commit()
            
            # Recalculate total size
            self._update_cache_stats()
            
            logger.info(f"Cache cleanup completed. Evicted {len(expired_keys)} expired entries")
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    def _update_cache_stats(self):
        """Update cache statistics."""
        try:
            # Memory cache size
            memory_size = sum(entry.size_bytes for entry in self.memory_cache.values())
            
            # Persistent cache size
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
                persistent_size = cursor.fetchone()[0] or 0
            
            self.stats["total_size"] = memory_size + persistent_size
            
        except Exception as e:
            logger.error(f"Failed to update cache stats: {e}")
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache entries.
        
        Args:
            cache_type: Type of cache to clear (None for all)
        """
        with self.cache_lock:
            try:
                if cache_type:
                    # Clear specific cache type
                    keys_to_remove = [
                        key for key in self.memory_cache.keys()
                        if cache_type in key
                    ]
                    
                    for key in keys_to_remove:
                        del self.memory_cache[key]
                    
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(
                            "DELETE FROM cache_entries WHERE key LIKE ?",
                            (f"%{cache_type}%",)
                        )
                        conn.commit()
                else:
                    # Clear all cache
                    self.memory_cache.clear()
                    
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("DELETE FROM cache_entries")
                        conn.commit()
                
                # Reset statistics
                self.stats = {
                    "hits": 0,
                    "misses": 0,
                    "evictions": 0,
                    "total_size": 0
                }
                
                logger.info(f"Cache cleared: {cache_type or 'all'}")
                
            except Exception as e:
                logger.error(f"Failed to clear cache: {e}")
                raise CacheError(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        self._update_cache_stats()
        
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                entry_count = cursor.fetchone()[0]
        except Exception:
            entry_count = 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "entry_count": entry_count,
            "memory_entries": len(self.memory_cache),
            "max_size_bytes": self.max_size_bytes,
            "cache_dir": str(self.cache_dir)
        }
    
    def cleanup_expired(self):
        """Clean up expired cache entries."""
        self._cleanup_cache()


class IncrementalEvaluator:
    """Handles incremental evaluation with caching."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """Initialize incremental evaluator.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager or CacheManager()
        
    def get_cached_results(self, 
                          prompts: List[TestPrompt], 
                          model_name: str,
                          model_config: Dict[str, Any] = None) -> tuple[List[TestPrompt], List[EvaluationResult]]:
        """Get cached results and remaining prompts to evaluate.
        
        Args:
            prompts: List of prompts to evaluate
            model_name: Model name
            model_config: Model configuration
            
        Returns:
            Tuple of (remaining_prompts, cached_results)
        """
        remaining_prompts = []
        cached_results = []
        
        for prompt in prompts:
            cached_result = self.cache_manager.get_cached_evaluation(
                prompt.id, model_name, model_config=model_config
            )
            
            if cached_result:
                cached_results.append(cached_result)
                logger.debug(f"Using cached result for prompt {prompt.id}")
            else:
                remaining_prompts.append(prompt)
        
        logger.info(
            f"Found {len(cached_results)} cached results, "
            f"{len(remaining_prompts)} prompts need evaluation"
        )
        
        return remaining_prompts, cached_results
    
    def cache_results(self, 
                     results: List[EvaluationResult], 
                     model_name: str,
                     model_config: Dict[str, Any] = None,
                     ttl: Optional[float] = None):
        """Cache evaluation results.
        
        Args:
            results: Evaluation results to cache
            model_name: Model name
            model_config: Model configuration
            ttl: Time to live in seconds
        """
        for result in results:
            self.cache_manager.cache_evaluation(
                result.prompt.id, 
                model_name, 
                result,
                model_config=model_config,
                ttl=ttl
            )
            
            # Also cache the response
            self.cache_manager.cache_response(
                result.prompt.id,
                model_name,
                result.response,
                model_config=model_config,
                ttl=ttl
            )
        
        logger.info(f"Cached {len(results)} evaluation results")


# Global cache manager instance
cache_manager = CacheManager()