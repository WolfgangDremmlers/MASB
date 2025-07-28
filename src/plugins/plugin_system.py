"""Plugin system for MASB custom evaluators."""

import importlib
import inspect
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, asdict
import asyncio
from enum import Enum

from src.models.data_models import TestPrompt, ModelResponse, EvaluationScore, Category
from src.evaluators.base_evaluator import BaseEvaluator
from src.utils.logger import logger


class PluginStatus(Enum):
    """Plugin status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class PluginInfo:
    """Plugin information."""
    name: str
    version: str
    author: str
    description: str
    category: str
    dependencies: List[str]
    config_schema: Dict[str, Any]
    entry_point: str
    status: PluginStatus = PluginStatus.INACTIVE
    error_message: Optional[str] = None


@dataclass
class PluginConfig:
    """Plugin configuration."""
    enabled: bool = True
    config: Dict[str, Any] = None
    priority: int = 0  # Higher priority loads first
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class PluginInterface(ABC):
    """Interface that all plugins must implement."""
    
    @abstractmethod
    def get_plugin_info(self) -> PluginInfo:
        """Return plugin information."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class EvaluatorPlugin(PluginInterface):
    """Base class for evaluator plugins."""
    
    @abstractmethod
    def create_evaluator(self, config: Dict[str, Any]) -> BaseEvaluator:
        """Create and return an evaluator instance."""
        pass
    
    @abstractmethod
    def get_supported_categories(self) -> List[Category]:
        """Return list of categories this evaluator supports."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration. Override if needed."""
        return True
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for configuration validation."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class PluginManager:
    """Manages plugin loading, activation, and lifecycle."""
    
    def __init__(self, plugins_dir: Path = None):
        """Initialize plugin manager.
        
        Args:
            plugins_dir: Directory containing plugins
        """
        from src.config import settings
        self.plugins_dir = plugins_dir or settings.plugins_dir
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs: Dict[str, PluginConfig] = {}
        self.evaluator_plugins: Dict[str, EvaluatorPlugin] = {}
        self.active_evaluators: Dict[Category, List[BaseEvaluator]] = {}
        
        # Create plugins directory if it doesn't exist
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Load plugin configurations
        self._load_plugin_configs()
    
    def _load_plugin_configs(self):
        """Load plugin configurations from file."""
        config_file = self.plugins_dir / "plugins_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                
                for name, config_data in configs.items():
                    self.plugin_configs[name] = PluginConfig(**config_data)
                    
            except Exception as e:
                logger.error(f"Failed to load plugin configs: {e}")
    
    def _save_plugin_configs(self):
        """Save plugin configurations to file."""
        config_file = self.plugins_dir / "plugins_config.json"
        
        try:
            configs = {}
            for name, config in self.plugin_configs.items():
                configs[name] = asdict(config)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save plugin configs: {e}")
    
    def discover_plugins(self) -> List[Path]:
        """Discover available plugins in the plugins directory.
        
        Returns:
            List of plugin file paths
        """
        plugin_files = []
        
        # Look for Python files
        for py_file in self.plugins_dir.rglob("*.py"):
            if py_file.name.startswith("plugin_") or py_file.parent.name == "plugins":
                plugin_files.append(py_file)
        
        # Look for plugin directories with __init__.py
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                plugin_files.append(plugin_dir / "__init__.py")
        
        return plugin_files
    
    def load_plugin(self, plugin_path: Path) -> bool:
        """Load a single plugin.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            True if loaded successfully
        """
        try:
            # Create module name from path
            module_name = f"plugins.{plugin_path.stem}"
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load plugin spec from {plugin_path}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes in the module
            plugin_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, PluginInterface) and 
                    obj != PluginInterface and 
                    obj != EvaluatorPlugin):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                logger.warning(f"No plugin classes found in {plugin_path}")
                return False
            
            # Instantiate and register plugins
            for plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class()
                    plugin_info = plugin_instance.get_plugin_info()
                    
                    # Get or create plugin config
                    if plugin_info.name not in self.plugin_configs:
                        self.plugin_configs[plugin_info.name] = PluginConfig()
                    
                    config = self.plugin_configs[plugin_info.name]
                    
                    if config.enabled:
                        # Initialize plugin
                        if plugin_instance.initialize(config.config):
                            self.plugins[plugin_info.name] = plugin_instance
                            
                            # Register evaluator plugins separately
                            if isinstance(plugin_instance, EvaluatorPlugin):
                                self.evaluator_plugins[plugin_info.name] = plugin_instance
                                self._register_evaluator_plugin(plugin_instance)
                            
                            logger.info(f"Loaded plugin: {plugin_info.name} v{plugin_info.version}")
                            return True
                        else:
                            logger.error(f"Failed to initialize plugin: {plugin_info.name}")
                    else:
                        logger.info(f"Plugin disabled: {plugin_info.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to instantiate plugin {plugin_class.__name__}: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_path}: {e}")
            return False
    
    def _register_evaluator_plugin(self, plugin: EvaluatorPlugin):
        """Register an evaluator plugin."""
        try:
            supported_categories = plugin.get_supported_categories()
            config = self.plugin_configs[plugin.get_plugin_info().name]
            
            # Create evaluator instance
            evaluator = plugin.create_evaluator(config.config)
            
            # Register for each supported category
            for category in supported_categories:
                if category not in self.active_evaluators:
                    self.active_evaluators[category] = []
                
                self.active_evaluators[category].append(evaluator)
                logger.info(f"Registered evaluator for category {category.value}")
                
        except Exception as e:
            logger.error(f"Failed to register evaluator plugin: {e}")
    
    def load_all_plugins(self) -> int:
        """Load all discovered plugins.
        
        Returns:
            Number of plugins loaded successfully
        """
        plugin_files = self.discover_plugins()
        loaded_count = 0
        
        # Sort by priority if configs exist
        def get_priority(path):
            plugin_name = path.stem
            if plugin_name in self.plugin_configs:
                return self.plugin_configs[plugin_name].priority
            return 0
        
        plugin_files.sort(key=get_priority, reverse=True)
        
        for plugin_file in plugin_files:
            if self.load_plugin(plugin_file):
                loaded_count += 1
        
        # Save any new configurations
        self._save_plugin_configs()
        
        logger.info(f"Loaded {loaded_count} plugins out of {len(plugin_files)} discovered")
        return loaded_count
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if unloaded successfully
        """
        if plugin_name not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            plugin.cleanup()
            
            # Remove from active plugins
            del self.plugins[plugin_name]
            
            # Remove evaluator if it's an evaluator plugin
            if plugin_name in self.evaluator_plugins:
                self._unregister_evaluator_plugin(plugin_name)
                del self.evaluator_plugins[plugin_name]
            
            logger.info(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def _unregister_evaluator_plugin(self, plugin_name: str):
        """Unregister an evaluator plugin."""
        # Remove evaluators created by this plugin
        plugin = self.evaluator_plugins[plugin_name]
        supported_categories = plugin.get_supported_categories()
        
        for category in supported_categories:
            if category in self.active_evaluators:
                # Remove evaluators from this plugin (basic implementation)
                # In a more sophisticated system, you'd track which evaluator came from which plugin
                self.active_evaluators[category] = []
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin information or None if not found
        """
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].get_plugin_info()
        return None
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all loaded plugins.
        
        Returns:
            List of plugin information
        """
        return [plugin.get_plugin_info() for plugin in self.plugins.values()]
    
    def get_evaluators_for_category(self, category: Category) -> List[BaseEvaluator]:
        """Get all evaluators for a specific category.
        
        Args:
            category: Evaluation category
            
        Returns:
            List of evaluators
        """
        return self.active_evaluators.get(category, [])
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin.
        
        Args:
            plugin_name: Name of plugin to enable
            
        Returns:
            True if enabled successfully
        """
        if plugin_name in self.plugin_configs:
            self.plugin_configs[plugin_name].enabled = True
            self._save_plugin_configs()
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin.
        
        Args:
            plugin_name: Name of plugin to disable
            
        Returns:
            True if disabled successfully
        """
        if plugin_name in self.plugin_configs:
            self.plugin_configs[plugin_name].enabled = False
            self._save_plugin_configs()
            
            # Unload if currently loaded
            if plugin_name in self.plugins:
                self.unload_plugin(plugin_name)
            
            return True
        return False
    
    def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Update plugin configuration.
        
        Args:
            plugin_name: Name of plugin
            config: New configuration
            
        Returns:
            True if updated successfully
        """
        if plugin_name not in self.plugin_configs:
            return False
        
        # Validate config if plugin is loaded
        if plugin_name in self.evaluator_plugins:
            plugin = self.evaluator_plugins[plugin_name]
            if not plugin.validate_config(config):
                return False
        
        self.plugin_configs[plugin_name].config = config
        self._save_plugin_configs()
        
        # Reload plugin if it's currently loaded
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)
            # Would need to reload from original path - simplified for now
        
        return True
    
    def create_plugin_template(self, plugin_name: str, plugin_type: str = "evaluator") -> Path:
        """Create a plugin template file.
        
        Args:
            plugin_name: Name for the new plugin
            plugin_type: Type of plugin to create
            
        Returns:
            Path to created template file
        """
        template_content = self._get_plugin_template(plugin_name, plugin_type)
        plugin_file = self.plugins_dir / f"plugin_{plugin_name}.py"
        
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        logger.info(f"Created plugin template: {plugin_file}")
        return plugin_file
    
    def _get_plugin_template(self, plugin_name: str, plugin_type: str) -> str:
        """Get plugin template content."""
        if plugin_type == "evaluator":
            return f'''"""Custom evaluator plugin: {plugin_name}"""

import asyncio
from typing import List, Dict, Any

from src.evaluators.base_evaluator import BaseEvaluator
from src.models.data_models import TestPrompt, ModelResponse, EvaluationScore, Category
from src.plugins.plugin_system import EvaluatorPlugin, PluginInfo


class Custom{plugin_name.title()}Evaluator(BaseEvaluator):
    """Custom evaluator implementation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize evaluator."""
        super().__init__()
        self.config = config or {{}}
        
        # Initialize your custom logic here
        # Example: self.threshold = config.get("threshold", 0.5)
    
    async def evaluate(self, prompt: TestPrompt, response: ModelResponse) -> EvaluationScore:
        """Evaluate a prompt-response pair.
        
        Args:
            prompt: Test prompt
            response: Model response
            
        Returns:
            Evaluation score
        """
        # Implement your custom evaluation logic here
        # This is just a template - replace with actual logic
        
        score = 0.5  # Replace with your scoring logic
        reasoning = "Custom evaluation reasoning"
        confidence = 1.0
        
        return EvaluationScore(
            category=Category.HALLUCINATION,  # Replace with appropriate category
            score=score,
            reasoning=reasoning,
            confidence=confidence,
            details={{"custom_metric": score}}
        )


class {plugin_name.title()}Plugin(EvaluatorPlugin):
    """Plugin class for {plugin_name} evaluator."""
    
    def get_plugin_info(self) -> PluginInfo:
        """Return plugin information."""
        return PluginInfo(
            name="{plugin_name}",
            version="1.0.0",
            author="Your Name",
            description="Custom evaluator plugin for {plugin_name}",
            category="evaluator",
            dependencies=[],
            config_schema={{
                "type": "object",
                "properties": {{
                    "threshold": {{
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.5,
                        "description": "Evaluation threshold"
                    }}
                }},
                "required": []
            }},
            entry_point="Custom{plugin_name.title()}Evaluator"
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin."""
        try:
            # Perform any initialization logic here
            return True
        except Exception as e:
            print(f"Failed to initialize plugin: {{e}}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        # Perform cleanup here
        pass
    
    def create_evaluator(self, config: Dict[str, Any]) -> BaseEvaluator:
        """Create evaluator instance."""
        return Custom{plugin_name.title()}Evaluator(config)
    
    def get_supported_categories(self) -> List[Category]:
        """Return supported categories."""
        return [Category.HALLUCINATION]  # Replace with actual supported categories
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        # Add custom validation logic here
        return True
'''
        
        return ""


# Global plugin manager instance
plugin_manager = PluginManager()