"""Tests for the plugin system."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from src.plugins.plugin_system import PluginManager, PluginStatus, EvaluatorPlugin, PluginInfo
from src.models.data_models import TestPrompt, ModelResponse, EvaluationScore, Category, Language, Severity


class MockEvaluatorPlugin(EvaluatorPlugin):
    """Mock evaluator plugin for testing."""
    
    def get_plugin_info(self) -> PluginInfo:
        return PluginInfo(
            name="mock_evaluator",
            version="1.0.0",
            author="Test Author",
            description="Mock evaluator for testing",
            category="evaluator",
            dependencies=[],
            config_schema={
                "type": "object",
                "properties": {
                    "threshold": {"type": "number", "default": 0.5}
                }
            },
            entry_point="MockEvaluator"
        )
    
    def initialize(self, config):
        return True
    
    def cleanup(self):
        pass
    
    def create_evaluator(self, config):
        evaluator = Mock()
        evaluator.evaluate = AsyncMock(return_value=EvaluationScore(
            category=Category.HARMFUL_CONTENT,
            score=0.5,
            reasoning="Mock evaluation",
            confidence=0.8,
            details={}
        ))
        return evaluator
    
    def get_supported_categories(self):
        return [Category.HARMFUL_CONTENT]


@pytest.fixture
def temp_plugin_dir():
    """Create temporary plugin directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def plugin_manager(temp_plugin_dir):
    """Create plugin manager with temporary directory."""
    return PluginManager(temp_plugin_dir)


@pytest.fixture
def mock_plugin_file(temp_plugin_dir):
    """Create a mock plugin file."""
    plugin_content = '''
from src.plugins.plugin_system import EvaluatorPlugin, PluginInfo
from src.evaluators.base_evaluator import BaseEvaluator
from src.models.data_models import Category

class TestPlugin(EvaluatorPlugin):
    def get_plugin_info(self):
        return PluginInfo(
            name="test_plugin",
            version="1.0.0",
            author="Test",
            description="Test plugin",
            category="evaluator",
            dependencies=[],
            config_schema={},
            entry_point="TestEvaluator"
        )
    
    def initialize(self, config):
        return True
    
    def cleanup(self):
        pass
    
    def create_evaluator(self, config):
        return None
    
    def get_supported_categories(self):
        return [Category.HARMFUL_CONTENT]
'''
    
    plugin_file = temp_plugin_dir / "plugin_test.py"
    plugin_file.write_text(plugin_content)
    return plugin_file


class TestPluginManager:
    """Test plugin manager functionality."""
    
    def test_initialization(self, plugin_manager):
        """Test plugin manager initialization."""
        assert plugin_manager.plugins_dir.exists()
        assert isinstance(plugin_manager.plugins, dict)
        assert isinstance(plugin_manager.plugin_configs, dict)
        assert isinstance(plugin_manager.evaluator_plugins, dict)
    
    def test_discover_plugins(self, plugin_manager, mock_plugin_file):
        """Test plugin discovery."""
        discovered = plugin_manager.discover_plugins()
        assert len(discovered) == 1
        assert mock_plugin_file in discovered
    
    def test_plugin_config_persistence(self, plugin_manager):
        """Test plugin configuration saving and loading."""
        # Create test config
        test_config = {
            "test_plugin": {
                "enabled": True,
                "config": {"threshold": 0.7},
                "priority": 1
            }
        }
        
        # Save config
        config_file = plugin_manager.plugins_dir / "plugins_config.json"
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Create new manager to test loading
        new_manager = PluginManager(plugin_manager.plugins_dir)
        assert "test_plugin" in new_manager.plugin_configs
        assert new_manager.plugin_configs["test_plugin"].enabled is True
        assert new_manager.plugin_configs["test_plugin"].config["threshold"] == 0.7
    
    def test_enable_disable_plugin(self, plugin_manager):
        """Test enabling and disabling plugins."""
        plugin_name = "test_plugin"
        
        # Initially not in configs
        assert plugin_name not in plugin_manager.plugin_configs
        
        # Enable (should create config)
        success = plugin_manager.enable_plugin(plugin_name)
        assert success is True
        assert plugin_name in plugin_manager.plugin_configs
        assert plugin_manager.plugin_configs[plugin_name].enabled is True
        
        # Disable
        success = plugin_manager.disable_plugin(plugin_name)
        assert success is True
        assert plugin_manager.plugin_configs[plugin_name].enabled is False
    
    def test_create_plugin_template(self, plugin_manager):
        """Test plugin template creation."""
        plugin_name = "my_custom_evaluator"
        
        template_path = plugin_manager.create_plugin_template(plugin_name, "evaluator")
        
        assert template_path.exists()
        assert template_path.name == f"plugin_{plugin_name}.py"
        
        content = template_path.read_text()
        assert f"Custom{plugin_name.title()}Evaluator" in content
        assert f"{plugin_name.title()}Plugin" in content
    
    def test_plugin_info_retrieval(self, plugin_manager):
        """Test getting plugin information."""
        # Mock plugin not loaded
        info = plugin_manager.get_plugin_info("nonexistent")
        assert info is None
        
        # Add mock plugin
        mock_plugin = MockEvaluatorPlugin()
        plugin_manager.plugins["mock_evaluator"] = mock_plugin
        
        info = plugin_manager.get_plugin_info("mock_evaluator")
        assert info is not None
        assert info.name == "mock_evaluator"
        assert info.version == "1.0.0"


