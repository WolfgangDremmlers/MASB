"""Main evaluation engine for MASB."""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union
import json

from src.models.data_models import (
    TestPrompt, ModelResponse, EvaluationResult, 
    BatchEvaluationResult, Language, Category, ModelConfig
)
from src.models.provider_factory import ProviderFactory
from src.evaluators.evaluator_factory import EvaluatorFactory
from src.utils.dataset_manager import DatasetManager
from src.utils.logger import logger
from src.utils.cache_manager import CacheManager
from src.utils.error_handling import MASBError, ProviderError, handle_errors
from src.storage.database import db_manager
from src.config import settings, SAFETY_THRESHOLDS
from src.plugins.plugin_system import plugin_manager
from src.monitoring.performance_monitor import performance_tracker
from tqdm.asyncio import tqdm_asyncio


class EvaluationEngine:
    """Main engine for running evaluations."""
    
    def __init__(self, 
                 model_name: str,
                 model_config: Optional[ModelConfig] = None,
                 dataset_manager: Optional[DatasetManager] = None,
                 use_database: bool = True,
                 load_plugins: bool = True):
        """Initialize evaluation engine.
        
        Args:
            model_name: Name of the model to evaluate
            model_config: Optional model configuration
            dataset_manager: Optional dataset manager instance
            use_database: Whether to save results to database
            load_plugins: Whether to load plugin evaluators
        """
        self.model_name = model_name
        self.model_config = model_config
        self.provider = ProviderFactory.create_provider(model_name, model_config)
        self.dataset_manager = dataset_manager or DatasetManager()
        self.evaluators = EvaluatorFactory.create_all_evaluators()
        self.use_database = use_database
        self.cache_manager = CacheManager() if settings.cache_enabled else None
        
        # Load plugin evaluators
        if load_plugins:
            self._load_plugin_evaluators()
        
        # Initialize database if needed
        if self.use_database:
            try:
                db_manager.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                self.use_database = False
        
    def _load_plugin_evaluators(self):
        """Load plugin evaluators and integrate them with the evaluation system."""
        try:
            # Load all plugins
            loaded_count = plugin_manager.load_all_plugins()
            logger.info(f"Loaded {loaded_count} plugins")
            
            # Integrate plugin evaluators with the main evaluator system
            for category in Category:
                plugin_evaluators = plugin_manager.get_evaluators_for_category(category)
                if plugin_evaluators:
                    logger.info(f"Found {len(plugin_evaluators)} plugin evaluators for {category.value}")
                    
                    # If we don't have a built-in evaluator for this category, use the first plugin
                    if category not in self.evaluators and plugin_evaluators:
                        self.evaluators[category] = plugin_evaluators[0]
                        logger.info(f"Using plugin evaluator for {category.value}: {type(plugin_evaluators[0]).__name__}")
            
        except Exception as e:
            logger.error(f"Failed to load plugin evaluators: {e}")
    
    def get_available_plugins(self) -> List[Dict[str, any]]:
        """Get information about available plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        plugin_infos = plugin_manager.list_plugins()
        return [
            {
                'name': info.name,
                'version': info.version,
                'author': info.author,
                'description': info.description,
                'category': info.category,
                'status': info.status.value,
                'supported_categories': [cat.value for cat in plugin_manager.evaluator_plugins[info.name].get_supported_categories()]
                if info.name in plugin_manager.evaluator_plugins else []
            }
            for info in plugin_infos
        ]
        
    async def evaluate_prompt(self, prompt: TestPrompt) -> EvaluationResult:
        """Evaluate a single prompt.
        
        Args:
            prompt: Test prompt to evaluate
            
        Returns:
            Evaluation result
        """
        # Start performance tracking
        operation_id = f"eval_{prompt.id}_{datetime.utcnow().timestamp()}"
        perf_metrics = performance_tracker.start_operation(
            operation_id=operation_id,
            operation_type="single_evaluation",
            prompt_id=prompt.id,
            category=prompt.category.value,
            language=prompt.language.value
        )
        
        try:
            # Check cache first
            cache_key = f"{self.model_name}:{prompt.id}"
            if self.cache_manager:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    logger.debug(f"Using cached result for prompt {prompt.id}")
                    performance_tracker.update_operation(operation_id, cache_hits=1)
                    return cached_result
                else:
                    performance_tracker.update_operation(operation_id, cache_misses=1)
            
            # Generate response
            start_time = datetime.utcnow()
            response = await self.provider.generate_response(prompt.id, prompt.text)
            
            # Update performance metrics
            performance_tracker.update_operation(
                operation_id,
                requests_made=1,
                prompts_processed=1,
                tokens_processed=len(response.text.split()) if response.text else 0
            )
            
            # Get evaluators for this category (both built-in and plugins)
            scores = []
            
            # Use built-in evaluator if available
            builtin_evaluator = self.evaluators.get(prompt.category)
            if builtin_evaluator:
                try:
                    score = await builtin_evaluator.evaluate(prompt, response)
                    scores.append(score)
                except Exception as e:
                    logger.error(f"Built-in evaluator failed for {prompt.category}: {e}")
                    performance_tracker.update_operation(operation_id, errors_count=1)
            
            # Use plugin evaluators for additional scoring
            plugin_evaluators = plugin_manager.get_evaluators_for_category(prompt.category)
            for plugin_evaluator in plugin_evaluators:
                try:
                    plugin_score = await plugin_evaluator.evaluate(prompt, response)
                    scores.append(plugin_score)
                except Exception as e:
                    logger.error(f"Plugin evaluator failed for {prompt.category}: {e}")
                    performance_tracker.update_operation(operation_id, errors_count=1)
            
            if not scores:
                logger.warning(f"No evaluators available for category: {prompt.category}")
            
            # Create result
            result = EvaluationResult(
                id=f"{prompt.id}_{response.model_name}_{datetime.utcnow().timestamp()}",
                prompt=prompt,
                response=response,
                scores=scores,
                evaluation_timestamp=datetime.utcnow(),
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            # Cache result
            if self.cache_manager:
                await self.cache_manager.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating prompt {prompt.id}: {e}")
            performance_tracker.update_operation(operation_id, errors_count=1)
            raise
        finally:
            # Finish performance tracking
            performance_tracker.finish_operation(operation_id)
    
    async def evaluate_dataset(self,
                             language: Union[Language, str],
                             category: Optional[Union[Category, str]] = None,
                             max_prompts: Optional[int] = None,
                             batch_size: Optional[int] = None) -> BatchEvaluationResult:
        """Evaluate a dataset of prompts.
        
        Args:
            language: Language to evaluate
            category: Optional category filter
            max_prompts: Maximum number of prompts to evaluate
            batch_size: Batch size for concurrent requests
            
        Returns:
            Batch evaluation result
        """
        # Start performance tracking for batch evaluation
        batch_id = str(uuid.uuid4())
        operation_id = f"batch_eval_{batch_id}"
        perf_metrics = performance_tracker.start_operation(
            operation_id=operation_id,
            operation_type="batch_evaluation",
            model_name=self.model_name,
            language=str(language),
            category=str(category) if category else None,
            max_prompts=max_prompts
        )
        
        try:
            # Load dataset
            prompts = self.dataset_manager.load_dataset(language, category)
            
            if max_prompts:
                prompts = prompts[:max_prompts]
            
            if not prompts:
                logger.warning(f"No prompts found for {language} {category or 'all categories'}")
                return self._create_empty_batch_result(language)
            
            logger.info(f"Evaluating {len(prompts)} prompts for {language}")
            
            # Initialize batch result
            start_time = datetime.utcnow()
            
            # Set batch size
            if batch_size is None:
                batch_size = settings.batch_size
            
            # Update performance tracking
            performance_tracker.update_operation(
                operation_id,
                prompts_processed=0,  # Will be updated as we process
                requests_made=0
            )
            
            # Process in batches
            results = []
            failed_count = 0
            
            # Create progress bar
            pbar = tqdm_asyncio(total=len(prompts), desc="Evaluating prompts")
            
            for i in range(0, len(prompts), batch_size):
                batch = prompts[i:i + batch_size]
                
                # Evaluate batch concurrently
                batch_tasks = [self.evaluate_prompt(prompt) for prompt in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results and update metrics
                batch_success_count = 0
                batch_error_count = 0
                batch_tokens = 0
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Evaluation failed: {result}")
                        failed_count += 1
                        batch_error_count += 1
                    else:
                        results.append(result)
                        batch_success_count += 1
                        # Count tokens in response
                        if result.response and result.response.text:
                            batch_tokens += len(result.response.text.split())
                    
                    pbar.update(1)
                
                # Update performance metrics for this batch
                performance_tracker.update_operation(
                    operation_id,
                    prompts_processed=len(results),
                    requests_made=performance_tracker.active_operations[operation_id].requests_made + len(batch),
                    tokens_processed=performance_tracker.active_operations[operation_id].tokens_processed + batch_tokens,
                    errors_count=performance_tracker.active_operations[operation_id].errors_count + batch_error_count
                )
            
            pbar.close()
            
            # Create batch result
            batch_result = BatchEvaluationResult(
                batch_id=batch_id,
                model_name=self.model_name,
                language=Language(language) if isinstance(language, str) else language,
                category=Category(category) if isinstance(category, str) and category else None,
                total_prompts=len(prompts),
                completed_prompts=len(results),
                failed_prompts=failed_count,
                results=results,
                start_time=start_time,
                end_time=datetime.utcnow(),
                duration=(datetime.utcnow() - start_time).total_seconds(),
                status='completed' if failed_count == 0 else 'completed_with_errors',
                config={'batch_size': batch_size, 'max_prompts': max_prompts},
                metadata={'engine_version': '1.0', 'use_database': self.use_database}
            )
            
            # Calculate summary statistics
            batch_result.calculate_summary()
            
            # Save results to database and file
            await self._save_batch_result(batch_result)
            
            return batch_result
            
        except Exception as e:
            logger.error(f"Error in batch evaluation: {e}")
            performance_tracker.update_operation(operation_id, errors_count=1)
            raise
        finally:
            # Finish performance tracking
            performance_tracker.finish_operation(operation_id)
    
    async def evaluate_multiple_languages(self,
                                        languages: List[Union[Language, str]],
                                        category: Optional[Union[Category, str]] = None,
                                        max_prompts_per_language: Optional[int] = None
                                        ) -> Dict[str, BatchEvaluationResult]:
        """Evaluate multiple languages.
        
        Args:
            languages: List of languages to evaluate
            category: Optional category filter
            max_prompts_per_language: Max prompts per language
            
        Returns:
            Dictionary mapping language to batch results
        """
        results = {}
        
        for language in languages:
            logger.info(f"Starting evaluation for {language}")
            result = await self.evaluate_dataset(
                language, 
                category, 
                max_prompts_per_language
            )
            results[str(language)] = result
        
        return results
    
    def _create_empty_batch_result(self, language: Union[Language, str]) -> BatchEvaluationResult:
        """Create an empty batch result."""
        return BatchEvaluationResult(
            batch_id=str(uuid.uuid4()),
            model_name=self.model_name,
            language=Language(language) if isinstance(language, str) else language,
            category=None,
            total_prompts=0,
            completed_prompts=0,
            failed_prompts=0,
            results=[],
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration=0.0,
            status='completed',
            config={},
            metadata={}
        )
    
    async def _save_batch_result(self, batch_result: BatchEvaluationResult):
        """Save batch result to database and file."""
        try:
            # Save to database first
            if self.use_database:
                success = db_manager.save_batch_result(batch_result)
                if success:
                    logger.info(f"Saved batch result to database: {batch_result.batch_id}")
                else:
                    logger.error(f"Failed to save batch result to database: {batch_result.batch_id}")
            
            # Also save to file as backup
            await self._save_batch_result_to_file(batch_result)
            
        except Exception as e:
            logger.error(f"Failed to save batch result: {e}")
    
    async def _save_batch_result_to_file(self, batch_result: BatchEvaluationResult):
        """Save batch result to JSON file."""
        try:
            # Create filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.model_name}_{batch_result.language.value}_{timestamp}.json"
            filepath = settings.results_dir / filename
            
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict and save
            result_dict = batch_result.model_dump()
            
            # Convert datetime objects to strings for JSON serialization
            result_dict['start_time'] = result_dict['start_time'].isoformat()
            if result_dict['end_time']:
                result_dict['end_time'] = result_dict['end_time'].isoformat()
            
            # Convert nested datetime objects
            for result in result_dict['results']:
                if 'evaluation_timestamp' in result:
                    result['evaluation_timestamp'] = result['evaluation_timestamp'].isoformat()
                if 'response' in result and 'timestamp' in result['response']:
                    result['response']['timestamp'] = result['response']['timestamp'].isoformat()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved results to file: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save results to file: {e}")
    
    def get_batch_result_from_database(self, batch_id: str) -> Optional[BatchEvaluationResult]:
        """Retrieve batch result from database.
        
        Args:
            batch_id: ID of the batch to retrieve
            
        Returns:
            Batch evaluation result or None if not found
        """
        if not self.use_database:
            logger.warning("Database not available")
            return None
        
        return db_manager.get_batch_result(batch_id)
    
    def list_batch_results_from_database(self,
                                       model_name: Optional[str] = None,
                                       language: Optional[str] = None,
                                       category: Optional[str] = None,
                                       limit: int = 100) -> List[BatchEvaluationResult]:
        """List batch results from database.
        
        Args:
            model_name: Filter by model name
            language: Filter by language
            category: Filter by category
            limit: Maximum number of results
            
        Returns:
            List of batch evaluation results
        """
        if not self.use_database:
            logger.warning("Database not available")
            return []
        
        return db_manager.list_batch_results(
            model_name=model_name or self.model_name,
            language=language,
            category=category,
            limit=limit
        )
    
    def get_summary_report(self, batch_result: BatchEvaluationResult) -> str:
        """Generate a summary report from batch results.
        
        Args:
            batch_result: Batch evaluation result
            
        Returns:
            Summary report as string
        """
        report = []
        report.append(f"\n{'='*60}")
        report.append(f"MASB Evaluation Report")
        report.append(f"{'='*60}")
        report.append(f"Model: {batch_result.model_name}")
        report.append(f"Language: {batch_result.language.value}")
        report.append(f"Total Prompts: {batch_result.total_prompts}")
        report.append(f"Completed: {batch_result.completed_prompts}")
        report.append(f"Failed: {batch_result.failed_prompts}")
        report.append(f"Duration: {batch_result.duration:.2f} seconds")
        report.append(f"\nCategory Summary:")
        report.append(f"{'-'*60}")
        
        for category, stats in batch_result.summary.items():
            report.append(f"\n{category.value.upper()}:")
            report.append(f"  Mean Score: {stats['mean']:.3f}")
            report.append(f"  Min Score: {stats['min']:.3f}")
            report.append(f"  Max Score: {stats['max']:.3f}")
            report.append(f"  Pass Rate: {stats['pass_rate']:.1%}")
            
            # Check against threshold
            threshold = SAFETY_THRESHOLDS.get(category.value, 0.7)
            if stats['mean'] < threshold:
                report.append(f"  ⚠️  Below safety threshold ({threshold})")
        
        report.append(f"\n{'='*60}")
        
        return '\n'.join(report)