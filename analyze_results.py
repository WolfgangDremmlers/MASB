"""Command-line tool for analyzing MASB results."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.result_analyzer import ResultAnalyzer
from src.utils.logger import logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MASB Results Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate comprehensive report
  python analyze_results.py --report
  
  # Compare specific models
  python analyze_results.py --model-comparison --models gpt-4 claude-3-opus
  
  # Analyze specific language
  python analyze_results.py --language-analysis --language en
  
  # Export results to CSV
  python analyze_results.py --export-csv
        """
    )
    
    # Analysis options
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive HTML report"
    )
    
    parser.add_argument(
        "--model-comparison",
        action="store_true",
        help="Generate model comparison plots"
    )
    
    parser.add_argument(
        "--language-analysis",
        action="store_true",
        help="Generate language comparison analysis"
    )
    
    parser.add_argument(
        "--category-breakdown",
        action="store_true",
        help="Generate category breakdown analysis"
    )
    
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export results to CSV format"
    )
    
    # Filters
    parser.add_argument(
        "--models",
        nargs="+",
        help="Filter by specific models"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        help="Filter by specific language"
    )
    
    parser.add_argument(
        "--category",
        type=str,
        help="Filter by specific category"
    )
    
    # Input/output
    parser.add_argument(
        "--results-dir",
        type=Path,
        help="Directory containing result files"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file/directory path"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="Analyze specific result file"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Initialize analyzer
    analyzer = ResultAnalyzer(args.results_dir)
    
    # Load results
    try:
        results = analyzer.load_results(args.file)
        if not results:
            print("No results found to analyze.")
            return
            
        print(f"Loaded {len(results)} result files for analysis.")
        
    except Exception as e:
        logger.error(f"Failed to load results: {e}")
        return
    
    # Apply filters
    if args.models:
        results = [r for r in results if r.model_name in args.models]
        print(f"Filtered to {len(results)} results matching models: {args.models}")
    
    if args.language:
        results = [r for r in results if r.language.value == args.language]
        print(f"Filtered to {len(results)} results for language: {args.language}")
    
    if not results:
        print("No results match the specified filters.")
        return
    
    # Generate analyses
    try:
        if args.report:
            print("Generating comprehensive report...")
            report_path = analyzer.generate_report(results, args.output)
            print(f"Report saved to: {report_path}")
        
        if args.model_comparison:
            print("Generating model comparison...")
            fig = analyzer.plot_model_comparison(
                results, 
                language=args.language,
                save_path=args.output / "model_comparison.html" if args.output else None
            )
            if not args.output:
                fig.show()
        
        if args.language_analysis:
            print("Generating language analysis...")
            fig = analyzer.plot_language_comparison(
                results,
                model=args.models[0] if args.models else None,
                save_path=args.output / "language_analysis.html" if args.output else None
            )
            if not args.output:
                fig.show()
        
        if args.category_breakdown:
            print("Generating category breakdown...")
            fig = analyzer.plot_category_breakdown(
                results,
                save_path=args.output / "category_breakdown.html" if args.output else None
            )
            if not args.output:
                fig.show()
        
        if args.export_csv:
            print("Exporting to CSV...")
            csv_path = analyzer.export_to_csv(results, args.output)
            print(f"CSV exported to: {csv_path}")
        
        # If no specific analysis requested, show summary
        if not any([args.report, args.model_comparison, args.language_analysis, 
                   args.category_breakdown, args.export_csv]):
            print("\nSummary Statistics:")
            print("=" * 50)
            
            df = analyzer.create_summary_dataframe(results)
            
            print(f"Models: {', '.join(df['model'].unique())}")
            print(f"Languages: {', '.join(df['language'].unique())}")
            print(f"Categories: {', '.join(df['category'].unique())}")
            print(f"Total evaluations: {len(df)}")
            
            print("\nMean scores by category:")
            category_means = df.groupby('category')['mean_score'].mean()
            for category, score in category_means.items():
                print(f"  {category}: {score:.3f}")
            
            print("\nPass rates by category:")
            category_pass_rates = df.groupby('category')['pass_rate'].mean()
            for category, rate in category_pass_rates.items():
                print(f"  {category}: {rate:.1%}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()