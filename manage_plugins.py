#!/usr/bin/env python3
"""CLI tool for managing MASB plugins."""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.plugins.plugin_system import plugin_manager
from src.utils.logger import logger
from src.config import settings


def list_plugins():
    """List all available plugins."""
    print("\n🔌 MASB Plugin Manager")
    print("=" * 60)
    
    try:
        # Discover plugins
        plugin_files = plugin_manager.discover_plugins()
        print(f"📁 Plugin directory: {plugin_manager.plugins_dir}")
        print(f"🔍 Found {len(plugin_files)} plugin files")
        
        # Load plugins to get their info
        loaded_count = plugin_manager.load_all_plugins()
        print(f"✅ Loaded {loaded_count} plugins successfully")
        
        # List plugin information
        plugin_infos = plugin_manager.list_plugins()
        
        if not plugin_infos:
            print("\n❌ No plugins found")
            return
        
        print(f"\n📋 Plugin List ({len(plugin_infos)} total):")
        print("-" * 60)
        
        for info in plugin_infos:
            status_icon = {
                'active': '🟢',
                'inactive': '🔴',
                'error': '🔸',
                'loading': '🟡'
            }.get(info.status.value, '⚪')
            
            enabled = info.name in plugin_manager.plugins
            enabled_text = "✅ Enabled" if enabled else "❌ Disabled"
            
            print(f"\n{status_icon} {info.name} v{info.version}")
            print(f"   Author: {info.author}")
            print(f"   Description: {info.description}")
            print(f"   Category: {info.category}")
            print(f"   Status: {enabled_text}")
            
            if info.name in plugin_manager.evaluator_plugins:
                evaluator_plugin = plugin_manager.evaluator_plugins[info.name]
                categories = evaluator_plugin.get_supported_categories()
                print(f"   Supports: {', '.join([c.value for c in categories])}")
            
            if info.error_message:
                print(f"   ⚠️  Error: {info.error_message}")
        
        print(f"\n{'='*60}")
        
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        print(f"❌ Error listing plugins: {e}")


def enable_plugin(plugin_name: str):
    """Enable a plugin."""
    print(f"🔌 Enabling plugin: {plugin_name}")
    
    try:
        success = plugin_manager.enable_plugin(plugin_name)
        
        if success:
            # Reload to activate
            plugin_manager.load_all_plugins()
            print(f"✅ Plugin '{plugin_name}' enabled successfully")
        else:
            print(f"❌ Plugin '{plugin_name}' not found")
            return False
            
    except Exception as e:
        logger.error(f"Failed to enable plugin {plugin_name}: {e}")
        print(f"❌ Error enabling plugin: {e}")
        return False
    
    return True


def disable_plugin(plugin_name: str):
    """Disable a plugin."""
    print(f"🔌 Disabling plugin: {plugin_name}")
    
    try:
        success = plugin_manager.disable_plugin(plugin_name)
        
        if success:
            print(f"✅ Plugin '{plugin_name}' disabled successfully")
        else:
            print(f"❌ Plugin '{plugin_name}' not found")
            return False
            
    except Exception as e:
        logger.error(f"Failed to disable plugin {plugin_name}: {e}")
        print(f"❌ Error disabling plugin: {e}")
        return False
    
    return True


def create_plugin(plugin_name: str, plugin_type: str = "evaluator"):
    """Create a new plugin template."""
    print(f"🛠️  Creating plugin template: {plugin_name}")
    
    try:
        template_path = plugin_manager.create_plugin_template(plugin_name, plugin_type)
        print(f"✅ Plugin template created: {template_path}")
        print(f"📝 Edit the file to implement your custom evaluator")
        print(f"🔄 Run 'python manage_plugins.py --reload' to load your plugin")
        
    except Exception as e:
        logger.error(f"Failed to create plugin {plugin_name}: {e}")
        print(f"❌ Error creating plugin: {e}")
        return False
    
    return True


def reload_plugins():
    """Reload all plugins."""
    print("🔄 Reloading plugins...")
    
    try:
        loaded_count = plugin_manager.load_all_plugins()
        print(f"✅ Reloaded plugins successfully - {loaded_count} loaded")
        
    except Exception as e:
        logger.error(f"Failed to reload plugins: {e}")
        print(f"❌ Error reloading plugins: {e}")
        return False
    
    return True


