"""Advanced evaluation metrics and statistical analysis for MASB."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.models.data_models import (
    EvaluationResult, BatchEvaluationResult, Category, Language, Severity
)
from src.utils.logger import logger


@dataclass
class StatisticalSummary:
    """Statistical summary for evaluation metrics."""
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float
    skewness: float
    kurtosis: float
    confidence_interval_95: Tuple[float, float]


@dataclass
class ModelComparison:
    """Statistical comparison between models."""
    model_a: str
    model_b: str
    category: str
    p_value: float
    statistic: float
    effect_size: float
    significant: bool
    interpretation: str


@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    category: str
    trend_slope: float
    trend_r_squared: float
    trend_p_value: float
    trend_direction: str  # 'improving', 'declining', 'stable'
    forecasted_scores: List[float]


class AdvancedMetrics:
    """Advanced evaluation metrics calculator."""
    
    def __init__(self):
        """Initialize advanced metrics calculator."""
        self.significance_level = 0.05
        
    def calculate_statistical_summary(self, scores: List[float]) -> StatisticalSummary:
        """Calculate comprehensive statistical summary.
        
        Args:
            scores: List of scores to analyze
            
        Returns:
            Statistical summary
        """
        if not scores:
            return StatisticalSummary(0, 0, 0, 0, 0, 0, 0, 0, 0, (0, 0))
        
        scores_array = np.array(scores)
        
        # Basic statistics
        mean = float(np.mean(scores_array))
        median = float(np.median(scores_array))
        std = float(np.std(scores_array, ddof=1)) if len(scores) > 1 else 0
        min_val = float(np.min(scores_array))
        max_val = float(np.max(scores_array))
        q25 = float(np.percentile(scores_array, 25))
        q75 = float(np.percentile(scores_array, 75))
        
        # Advanced statistics
        skewness = float(stats.skew(scores_array)) if len(scores) > 2 else 0
        kurtosis = float(stats.kurtosis(scores_array)) if len(scores) > 3 else 0
        
        # Confidence interval
        if len(scores) > 1:
            confidence_interval = stats.t.interval(
                0.95, len(scores) - 1, loc=mean, scale=stats.sem(scores_array)
            )
        else:
            confidence_interval = (mean, mean)
        
        return StatisticalSummary(
            mean=mean,
            median=median,
            std=std,
            min=min_val,
            max=max_val,
            q25=q25,
            q75=q75,
            skewness=skewness,
            kurtosis=kurtosis,
            confidence_interval_95=confidence_interval
        )
    
    def compare_models(self, 
                      results_a: List[EvaluationResult],
                      results_b: List[EvaluationResult],
                      model_a_name: str,
                      model_b_name: str) -> List[ModelComparison]:
        """Compare two models statistically.
        
        Args:
            results_a: Results from model A
            results_b: Results from model B
            model_a_name: Name of model A
            model_b_name: Name of model B
            
        Returns:
            List of model comparisons by category
        """
        comparisons = []
        
        # Group results by category
        scores_a_by_category = {}
        scores_b_by_category = {}
        
        for result in results_a:
            for score in result.scores:
                category = score.category.value
                if category not in scores_a_by_category:
                    scores_a_by_category[category] = []
                scores_a_by_category[category].append(score.score)
        
        for result in results_b:
            for score in result.scores:
                category = score.category.value
                if category not in scores_b_by_category:
                    scores_b_by_category[category] = []
                scores_b_by_category[category].append(score.score)
        
        # Compare each category
        for category in set(scores_a_by_category.keys()) & set(scores_b_by_category.keys()):
            scores_a = scores_a_by_category[category]
            scores_b = scores_b_by_category[category]
            
            if len(scores_a) < 3 or len(scores_b) < 3:
                continue
            
            # Perform statistical tests
            # Mann-Whitney U test (non-parametric)
            statistic, p_value = stats.mannwhitneyu(scores_a, scores_b, alternative='two-sided')
            
            # Calculate effect size (Cohen's d)
            effect_size = self._calculate_cohens_d(scores_a, scores_b)
            
            # Determine significance
            significant = p_value < self.significance_level
            
            # Interpretation
            interpretation = self._interpret_comparison(
                np.mean(scores_a), np.mean(scores_b), p_value, effect_size
            )
            
            comparisons.append(ModelComparison(
                model_a=model_a_name,
                model_b=model_b_name,
                category=category,
                p_value=p_value,
                statistic=statistic,
                effect_size=effect_size,
                significant=significant,
                interpretation=interpretation
            ))
        
        return comparisons
    
    def analyze_trends(self, 
                      results: List[BatchEvaluationResult],
                      time_window_days: int = 30) -> List[TrendAnalysis]:
        """Analyze performance trends over time.
        
        Args:
            results: List of batch results
            time_window_days: Time window for trend analysis
            
        Returns:
            List of trend analyses by category
        """
        if len(results) < 3:
            return []
        
        # Sort by date
        results_sorted = sorted(results, key=lambda x: x.start_time)
        
        # Filter to time window
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        results_filtered = [r for r in results_sorted if r.start_time >= cutoff_date]
        
        if len(results_filtered) < 3:
            results_filtered = results_sorted[-10:]  # Use last 10 if not enough recent data
        
        trends = []
        
        # Analyze trends by category
        categories = set()
        for result in results_filtered:
            categories.update(result.summary.keys())
        
        for category in categories:
            # Extract scores and dates
            scores = []
            dates = []
            
            for result in results_filtered:
                if category in result.summary:
                    scores.append(result.summary[category]['mean'])
                    dates.append(result.start_time.timestamp())
            
            if len(scores) < 3:
                continue
            
            # Perform linear regression
            dates_array = np.array(dates)
            scores_array = np.array(scores)
            
            # Normalize dates to days from first measurement
            dates_normalized = (dates_array - dates_array[0]) / (24 * 3600)
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                dates_normalized, scores_array
            )
            
            # Determine trend direction
            if p_value < 0.05:
                if slope > 0.001:  # Meaningful positive slope
                    direction = 'improving'
                elif slope < -0.001:  # Meaningful negative slope
                    direction = 'declining'
                else:
                    direction = 'stable'
            else:
                direction = 'stable'
            
            # Forecast next few points
            last_date = dates_normalized[-1]
            forecast_points = 5
            forecast_dates = np.linspace(last_date + 1, last_date + forecast_points, forecast_points)
            forecasted_scores = [float(slope * date + intercept) for date in forecast_dates]
            
            trends.append(TrendAnalysis(
                category=category.value if hasattr(category, 'value') else str(category),
                trend_slope=slope,
                trend_r_squared=r_value ** 2,
                trend_p_value=p_value,
                trend_direction=direction,
                forecasted_scores=forecasted_scores
            ))
        
        return trends
    
    def calculate_reliability_metrics(self, 
                                    results: List[EvaluationResult]) -> Dict[str, float]:
        """Calculate reliability and consistency metrics.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Dictionary of reliability metrics
        """
        if not results:
            return {}
        
        # Group by category
        scores_by_category = {}
        for result in results:
            for score in result.scores:
                category = score.category.value
                if category not in scores_by_category:
                    scores_by_category[category] = []
                scores_by_category[category].append(score.score)
        
        reliability_metrics = {}
        
        for category, scores in scores_by_category.items():
            if len(scores) < 2:
                continue
            
            scores_array = np.array(scores)
            
            # Coefficient of variation (relative variability)
            cv = np.std(scores_array) / np.mean(scores_array) if np.mean(scores_array) > 0 else 0
            
            # Consistency score (1 - CV, bounded between 0 and 1)
            consistency = max(0, min(1, 1 - cv))
            
            # Stability (proportion of scores within 1 std of mean)
            mean_score = np.mean(scores_array)
            std_score = np.std(scores_array)
            within_std = np.sum(np.abs(scores_array - mean_score) <= std_score)
            stability = within_std / len(scores_array)
            
            reliability_metrics[f"{category}_consistency"] = consistency
            reliability_metrics[f"{category}_stability"] = stability
            reliability_metrics[f"{category}_coefficient_of_variation"] = cv
        
        return reliability_metrics
    
    def detect_anomalies(self, 
                        results: List[EvaluationResult],
                        method: str = 'iqr') -> List[Dict[str, Any]]:
        """Detect anomalous evaluation results.
        
        Args:
            results: List of evaluation results
            method: Anomaly detection method ('iqr', 'zscore', 'isolation')
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Group by category
        data_by_category = {}
        for result in results:
            for score in result.scores:
                category = score.category.value
                if category not in data_by_category:
                    data_by_category[category] = []
                data_by_category[category].append({
                    'score': score.score,
                    'result_id': result.id,
                    'prompt_id': result.prompt.id,
                    'model': result.response.model_name
                })
        
        for category, data in data_by_category.items():
            if len(data) < 10:  # Need enough data for anomaly detection
                continue
            
            scores = [d['score'] for d in data]
            scores_array = np.array(scores)
            
            if method == 'iqr':
                # Interquartile Range method
                Q1 = np.percentile(scores_array, 25)
                Q3 = np.percentile(scores_array, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                for i, d in enumerate(data):
                    score = d['score']
                    if score < lower_bound or score > upper_bound:
                        anomalies.append({
                            'type': 'outlier',
                            'category': category,
                            'score': score,
                            'expected_range': (lower_bound, upper_bound),
                            'result_id': d['result_id'],
                            'prompt_id': d['prompt_id'],
                            'model': d['model'],
                            'severity': 'high' if score < lower_bound - IQR or score > upper_bound + IQR else 'medium'
                        })
            
            elif method == 'zscore':
                # Z-score method
                mean_score = np.mean(scores_array)
                std_score = np.std(scores_array)
                
                for i, d in enumerate(data):
                    score = d['score']
                    z_score = abs((score - mean_score) / std_score) if std_score > 0 else 0
                    
                    if z_score > 2.5:  # More than 2.5 standard deviations
                        anomalies.append({
                            'type': 'statistical_outlier',
                            'category': category,
                            'score': score,
                            'z_score': z_score,
                            'result_id': d['result_id'],
                            'prompt_id': d['prompt_id'],
                            'model': d['model'],
                            'severity': 'high' if z_score > 3 else 'medium'
                        })
        
        return anomalies
    
    def _calculate_cohens_d(self, scores_a: List[float], scores_b: List[float]) -> float:
        """Calculate Cohen's d effect size."""
        mean_a = np.mean(scores_a)
        mean_b = np.mean(scores_b)
        
        # Pooled standard deviation
        n_a, n_b = len(scores_a), len(scores_b)
        var_a = np.var(scores_a, ddof=1) if n_a > 1 else 0
        var_b = np.var(scores_b, ddof=1) if n_b > 1 else 0
        
        pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
        
        if pooled_std == 0:
            return 0
        
        return (mean_a - mean_b) / pooled_std
    
    def _interpret_comparison(self, 
                            mean_a: float, 
                            mean_b: float, 
                            p_value: float, 
                            effect_size: float) -> str:
        """Interpret statistical comparison results."""
        diff = mean_a - mean_b
        
        if p_value >= self.significance_level:
            return "No significant difference detected"
        
        # Determine direction
        better_model = "Model A" if diff > 0 else "Model B"
        
        # Interpret effect size
        if abs(effect_size) < 0.2:
            magnitude = "negligible"
        elif abs(effect_size) < 0.5:
            magnitude = "small"
        elif abs(effect_size) < 0.8:
            magnitude = "medium"
        else:
            magnitude = "large"
        
        return f"{better_model} performs significantly better with {magnitude} effect size (p={p_value:.4f})"


class MetricsReporter:
    """Generate comprehensive metrics reports."""
    
    def __init__(self):
        """Initialize metrics reporter."""
        self.metrics_calculator = AdvancedMetrics()
    
    def generate_comprehensive_report(self, 
                                    results: List[BatchEvaluationResult]) -> Dict[str, Any]:
        """Generate comprehensive metrics report.
        
        Args:
            results: List of batch evaluation results
            
        Returns:
            Comprehensive report dictionary
        """
        if not results:
            return {"error": "No results provided"}
        
        # Flatten results
        all_evaluation_results = []
        for batch in results:
            all_evaluation_results.extend(batch.results)
        
        report = {
            "summary": {
                "total_evaluations": len(results),
                "total_prompts": sum(r.total_prompts for r in results),
                "date_range": {
                    "start": min(r.start_time for r in results).isoformat(),
                    "end": max(r.start_time for r in results).isoformat()
                },
                "models_evaluated": list(set(r.model_name for r in results)),
                "languages_tested": list(set(r.language.value for r in results))
            },
            "statistical_analysis": {},
            "model_comparisons": [],
            "trend_analysis": [],
            "reliability_metrics": {},
            "anomaly_detection": [],
            "recommendations": []
        }
        
        # Statistical analysis by category
        scores_by_category = {}
        for result in all_evaluation_results:
            for score in result.scores:
                category = score.category.value
                if category not in scores_by_category:
                    scores_by_category[category] = []
                scores_by_category[category].append(score.score)
        
        for category, scores in scores_by_category.items():
            summary = self.metrics_calculator.calculate_statistical_summary(scores)
            report["statistical_analysis"][category] = {
                "mean": summary.mean,
                "median": summary.median,
                "std": summary.std,
                "min": summary.min,
                "max": summary.max,
                "quartiles": {"q25": summary.q25, "q75": summary.q75},
                "skewness": summary.skewness,
                "kurtosis": summary.kurtosis,
                "confidence_interval_95": summary.confidence_interval_95
            }
        
        # Model comparisons (if multiple models)
        models = list(set(r.model_name for r in results))
        if len(models) >= 2:
            for i in range(len(models)):
                for j in range(i + 1, len(models)):
                    model_a_results = [r for batch in results if batch.model_name == models[i] for r in batch.results]
                    model_b_results = [r for batch in results if batch.model_name == models[j] for r in batch.results]
                    
                    comparisons = self.metrics_calculator.compare_models(
                        model_a_results, model_b_results, models[i], models[j]
                    )
                    
                    for comp in comparisons:
                        report["model_comparisons"].append({
                            "model_a": comp.model_a,
                            "model_b": comp.model_b,
                            "category": comp.category,
                            "p_value": comp.p_value,
                            "effect_size": comp.effect_size,
                            "significant": comp.significant,
                            "interpretation": comp.interpretation
                        })
        
        # Trend analysis
        trends = self.metrics_calculator.analyze_trends(results)
        for trend in trends:
            report["trend_analysis"].append({
                "category": trend.category,
                "slope": trend.trend_slope,
                "r_squared": trend.trend_r_squared,
                "p_value": trend.trend_p_value,
                "direction": trend.trend_direction,
                "forecasted_scores": trend.forecasted_scores
            })
        
        # Reliability metrics
        report["reliability_metrics"] = self.metrics_calculator.calculate_reliability_metrics(
            all_evaluation_results
        )
        
        # Anomaly detection
        anomalies = self.metrics_calculator.detect_anomalies(all_evaluation_results)
        report["anomaly_detection"] = anomalies
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        logger.info(f"Generated comprehensive report for {len(results)} evaluations")
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Check for low-performing categories
        for category, stats in report["statistical_analysis"].items():
            if stats["mean"] < 0.7:
                recommendations.append(
                    f"Category '{category}' shows low performance (mean: {stats['mean']:.2f}). "
                    f"Consider additional training or evaluation refinement."
                )
        
        # Check for high variability
        for category, stats in report["statistical_analysis"].items():
            if stats["std"] > 0.2:
                recommendations.append(
                    f"Category '{category}' shows high variability (std: {stats['std']:.2f}). "
                    f"Results may be inconsistent - consider more evaluation data."
                )
        
        # Check trends
        for trend in report["trend_analysis"]:
            if trend["direction"] == "declining" and trend["p_value"] < 0.05:
                recommendations.append(
                    f"Performance in '{trend['category']}' is declining over time. "
                    f"Investigate potential causes and consider intervention."
                )
        
        # Check anomalies
        if len(report["anomaly_detection"]) > len(report["statistical_analysis"]) * 0.1:
            recommendations.append(
                f"High number of anomalies detected ({len(report['anomaly_detection'])}). "
                f"Review evaluation process for consistency issues."
            )
        
        return recommendations