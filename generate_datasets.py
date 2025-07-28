#!/usr/bin/env python3
"""CLI tool for generating multi-language datasets for MASB."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.localization.dataset_generator import dataset_generator, MultiLanguageDatasetGenerator
from src.localization.languages import ExtendedLanguage, EXTENDED_LANGUAGE_INFO
from src.models.data_models import Category


def list_languages():
    """List all supported languages."""
    print("\n🌍 Supported Languages:")
    print("=" * 80)
    print(f"{'Code':<6} {'Name':<20} {'Native Name':<20} {'Family':<15} {'AI Support':<12}")
    print("-" * 80)
    
    for code, info in EXTENDED_LANGUAGE_INFO.items():
        support_indicator = {
            'excellent': '🟢',
            'good': '🟡', 
            'fair': '🟠',
            'poor': '🔴'
        }.get(info.ai_support_level, '⚪')
        
        print(f"{code:<6} {info.name:<20} {info.native_name:<20} {info.family:<15} {support_indicator} {info.ai_support_level}")


def generate_dataset(languages, categories, output_dir, prompts_per_language, verbose):
    """Generate datasets for specified languages and categories."""
    print(f"\n🚀 Generating Multi-Language Datasets")
    print("=" * 50)
    
    # Parse languages
    if languages:
        lang_codes = languages.split(',')
        target_languages = []
        for code in lang_codes:
            try:
                lang = ExtendedLanguage(code.strip())
                target_languages.append(lang)
            except ValueError:
                print(f"❌ Unknown language code: {code}")
                return False
    else:
        # Default to major languages
        target_languages = [
            ExtendedLanguage.EN, ExtendedLanguage.ZH, ExtendedLanguage.FR,
            ExtendedLanguage.ES, ExtendedLanguage.DE, ExtendedLanguage.JA
        ]
    
    # Parse categories
    target_categories = None
    if categories:
        cat_names = categories.split(',')
        target_categories = []
        for cat_name in cat_names:
            try:
                cat = Category(cat_name.strip().lower())
                target_categories.append(cat)
            except ValueError:
                print(f"❌ Unknown category: {cat_name}")
                return False
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate datasets
    generator = MultiLanguageDatasetGenerator()
    total_prompts = 0
    
    for language in target_languages:
        lang_info = EXTENDED_LANGUAGE_INFO.get(language.value)
        print(f"\n📝 Generating dataset for {lang_info.name} ({language.value})...")
        
        if target_categories:
            # Generate for specific categories
            for category in target_categories:
                prompts = generator.generate_prompts(
                    language=language,
                    category=category,
                    count=prompts_per_language // len(target_categories)
                )
                
                # Save category-specific dataset
                output_file = output_path / f"{language.value}_{category.value}_dataset.json"
                generator.save_dataset(prompts, output_file)
                
                total_prompts += len(prompts)
                if verbose:
                    print(f"  ✅ {category.value}: {len(prompts)} prompts -> {output_file}")
        else:
            # Generate for all categories
            prompts = generator.generate_prompts(
                language=language,
                count=prompts_per_language
            )
            
            # Save complete dataset
            output_file = output_path / f"{language.value}_dataset.json"
            generator.save_dataset(prompts, output_file)
            
            total_prompts += len(prompts)
            if verbose:
                print(f"  ✅ All categories: {len(prompts)} prompts -> {output_file}")
    
    print(f"\n🎉 Dataset generation completed!")
    print(f"📊 Total prompts generated: {total_prompts}")
    print(f"📂 Output directory: {output_path.absolute()}")
    
    return True


def analyze_language_coverage():
    """Analyze language coverage and AI support levels."""
    print("\n📊 Language Coverage Analysis")
    print("=" * 50)
    
    # Group by AI support level
    support_levels = {}
    for code, info in EXTENDED_LANGUAGE_INFO.items():
        level = info.ai_support_level
        if level not in support_levels:
            support_levels[level] = []
        support_levels[level].append(info)
    
    # Display statistics
    total_languages = len(EXTENDED_LANGUAGE_INFO)
    print(f"Total supported languages: {total_languages}")
    
    for level in ['excellent', 'good', 'fair', 'poor']:
        if level in support_levels:
            count = len(support_levels[level])
            percentage = (count / total_languages) * 100
            print(f"{level.capitalize()} AI support: {count} languages ({percentage:.1f}%)")
            
            if len(support_levels[level]) <= 10:  # Show details for smaller groups
                langs = [f"{info.name} ({info.code})" for info in support_levels[level]]
                print(f"  Languages: {', '.join(langs)}")
    
    # Language families
    families = {}
    for info in EXTENDED_LANGUAGE_INFO.values():
        family = info.family
        if family not in families:
            families[family] = 0
        families[family] += 1
    
    print(f"\nLanguage families represented: {len(families)}")
    for family, count in sorted(families.items(), key=lambda x: x[1], reverse=True):
        print(f"  {family}: {count} languages")
    
    # Script systems
    scripts = {}
    for info in EXTENDED_LANGUAGE_INFO.values():
        script = info.script
        if script not in scripts:
            scripts[script] = 0
        scripts[script] += 1
    
    print(f"\nScript systems supported: {len(scripts)}")
    for script, count in sorted(scripts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {script}: {count} languages")
    
    # RTL languages
    rtl_count = sum(1 for info in EXTENDED_LANGUAGE_INFO.values() if info.rtl)
    print(f"\nRight-to-left languages: {rtl_count} ({(rtl_count/total_languages)*100:.1f}%)")


def validate_datasets(dataset_dir):
    """Validate existing datasets."""
    print(f"\n🔍 Validating datasets in {dataset_dir}")
    print("=" * 50)
    
    dataset_path = Path(dataset_dir)
    if not dataset_path.exists():
        print(f"❌ Directory not found: {dataset_dir}")
        return False
    
    json_files = list(dataset_path.glob("*_dataset.json"))
    if not json_files:
        print(f"❌ No dataset files found in {dataset_dir}")
        return False
    
    print(f"Found {len(json_files)} dataset files")
    
    total_prompts = 0
    valid_files = 0
    
    for json_file in json_files:
        try:
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list) and len(data) > 0:
                # Validate structure
                sample = data[0]
                required_fields = ['id', 'text', 'language', 'category', 'expected_behavior', 'severity']
                
                if all(field in sample for field in required_fields):
                    total_prompts += len(data)
                    valid_files += 1
                    print(f"  ✅ {json_file.name}: {len(data)} prompts")
                else:
                    print(f"  ❌ {json_file.name}: Missing required fields")
            else:
                print(f"  ❌ {json_file.name}: Invalid format")
                
        except Exception as e:
            print(f"  ❌ {json_file.name}: Error reading file - {e}")
    
    print(f"\n📊 Validation Summary:")
    print(f"Valid files: {valid_files}/{len(json_files)}")
    print(f"Total prompts: {total_prompts}")
    
    return valid_files == len(json_files)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MASB Multi-Language Dataset Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all supported languages
  python generate_datasets.py --list-languages
  
  # Generate datasets for major languages (default)
  python generate_datasets.py --generate --output-dir ./datasets
  
  # Generate for specific languages
  python generate_datasets.py --generate --languages "en,zh,fr,es" --output-dir ./datasets
  
  # Generate for specific categories
  python generate_datasets.py --generate --categories "hallucination,bias" --output-dir ./datasets
  
  # Analyze language coverage
  python generate_datasets.py --analyze-coverage
  
  # Validate existing datasets
  python generate_datasets.py --validate ./datasets
        """
    )
    
    parser.add_argument('--list-languages', action='store_true',
                       help='List all supported languages')
    
    parser.add_argument('--generate', action='store_true',
                       help='Generate multi-language datasets')
    
    parser.add_argument('--languages', type=str,
                       help='Comma-separated list of language codes (default: major languages)')
    
    parser.add_argument('--categories', type=str,
                       help='Comma-separated list of categories (default: all categories)')
    
    parser.add_argument('--output-dir', type=str, default='./datasets',
                       help='Output directory for datasets (default: ./datasets)')
    
    parser.add_argument('--prompts-per-language', type=int, default=100,
                       help='Number of prompts per language (default: 100)')
    
    parser.add_argument('--analyze-coverage', action='store_true',
                       help='Analyze language coverage and support levels')
    
    parser.add_argument('--validate', type=str,
                       help='Validate datasets in specified directory')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.list_languages:
        list_languages()
    elif args.generate:
        success = generate_dataset(
            args.languages,
            args.categories, 
            args.output_dir,
            args.prompts_per_language,
            args.verbose
        )
        sys.exit(0 if success else 1)
    elif args.analyze_coverage:
        analyze_language_coverage()
    elif args.validate:
        success = validate_datasets(args.validate)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()