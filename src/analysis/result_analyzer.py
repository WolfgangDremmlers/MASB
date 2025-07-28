"""Analysis and visualization tools for MASB results."""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from src.models.data_models import BatchEvaluationResult, Category, Language, EvaluationResult
from src.config import settings, SAFETY_THRESHOLDS
from src.utils.logger import logger


class ResultAnalyzer:
    """Analyzer for MASB evaluation results."""
    
    def __init__(self, results_dir: Optional[Path] = None):
        """Initialize result analyzer.
        
        Args:
            results_dir: Directory containing result files
        """
        self.results_dir = results_dir or settings.results_dir
        self.results_cache: Dict[str, BatchEvaluationResult] = {}
        
    def load_results(self, filename: Optional[str] = None) -> List[BatchEvaluationResult]:
        """Load results from files.
        
        Args:
            filename: Specific file to load, or None for all files
            
        Returns:
            List of batch evaluation results
        """
        results = []
        
        if filename:
            # Load specific file
            file_path = self.results_dir / filename
            if file_path.exists():
                result = self._load_single_result(file_path)
                if result:
                    results.append(result)
        else:
            # Load all result files
            for file_path in self.results_dir.glob("*.json"):
                result = self._load_single_result(file_path)
                if result:
                    results.append(result)
        
        logger.info(f"Loaded {len(results)} result files")
        return results
    
    def _load_single_result(self, file_path: Path) -> Optional[BatchEvaluationResult]:
        """Load a single result file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert string timestamps back to datetime
            data['start_time'] = datetime.fromisoformat(data['start_time'])
            if data.get('end_time'):
                data['end_time'] = datetime.fromisoformat(data['end_time'])
            
            # Convert nested timestamps
            for result in data.get('results', []):
                if 'response' in result and 'timestamp' in result['response']:
                    result['response']['timestamp'] = datetime.fromisoformat(result['response']['timestamp'])
            
            return BatchEvaluationResult(**data)
            
        except Exception as e:
            logger.warning(f"Failed to load result file {file_path}: {e}")
            return None
    
    def create_summary_dataframe(self, results: List[BatchEvaluationResult]) -> pd.DataFrame:
        """Create a summary DataFrame from results.
        
        Args:
            results: List of batch results
            
        Returns:
            Summary DataFrame
        """
        summary_data = []
        
        for batch_result in results:
            for category, stats in batch_result.summary.items():
                summary_data.append({
                    'model': batch_result.model_name,
                    'language': batch_result.language.value,
                    'category': category.value,
                    'mean_score': stats['mean'],
                    'min_score': stats['min'],
                    'max_score': stats['max'],
                    'pass_rate': stats['pass_rate'],
                    'total_prompts': batch_result.total_prompts,
                    'completed_prompts': batch_result.completed_prompts,
                    'failed_prompts': batch_result.failed_prompts,
                    'duration': batch_result.duration,
                    'date': batch_result.start_time.date() if batch_result.start_time else None
                })
        
        return pd.DataFrame(summary_data)
    
    def create_detailed_dataframe(self, results: List[BatchEvaluationResult]) -> pd.DataFrame:
        """Create a detailed DataFrame with individual prompt results.
        
        Args:
            results: List of batch results
            
        Returns:
            Detailed DataFrame
        """
        detailed_data = []
        
        for batch_result in results:
            for eval_result in batch_result.results:
                for score in eval_result.scores:
                    detailed_data.append({
                        'model': batch_result.model_name,
                        'language': batch_result.language.value,
                        'category': score.category.value,
                        'prompt_id': eval_result.prompt.id,
                        'prompt_text': eval_result.prompt.text[:100] + "..." if len(eval_result.prompt.text) > 100 else eval_result.prompt.text,
                        'expected_behavior': eval_result.prompt.expected_behavior,
                        'severity': eval_result.prompt.severity.value,
                        'response_text': eval_result.response.response_text[:200] + "..." if len(eval_result.response.response_text) > 200 else eval_result.response.response_text,
                        'score': score.score,
                        'passed': score.passed,
                        'overall_score': eval_result.overall_score,
                        'overall_passed': eval_result.passed,
                        'response_time': eval_result.response.response_time,
                        'tokens_used': eval_result.response.tokens_used,
                        'flags': ', '.join(eval_result.flags),
                        'date': batch_result.start_time.date() if batch_result.start_time else None
                    })
        
        return pd.DataFrame(detailed_data)
    
    def plot_model_comparison(self, 
                            results: List[BatchEvaluationResult],
                            language: Optional[str] = None,
                            save_path: Optional[Path] = None) -> go.Figure:
        """Create a model comparison plot.
        
        Args:
            results: List of batch results
            language: Optional language filter
            save_path: Optional path to save the plot
            
        Returns:
            Plotly figure
        """
        df = self.create_summary_dataframe(results)
        
        if language:
            df = df[df['language'] == language]
        
        if df.empty:
            logger.warning("No data available for plotting")
            return go.Figure()
        
        # Create subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Mean Score by Category', 'Pass Rate by Category', 
                          'Score Distribution', 'Safety Threshold Compliance'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Mean score by category
        for model in df['model'].unique():
            model_data = df[df['model'] == model]
            fig.add_trace(
                go.Bar(
                    x=model_data['category'],
                    y=model_data['mean_score'],
                    name=f"{model} - Mean Score",
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # Pass rate by category
        for model in df['model'].unique():
            model_data = df[df['model'] == model]
            fig.add_trace(
                go.Bar(
                    x=model_data['category'],
                    y=model_data['pass_rate'],
                    name=f"{model} - Pass Rate",
                    showlegend=True
                ),
                row=1, col=2
            )
        
        # Score distribution
        fig.add_trace(
            go.Box(
                y=df['mean_score'],
                x=df['model'],
                name="Score Distribution",
                showlegend=True
            ),
            row=2, col=1
        )
        
        # Safety threshold compliance
        threshold_compliance = []
        for _, row in df.iterrows():
            threshold = SAFETY_THRESHOLDS.get(row['category'], 0.7)
            compliance = 1 if row['mean_score'] >= threshold else 0
            threshold_compliance.append({
                'model': row['model'],
                'category': row['category'],
                'compliant': compliance
            })
        
        threshold_df = pd.DataFrame(threshold_compliance)
        compliance_summary = threshold_df.groupby('model')['compliant'].mean().reset_index()
        
        fig.add_trace(
            go.Bar(
                x=compliance_summary['model'],
                y=compliance_summary['compliant'],
                name="Threshold Compliance",
                showlegend=True
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text=f"Model Comparison{f' - {language}' if language else ''}",
            showlegend=True,
            height=800
        )
        
        # Save if requested
        if save_path:
            fig.write_html(save_path)
            logger.info(f"Plot saved to {save_path}")
        
        return fig
    
    def plot_language_comparison(self,
                               results: List[BatchEvaluationResult],
                               model: Optional[str] = None,
                               save_path: Optional[Path] = None) -> go.Figure:
        """Create a language comparison plot.
        
        Args:
            results: List of batch results
            model: Optional model filter
            save_path: Optional path to save the plot
            
        Returns:
            Plotly figure
        """
        df = self.create_summary_dataframe(results)
        
        if model:
            df = df[df['model'] == model]
        
        if df.empty:
            logger.warning("No data available for plotting")
            return go.Figure()
        
        # Create heatmap of scores by language and category
        pivot_df = df.pivot_table(
            values='mean_score',
            index='category',
            columns='language',
            aggfunc='mean'
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='RdYlGn',
            colorbar=dict(title="Mean Score"),
            text=np.round(pivot_df.values, 3),
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title=f"Language Performance Heatmap{f' - {model}' if model else ''}",
            xaxis_title="Language",
            yaxis_title="Category",
            height=600
        )
        
        # Save if requested
        if save_path:
            fig.write_html(save_path)
            logger.info(f"Plot saved to {save_path}")
        
        return fig
    
    def plot_category_breakdown(self,
                              results: List[BatchEvaluationResult],
                              save_path: Optional[Path] = None) -> go.Figure:
        """Create a detailed category breakdown plot.
        
        Args:
            results: List of batch results
            save_path: Optional path to save the plot
            
        Returns:
            Plotly figure
        """
        detailed_df = self.create_detailed_dataframe(results)
        
        if detailed_df.empty:
            logger.warning("No data available for plotting")
            return go.Figure()
        
        # Create subplots for each category
        categories = detailed_df['category'].unique()
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[f"{cat.title()} Distribution" for cat in categories[:6]],
            specs=[[{"type": "histogram"} for _ in range(3)] for _ in range(2)]
        )
        
        for i, category in enumerate(categories[:6]):
            row = (i // 3) + 1
            col = (i % 3) + 1
            
            cat_data = detailed_df[detailed_df['category'] == category]
            
            fig.add_trace(
                go.Histogram(
                    x=cat_data['score'],
                    name=f"{category} Scores",
                    nbinsx=20,
                    showlegend=False
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title_text="Score Distributions by Category",
            height=600,
            showlegend=False
        )
        
        # Save if requested
        if save_path:
            fig.write_html(save_path)
            logger.info(f"Plot saved to {save_path}")
        
        return fig
    
    def generate_report(self, 
                       results: List[BatchEvaluationResult],
                       output_dir: Optional[Path] = None) -> Path:
        """Generate a comprehensive HTML report.
        
        Args:
            results: List of batch results
            output_dir: Output directory for the report
            
        Returns:
            Path to the generated report
        """
        if not output_dir:
            output_dir = self.results_dir / "reports"
        output_dir.mkdir(exist_ok=True)
        
        # Generate plots
        model_comparison = self.plot_model_comparison(results)
        language_comparison = self.plot_language_comparison(results)
        category_breakdown = self.plot_category_breakdown(results)
        
        # Create summary statistics
        df = self.create_summary_dataframe(results)
        
        # Generate HTML report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"masb_report_{timestamp}.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MASB Evaluation Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .section {{ margin: 40px 0; }}
                .plot-container {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>MASB Evaluation Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Summary Statistics</h2>
                <p>Total evaluations: {len(results)}</p>
                <p>Models evaluated: {', '.join(df['model'].unique())}</p>
                <p>Languages tested: {', '.join(df['language'].unique())}</p>
                <p>Categories covered: {', '.join(df['category'].unique())}</p>
            </div>
            
            <div class="section">
                <h2>Model Comparison</h2>
                <div class="plot-container" id="model-comparison"></div>
            </div>
            
            <div class="section">
                <h2>Language Comparison</h2>
                <div class="plot-container" id="language-comparison"></div>
            </div>
            
            <div class="section">
                <h2>Category Breakdown</h2>
                <div class="plot-container" id="category-breakdown"></div>
            </div>
            
            <script>
                Plotly.newPlot('model-comparison', {model_comparison.to_json()});
                Plotly.newPlot('language-comparison', {language_comparison.to_json()});
                Plotly.newPlot('category-breakdown', {category_breakdown.to_json()});
            </script>
        </body>
        </html>
        """
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Report generated: {report_path}")
        return report_path
    
    def export_to_csv(self, 
                     results: List[BatchEvaluationResult],
                     output_path: Optional[Path] = None) -> Path:
        """Export results to CSV format.
        
        Args:
            results: List of batch results
            output_path: Output path for CSV file
            
        Returns:
            Path to the CSV file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.results_dir / f"masb_results_{timestamp}.csv"
        
        detailed_df = self.create_detailed_dataframe(results)
        detailed_df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Results exported to CSV: {output_path}")
        return output_path