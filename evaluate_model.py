"""Main script for running MASB evaluations."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.evaluation_engine import EvaluationEngine
from src.models.data_models import ModelConfig, Language, Category
from src.utils.logger import logger
from src.utils.generate_examples import generate_example_datasets
from src.config import settings, SUPPORTED_LANGUAGES, SUPPORTED_MODELS


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MASB - Multilingual Adversarial Safety Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate Claude on German prompts
  python evaluate_model.py --model claude-3-opus --language de
  
  # Evaluate GPT-4 on all English harmful content prompts
  python evaluate_model.py --model gpt-4 --language en --category harmful_content
  
  # Evaluate multiple languages with custom settings
  python evaluate_model.py --model gpt-3.5-turbo --language en de fr --max-prompts 50
  
  # Generate example datasets
  python evaluate_model.py --generate-examples
  
  # List supported models and languages
  python evaluate_model.py --list-models
        """
    )
    
    # Model and language selection
    parser.add_argument(
        "--model",
        type=str,
        help=f"Model to evaluate. Supported: {', '.join(SUPPORTED_MODELS.keys())}"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        nargs="+",
        help=f"Language(s) to evaluate. Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"
    )
    
    parser.add_argument(
        "--category",
        type=str,
        choices=[c.value for c in Category],
        help="Specific category to evaluate"
    )
    
    # Evaluation settings
    parser.add_argument(
        "--max-prompts",
        type=int,
        help="Maximum number of prompts to evaluate per language"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.batch_size,
        help=f"Batch size for concurrent requests (default: {settings.batch_size})"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=settings.default_temperature,
        help=f"Model temperature (default: {settings.default_temperature})"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=settings.default_max_tokens,
        help=f"Maximum tokens in response (default: {settings.default_max_tokens})"
    )
    
    # Utility options
    parser.add_argument(
        "--generate-examples",
        action="store_true",
        help="Generate example datasets for all languages"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all supported models"
    )
    
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all supported languages"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


async def run_evaluation(args):
    """Run the evaluation based on arguments."""
    # Create model config
    model_config = ModelConfig(
        name=args.model,
        provider=SUPPORTED_MODELS[args.model],
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    
    # Create evaluation engine
    try:
        engine = EvaluationEngine(args.model, model_config)
    except ValueError as e:
        logger.error(f"Failed to create evaluation engine: {e}")
        return
    
    # Run evaluations
    if len(args.language) == 1:
        # Single language
        language = args.language[0]
        category = Category(args.category) if args.category else None
        
        logger.info(f"Starting evaluation of {args.model} on {language}")
        
        result = await engine.evaluate_dataset(
            language=language,
            category=category,
            max_prompts=args.max_prompts,
            batch_size=args.batch_size
        )
        
        # Print summary
        print(engine.get_summary_report(result))
        
    else:
        # Multiple languages
        logger.info(f"Starting evaluation of {args.model} on {len(args.language)} languages")
        
        results = await engine.evaluate_multiple_languages(
            languages=args.language,
            category=Category(args.category) if args.category else None,
            max_prompts_per_language=args.max_prompts
        )
        
        # Print summaries
        for language, result in results.items():
            print(engine.get_summary_report(result))


def list_models():
    """List all supported models."""
    print("\nSupported Models:")
    print("-" * 40)
    
    # Group by provider
    providers = {}
    for model, provider in SUPPORTED_MODELS.items():
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model)
    
    for provider, models in sorted(providers.items()):
        print(f"\n{provider.upper()}:")
        for model in sorted(models):
            print(f"  - {model}")


def list_languages():
    """List all supported languages."""
    print("\nSupported Languages:")
    print("-" * 40)
    
    for code, name in SUPPORTED_LANGUAGES.items():
        print(f"  {code} - {name}")


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logger.info("Verbose logging enabled")
    
    # Handle utility commands
    if args.list_models:
        list_models()
        return
    
    if args.list_languages:
        list_languages()
        return
    
    if args.generate_examples:
        logger.info("Generating example datasets...")
        generate_example_datasets()
        print("\nExample datasets generated successfully!")
        print(f"Location: {settings.data_dir / 'prompts'}")
        return
    
    # Validate arguments for evaluation
    if not args.model:
        print("Error: --model is required for evaluation")
        print("Use --list-models to see supported models")
        return
    
    if not args.language:
        print("Error: --language is required for evaluation")
        print("Use --list-languages to see supported languages")
        return
    
    # Validate model
    if args.model not in SUPPORTED_MODELS:
        print(f"Error: Model '{args.model}' is not supported")
        print("Use --list-models to see supported models")
        return
    
    # Validate languages
    for lang in args.language:
        if lang not in SUPPORTED_LANGUAGES:
            print(f"Error: Language '{lang}' is not supported")
            print("Use --list-languages to see supported languages")
            return
    
    # Run evaluation
    try:
        asyncio.run(run_evaluation(args))
    except KeyboardInterrupt:
        logger.info("Evaluation interrupted by user")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()