def show_plugin_info(plugin_name: str):
    """Show detailed information about a plugin."""
    print(f"🔍 Plugin Information: {plugin_name}")
    print("=" * 60)
    
    try:
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        
        if not plugin_info:
            print(f"❌ Plugin '{plugin_name}' not found")
            return False
        
        print(f"Name: {plugin_info.name}")
        print(f"Version: {plugin_info.version}")
        print(f"Author: {plugin_info.author}")
        print(f"Description: {plugin_info.description}")
        print(f"Category: {plugin_info.category}")
        print(f"Status: {plugin_info.status.value}")
        print(f"Entry Point: {plugin_info.entry_point}")
        
        if plugin_info.dependencies:
            print(f"Dependencies: {', '.join(plugin_info.dependencies)}")
        
        if plugin_info.error_message:
            print(f"⚠️  Error: {plugin_info.error_message}")
        
        # Show configuration schema
        if plugin_info.config_schema:
            print(f"\nConfiguration Schema:")
            print(json.dumps(plugin_info.config_schema, indent=2))
        
        # Show current configuration
        if plugin_name in plugin_manager.plugin_configs:
            config = plugin_manager.plugin_configs[plugin_name]
            print(f"\nCurrent Configuration:")
            print(f"  Enabled: {config.enabled}")
            print(f"  Priority: {config.priority}")
            if config.config:
                print(f"  Config: {json.dumps(config.config, indent=2)}")
        
        # Show supported categories for evaluator plugins
        if plugin_name in plugin_manager.evaluator_plugins:
            evaluator_plugin = plugin_manager.evaluator_plugins[plugin_name]
            categories = evaluator_plugin.get_supported_categories()
            print(f"\nSupported Categories: {', '.join([c.value for c in categories])}")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to get plugin info for {plugin_name}: {e}")
        print(f"❌ Error getting plugin info: {e}")
        return False
    
    return True


def test_plugin(plugin_name: str):
    """Test a plugin with a sample prompt."""
    print(f"🧪 Testing plugin: {plugin_name}")
    
    try:
        # Check if plugin is loaded
        if plugin_name not in plugin_manager.evaluator_plugins:
            print(f"❌ Plugin '{plugin_name}' not found or not an evaluator plugin")
            return False
        
        evaluator_plugin = plugin_manager.evaluator_plugins[plugin_name]
        
        # Get plugin configuration
        config = plugin_manager.plugin_configs.get(plugin_name, {}).config or {}
        
        # Create evaluator instance
        evaluator = evaluator_plugin.create_evaluator(config)
        
        # Create a test prompt and response
        from src.models.data_models import TestPrompt, ModelResponse, Category, Language, Severity
        
        test_prompt = TestPrompt(
            id="test_001",
            text="This is a test prompt for harmful content detection.",
            language=Language.EN,
            category=Category.HARMFUL_CONTENT,
            expected_behavior="Should refuse harmful requests",
            severity=Severity.HIGH
        )
        
        test_response = ModelResponse(
            id="test_response_001",
            model_name="test_model",
            text="I cannot and will not provide information that could be harmful.",
            timestamp=None,
            processing_time=0.1,
            metadata={}
        )
        
        # Run evaluation
        import asyncio
        result = asyncio.run(evaluator.evaluate(test_prompt, test_response))
        
        print(f"✅ Plugin test completed successfully!")
        print(f"📊 Test Results:")
        print(f"   Category: {result.category.value}")
        print(f"   Score: {result.score:.3f}")
        print(f"   Confidence: {result.confidence:.3f}")
        print(f"   Reasoning: {result.reasoning}")
        if result.details:
            print(f"   Details: {json.dumps(result.details, indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to test plugin {plugin_name}: {e}")
        print(f"❌ Error testing plugin: {e}")
        return False
    
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MASB Plugin Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all plugins
  python manage_plugins.py --list
  
  # Create a new plugin template
  python manage_plugins.py --create sentiment_analyzer
  
  # Enable a plugin
  python manage_plugins.py --enable sentiment_evaluator
  
  # Disable a plugin
  python manage_plugins.py --disable keyword_evaluator
  
  # Show plugin information
  python manage_plugins.py --info sentiment_evaluator
  
  # Test a plugin
  python manage_plugins.py --test sentiment_evaluator
  
  # Reload all plugins
  python manage_plugins.py --reload
        """
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all available plugins')
    
    parser.add_argument('--create', type=str,
                       help='Create a new plugin template with the given name')
    
    parser.add_argument('--enable', type=str,
                       help='Enable a plugin by name')
    
    parser.add_argument('--disable', type=str,
                       help='Disable a plugin by name')
    
    parser.add_argument('--info', type=str,
                       help='Show detailed information about a plugin')
    
    parser.add_argument('--test', type=str,
                       help='Test a plugin with a sample prompt')
    
    parser.add_argument('--reload', action='store_true',
                       help='Reload all plugins')
    
    parser.add_argument('--plugin-type', type=str, default='evaluator',
                       choices=['evaluator'],
                       help='Type of plugin to create (default: evaluator)')
    
    args = parser.parse_args()
    
    if args.list:
        list_plugins()
    elif args.create:
        success = create_plugin(args.create, args.plugin_type)
        sys.exit(0 if success else 1)
    elif args.enable:
        success = enable_plugin(args.enable)
        sys.exit(0 if success else 1)
    elif args.disable:
        success = disable_plugin(args.disable)
        sys.exit(0 if success else 1)
    elif args.info:
        success = show_plugin_info(args.info)
        sys.exit(0 if success else 1)
    elif args.test:
        success = test_plugin(args.test)
        sys.exit(0 if success else 1)
    elif args.reload:
        success = reload_plugins()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()