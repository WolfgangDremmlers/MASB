"""Dataset manager for handling multilingual test prompts."""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional, Union
import pandas as pd
from src.models.data_models import TestPrompt, Language, Category, Severity
from src.config import settings
from src.utils.logger import logger


class DatasetManager:
    """Manager for loading and managing test datasets."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize dataset manager.
        
        Args:
            data_dir: Directory containing datasets
        """
        self.data_dir = data_dir or settings.data_dir / "prompts"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[TestPrompt]] = {}
        
    def load_dataset(self, 
                    language: Union[Language, str],
                    category: Optional[Union[Category, str]] = None,
                    force_reload: bool = False) -> List[TestPrompt]:
        """Load dataset for a specific language and optional category.
        
        Args:
            language: Language code or Language enum
            category: Optional category filter
            force_reload: Force reload from disk
            
        Returns:
            List of test prompts
        """
        if isinstance(language, str):
            language = Language(language)
        if isinstance(category, str):
            category = Category(category)
            
        cache_key = f"{language.value}_{category.value if category else 'all'}"
        
        # Check cache
        if not force_reload and cache_key in self._cache:
            logger.info(f"Loading dataset from cache: {cache_key}")
            return self._cache[cache_key]
        
        # Load from files
        prompts = []
        
        # Try different file formats
        for file_format in ['.json', '.jsonl', '.csv']:
            file_path = self.data_dir / f"{language.value}{file_format}"
            if file_path.exists():
                logger.info(f"Loading dataset from: {file_path}")
                
                if file_format == '.json':
                    prompts.extend(self._load_json(file_path))
                elif file_format == '.jsonl':
                    prompts.extend(self._load_jsonl(file_path))
                elif file_format == '.csv':
                    prompts.extend(self._load_csv(file_path))
                    
        # Filter by category if specified
        if category:
            prompts = [p for p in prompts if p.category == category]
            
        # Cache results
        self._cache[cache_key] = prompts
        
        logger.info(f"Loaded {len(prompts)} prompts for {language.value}"
                   f"{f' in category {category.value}' if category else ''}")
        
        return prompts
    
    def _load_json(self, file_path: Path) -> List[TestPrompt]:
        """Load prompts from JSON file."""
        prompts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, list):
                for item in data:
                    try:
                        prompt = TestPrompt(**item)
                        prompts.append(prompt)
                    except Exception as e:
                        logger.warning(f"Failed to parse prompt: {e}")
            else:
                logger.warning(f"Expected list in JSON file, got {type(data)}")
                
        except Exception as e:
            logger.error(f"Failed to load JSON file {file_path}: {e}")
            
        return prompts
    
    def _load_jsonl(self, file_path: Path) -> List[TestPrompt]:
        """Load prompts from JSONL file."""
        prompts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        prompt = TestPrompt(**data)
                        prompts.append(prompt)
                    except Exception as e:
                        logger.warning(f"Failed to parse line {line_num}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to load JSONL file {file_path}: {e}")
            
        return prompts
    
    def _load_csv(self, file_path: Path) -> List[TestPrompt]:
        """Load prompts from CSV file."""
        prompts = []
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Required columns
            required_columns = ['id', 'text', 'language', 'category', 'expected_behavior']
            
            # Check for required columns
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return prompts
            
            # Convert dataframe to prompts
            for _, row in df.iterrows():
                try:
                    # Parse metadata and tags if they exist
                    metadata = {}
                    if 'metadata' in row and pd.notna(row['metadata']):
                        try:
                            metadata = json.loads(row['metadata'])
                        except:
                            pass
                    
                    tags = []
                    if 'tags' in row and pd.notna(row['tags']):
                        try:
                            tags = json.loads(row['tags']) if row['tags'].startswith('[') else row['tags'].split(',')
                        except:
                            tags = str(row['tags']).split(',')
                    
                    prompt = TestPrompt(
                        id=str(row['id']),
                        text=str(row['text']),
                        language=Language(row['language']),
                        category=Category(row['category']),
                        expected_behavior=str(row['expected_behavior']),
                        severity=Severity(row.get('severity', 'medium')),
                        metadata=metadata,
                        tags=[tag.strip() for tag in tags if tag.strip()]
                    )
                    prompts.append(prompt)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse CSV row: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load CSV file {file_path}: {e}")
            
        return prompts
    
    def save_dataset(self, prompts: List[TestPrompt], 
                    language: Union[Language, str],
                    format: str = 'json') -> Path:
        """Save dataset to file.
        
        Args:
            prompts: List of test prompts
            language: Language code
            format: Output format (json, jsonl, csv)
            
        Returns:
            Path to saved file
        """
        if isinstance(language, str):
            language = Language(language)
            
        file_path = self.data_dir / f"{language.value}.{format}"
        
        try:
            if format == 'json':
                self._save_json(prompts, file_path)
            elif format == 'jsonl':
                self._save_jsonl(prompts, file_path)
            elif format == 'csv':
                self._save_csv(prompts, file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            logger.info(f"Saved {len(prompts)} prompts to {file_path}")
            
            # Clear cache for this language
            cache_keys_to_clear = [k for k in self._cache.keys() if k.startswith(language.value)]
            for key in cache_keys_to_clear:
                del self._cache[key]
                
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save dataset: {e}")
            raise
    
    def _save_json(self, prompts: List[TestPrompt], file_path: Path):
        """Save prompts to JSON file."""
        data = [prompt.model_dump() for prompt in prompts]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_jsonl(self, prompts: List[TestPrompt], file_path: Path):
        """Save prompts to JSONL file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for prompt in prompts:
                f.write(json.dumps(prompt.model_dump(), ensure_ascii=False) + '\n')
    
    def _save_csv(self, prompts: List[TestPrompt], file_path: Path):
        """Save prompts to CSV file."""
        rows = []
        for prompt in prompts:
            row = {
                'id': prompt.id,
                'text': prompt.text,
                'language': prompt.language.value,
                'category': prompt.category.value,
                'expected_behavior': prompt.expected_behavior,
                'severity': prompt.severity.value,
                'metadata': json.dumps(prompt.metadata, ensure_ascii=False),
                'tags': json.dumps(prompt.tags, ensure_ascii=False)
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    def get_statistics(self, language: Optional[Union[Language, str]] = None) -> Dict:
        """Get dataset statistics.
        
        Args:
            language: Optional language filter
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_prompts': 0,
            'by_language': {},
            'by_category': {},
            'by_severity': {}
        }
        
        # Get all prompts
        all_prompts = []
        if language:
            if isinstance(language, str):
                language = Language(language)
            all_prompts = self.load_dataset(language)
        else:
            for lang in Language:
                all_prompts.extend(self.load_dataset(lang))
        
        stats['total_prompts'] = len(all_prompts)
        
        # Count by language
        for prompt in all_prompts:
            lang = prompt.language.value
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1
            
            cat = prompt.category.value
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            
            sev = prompt.severity.value
            stats['by_severity'][sev] = stats['by_severity'].get(sev, 0) + 1
        
        return stats
    
    def validate_dataset(self, prompts: List[TestPrompt]) -> List[str]:
        """Validate dataset for common issues.
        
        Args:
            prompts: List of prompts to validate
            
        Returns:
            List of validation errors/warnings
        """
        issues = []
        
        # Check for duplicate IDs
        ids = [p.id for p in prompts]
        duplicates = [id for id in ids if ids.count(id) > 1]
        if duplicates:
            issues.append(f"Duplicate IDs found: {set(duplicates)}")
        
        # Check for empty fields
        for i, prompt in enumerate(prompts):
            if not prompt.text.strip():
                issues.append(f"Prompt {i} (ID: {prompt.id}) has empty text")
            if not prompt.expected_behavior.strip():
                issues.append(f"Prompt {i} (ID: {prompt.id}) has empty expected_behavior")
        
        # Check category distribution
        category_counts = {}
        for prompt in prompts:
            category_counts[prompt.category] = category_counts.get(prompt.category, 0) + 1
        
        # Warn if any category has very few examples
        for category, count in category_counts.items():
            if count < 10:
                issues.append(f"Category {category.value} has only {count} examples")
        
        return issues