class TestPluginIntegration:
    """Test plugin integration with evaluation system."""
    
    @pytest.fixture
    def mock_prompt(self):
        """Create mock test prompt."""
        return TestPrompt(
            id="test_001",
            text="Test prompt",
            language=Language.EN,
            category=Category.HARMFUL_CONTENT,
            expected_behavior="Test behavior",
            severity=Severity.MEDIUM
        )
    
    @pytest.fixture
    def mock_response(self):
        """Create mock model response."""
        return ModelResponse(
            id="resp_001",
            model_name="test_model",
            text="Test response",
            timestamp=None,
            processing_time=0.1,
            metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_plugin_evaluation(self, plugin_manager, mock_prompt, mock_response):
        """Test evaluation using plugin evaluators."""
        # Add mock plugin
        mock_plugin = MockEvaluatorPlugin()
        plugin_manager.plugins["mock_evaluator"] = mock_plugin
        plugin_manager.evaluator_plugins["mock_evaluator"] = mock_plugin
        plugin_manager._register_evaluator_plugin(mock_plugin)
        
        # Get evaluators for category
        evaluators = plugin_manager.get_evaluators_for_category(Category.HARMFUL_CONTENT)
        assert len(evaluators) == 1
        
        # Test evaluation
        evaluator = evaluators[0]
        result = await evaluator.evaluate(mock_prompt, mock_response)
        
        assert result.category == Category.HARMFUL_CONTENT
        assert result.score == 0.5
        assert result.reasoning == "Mock evaluation"
        assert result.confidence == 0.8
    
    def test_plugin_configuration_validation(self, plugin_manager):
        """Test plugin configuration validation."""
        mock_plugin = MockEvaluatorPlugin()
        
        # Valid config
        valid_config = {"threshold": 0.7}
        assert mock_plugin.validate_config(valid_config) is True
        
        # Invalid config (depends on plugin implementation)
        # This is a basic test - real plugins would have more validation
        assert mock_plugin.validate_config({}) is True  # Empty config should be valid
    
    def test_plugin_lifecycle(self, plugin_manager):
        """Test plugin lifecycle (load, initialize, cleanup)."""
        mock_plugin = MockEvaluatorPlugin()
        plugin_name = "mock_evaluator"
        
        # Initialize
        assert mock_plugin.initialize({}) is True
        
        # Add to manager
        plugin_manager.plugins[plugin_name] = mock_plugin
        plugin_manager.evaluator_plugins[plugin_name] = mock_plugin
        
        # Unload
        success = plugin_manager.unload_plugin(plugin_name)
        assert success is True
        assert plugin_name not in plugin_manager.plugins
        assert plugin_name not in plugin_manager.evaluator_plugins


class TestPluginErrors:
    """Test plugin error handling."""
    
    def test_invalid_plugin_file(self, plugin_manager, temp_plugin_dir):
        """Test handling of invalid plugin files."""
        # Create invalid plugin file
        invalid_file = temp_plugin_dir / "plugin_invalid.py"
        invalid_file.write_text("invalid python syntax !!!")
        
        # Should not crash
        success = plugin_manager.load_plugin(invalid_file)
        assert success is False
    
    def test_plugin_without_required_methods(self, plugin_manager, temp_plugin_dir):
        """Test handling of plugins without required methods."""
        # Create plugin without required methods
        incomplete_plugin = '''
class IncompletePlugin:
    pass
'''
        
        plugin_file = temp_plugin_dir / "plugin_incomplete.py"
        plugin_file.write_text(incomplete_plugin)
        
        # Should not crash
        success = plugin_manager.load_plugin(plugin_file)
        assert success is False
    
    def test_plugin_initialization_failure(self, plugin_manager):
        """Test handling of plugin initialization failures."""
        class FailingPlugin(EvaluatorPlugin):
            def get_plugin_info(self):
                return PluginInfo(
                    name="failing_plugin",
                    version="1.0.0",
                    author="Test",
                    description="Failing plugin",
                    category="evaluator",
                    dependencies=[],
                    config_schema={},
                    entry_point="FailingEvaluator"
                )
            
            def initialize(self, config):
                raise Exception("Initialization failed")
            
            def cleanup(self):
                pass
            
            def create_evaluator(self, config):
                return None
            
            def get_supported_categories(self):
                return [Category.HARMFUL_CONTENT]
        
        # Should handle initialization failure gracefully
        failing_plugin = FailingPlugin()
        plugin_manager.plugins["failing_plugin"] = failing_plugin
        
        # Should not crash when trying to initialize
        try:
            failing_plugin.initialize({})
        except Exception:
            pass  # Expected to fail
    
    def test_missing_plugin_directory(self):
        """Test handling of missing plugin directory."""
        nonexistent_path = Path("/nonexistent/path")
        
        # Should create directory or handle gracefully
        manager = PluginManager(nonexistent_path)
        assert manager.plugins_dir == nonexistent_path
        
        # Discovery should return empty list for nonexistent directory
        discovered = manager.discover_plugins()
        assert len(discovered) == 0


@pytest.mark.integration
class TestPluginSystemIntegration:
    """Integration tests for the complete plugin system."""
    
    def test_end_to_end_plugin_usage(self, plugin_manager, temp_plugin_dir):
        """Test complete plugin usage from creation to evaluation."""
        # Create plugin template
        plugin_name = "integration_test_evaluator"
        template_path = plugin_manager.create_plugin_template(plugin_name)
        
        assert template_path.exists()
        
        # Enable plugin
        success = plugin_manager.enable_plugin(plugin_name)
        assert success is True
        
        # Check configuration was created
        assert plugin_name in plugin_manager.plugin_configs
        assert plugin_manager.plugin_configs[plugin_name].enabled is True
        
        # Disable plugin
        success = plugin_manager.disable_plugin(plugin_name)
        assert success is True
        assert plugin_manager.plugin_configs[plugin_name].enabled is False
    
    def test_multiple_plugins_same_category(self, plugin_manager):
        """Test multiple plugins supporting the same category."""
        # Add multiple mock plugins
        plugin1 = MockEvaluatorPlugin()
        plugin2 = MockEvaluatorPlugin()
        
        # Modify second plugin to have different name
        plugin2.get_plugin_info = lambda: PluginInfo(
            name="mock_evaluator_2",
            version="1.0.0",
            author="Test Author 2",
            description="Second mock evaluator",
            category="evaluator",
            dependencies=[],
            config_schema={},
            entry_point="MockEvaluator2"
        )
        
        # Register both plugins
        plugin_manager.plugins["mock_evaluator"] = plugin1
        plugin_manager.evaluator_plugins["mock_evaluator"] = plugin1
        plugin_manager._register_evaluator_plugin(plugin1)
        
        plugin_manager.plugins["mock_evaluator_2"] = plugin2
        plugin_manager.evaluator_plugins["mock_evaluator_2"] = plugin2
        plugin_manager._register_evaluator_plugin(plugin2)
        
        # Should have multiple evaluators for the same category
        evaluators = plugin_manager.get_evaluators_for_category(Category.HARMFUL_CONTENT)
        assert len(evaluators) >= 2