"""Example usage of MASB for evaluation and analysis."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.evaluation_engine import EvaluationEngine
from src.models.data_models import ModelConfig, Language, Category
from src.analysis.result_analyzer import ResultAnalyzer
from src.utils.logger import logger


async def example_basic_evaluation():
    """Example: Basic model evaluation."""
    print("🔍 Running basic evaluation example...")
    
    # Create evaluation engine (using a mock model for demonstration)
    # In practice, you'd use a real model like "claude-3-opus"
    try:
        engine = EvaluationEngine("gpt-3.5-turbo")
        
        # Run evaluation on a small dataset
        result = await engine.evaluate_dataset(
            language=Language.ENGLISH,
            category=Category.HARMFUL_CONTENT,
            max_prompts=5
        )
        
        # Print summary
        print(engine.get_summary_report(result))
        
    except Exception as e:
        print(f"⚠️  Could not run evaluation: {e}")
        print("   Make sure you have API keys configured in .env file")


async def example_custom_configuration():
    """Example: Custom model configuration."""
    print("\n⚙️  Custom configuration example...")
    
    # Custom model configuration
    custom_config = ModelConfig(
        name="gpt-4",
        provider="openai",
        temperature=0.3,  # Lower temperature for more deterministic responses
        max_tokens=200,   # Shorter responses
        top_p=0.9
    )
    
    try:
        engine = EvaluationEngine("gpt-4", custom_config)
        
        # Evaluate with custom settings
        result = await engine.evaluate_dataset(
            language=Language.GERMAN,
            max_prompts=3
        )
        
        print(f"✅ Evaluated {result.completed_prompts} prompts with custom config")
        
    except Exception as e:
        print(f"⚠️  Could not run custom evaluation: {e}")


def example_analysis():
    """Example: Analyzing existing results."""
    print("\n📊 Analysis example...")
    
    # Initialize analyzer
    analyzer = ResultAnalyzer()
    
    try:
        # Load existing results
        results = analyzer.load_results()
        
        if not results:
            print("📝 No existing results found. Run evaluations first.")
            return
        
        print(f"📈 Found {len(results)} result files")
        
        # Create summary dataframe
        df = analyzer.create_summary_dataframe(results)
        print(f"📋 Summary contains {len(df)} evaluation records")
        
        # Show basic statistics
        if not df.empty:
            print("\n🎯 Top performing categories:")
            category_means = df.groupby('category')['mean_score'].mean().sort_values(ascending=False)
            for category, score in category_means.head(3).items():
                print(f"   {category}: {score:.3f}")
        
        # Generate plots (won't display in console, but will create files)
        try:
            fig = analyzer.plot_model_comparison(results)
            print("📊 Model comparison plot created")
        except Exception as e:
            print(f"⚠️  Could not create plots: {e}")
        
    except Exception as e:
        print(f"⚠️  Analysis failed: {e}")


def example_dataset_management():
    """Example: Managing datasets."""
    print("\n📚 Dataset management example...")
    
    from src.utils.dataset_manager import DatasetManager
    
    # Initialize dataset manager
    dataset_manager = DatasetManager()
    
    try:
        # Load English harmful content prompts
        prompts = dataset_manager.load_dataset(
            language=Language.ENGLISH,
            category=Category.HARMFUL_CONTENT
        )
        
        print(f"📋 Loaded {len(prompts)} prompts for harmful content evaluation")
        
        if prompts:
            # Show example prompt
            example = prompts[0]
            print(f"\n📝 Example prompt:")
            print(f"   ID: {example.id}")
            print(f"   Text: {example.text[:100]}...")
            print(f"   Expected: {example.expected_behavior[:100]}...")
            print(f"   Severity: {example.severity.value}")
        
        # Get dataset statistics
        stats = dataset_manager.get_statistics()
        print(f"\n📊 Dataset statistics:")
        print(f"   Total prompts: {stats['total_prompts']}")
        print(f"   Languages: {len(stats['by_language'])}")
        print(f"   Categories: {len(stats['by_category'])}")
        
    except Exception as e:
        print(f"⚠️  Dataset management failed: {e}")


async def main():
    """Run all examples."""
    print("🚀 MASB Usage Examples")
    print("=" * 50)
    
    # Dataset management example (doesn't require API keys)
    example_dataset_management()
    
    # Analysis example (uses existing results)
    example_analysis()
    
    # Evaluation examples (require API keys)
    print("\n🔑 Evaluation examples (require API keys):")
    await example_basic_evaluation()
    await example_custom_configuration()
    
    print("\n✅ Examples completed!")
    print("\n💡 Next steps:")
    print("   1. Set up your API keys in .env file")
    print("   2. Generate example datasets: python evaluate_model.py --generate-examples")
    print("   3. Run your first evaluation: python evaluate_model.py --model claude-3-opus --language en")
    print("   4. Analyze results: python analyze_results.py --report")


if __name__ == "__main__":
    asyncio.run(main())