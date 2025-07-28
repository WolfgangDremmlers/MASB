"""Performance monitoring and resource usage statistics for MASB."""

import asyncio
import psutil
import time
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
import GPUtil

from src.utils.logger import logger
from src.config import settings


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    gpu_usage_percent: Optional[float] = None
    gpu_memory_percent: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    gpu_temperature: Optional[float] = None
    network_bytes_sent: Optional[int] = None
    network_bytes_recv: Optional[int] = None
    active_processes: int = 0


@dataclass
class PerformanceMetrics:
    """Performance metrics for evaluation operations."""
    operation_id: str
    operation_type: str  # 'evaluation', 'batch_evaluation', 'dataset_load', etc.
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    prompts_processed: int = 0
    tokens_processed: int = 0
    requests_made: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors_count: int = 0
    memory_peak_mb: Optional[float] = None
    cpu_avg_percent: Optional[float] = None
    throughput_prompts_per_second: Optional[float] = None
    throughput_tokens_per_second: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def finish(self):
        """Mark operation as finished and calculate final metrics."""
        self.end_time = datetime.utcnow()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        if self.duration_seconds > 0:
            self.throughput_prompts_per_second = self.prompts_processed / self.duration_seconds
            if self.tokens_processed > 0:
                self.throughput_tokens_per_second = self.tokens_processed / self.duration_seconds


class ResourceMonitor:
    """Monitors system resource usage."""
    
    def __init__(self, sampling_interval: float = 1.0, max_history: int = 3600):
        """Initialize resource monitor.
        
        Args:
            sampling_interval: Seconds between resource samples
            max_history: Maximum number of samples to keep in memory
        """
        self.sampling_interval = sampling_interval
        self.max_history = max_history
        self.history: deque = deque(maxlen=max_history)
        self.monitoring = False
        self.monitor_thread = None
        self._initial_network_stats = None
        
        # Check GPU availability
        self.gpu_available = self._check_gpu_availability()
        
        logger.info(f"ResourceMonitor initialized - GPU available: {self.gpu_available}")
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU monitoring is available."""
        try:
            gpus = GPUtil.getGPUs()
            return len(gpus) > 0
        except Exception:
            return False
    
    def start_monitoring(self):
        """Start background resource monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self._initial_network_stats = psutil.net_io_counters()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop background resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                snapshot = self._take_snapshot()
                self.history.append(snapshot)
            except Exception as e:
                logger.error(f"Error taking resource snapshot: {e}")
            
            time.sleep(self.sampling_interval)
    
    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a snapshot of current resource usage."""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network (delta from start)
        network = psutil.net_io_counters()
        network_sent = None
        network_recv = None
        if self._initial_network_stats:
            network_sent = network.bytes_sent - self._initial_network_stats.bytes_sent
            network_recv = network.bytes_recv - self._initial_network_stats.bytes_recv
        
        # Process count
        active_processes = len(psutil.pids())
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_available_gb=memory.available / (1024**3),
            disk_usage_percent=disk.percent,
            disk_used_gb=disk.used / (1024**3),
            disk_free_gb=disk.free / (1024**3),
            network_bytes_sent=network_sent,
            network_bytes_recv=network_recv,
            active_processes=active_processes
        )
        
        # GPU metrics if available
        if self.gpu_available:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    snapshot.gpu_usage_percent = gpu.load * 100
                    snapshot.gpu_memory_percent = gpu.memoryUtil * 100
                    snapshot.gpu_memory_used_mb = gpu.memoryUsed
                    snapshot.gpu_temperature = gpu.temperature
            except Exception as e:
                logger.debug(f"GPU monitoring error: {e}")
        
        return snapshot
    
    def get_current_snapshot(self) -> ResourceSnapshot:
        """Get current resource snapshot."""
        return self._take_snapshot()
    
    def get_history(self, minutes: Optional[int] = None) -> List[ResourceSnapshot]:
        """Get resource history.
        
        Args:
            minutes: Number of minutes of history to return (None for all)
            
        Returns:
            List of resource snapshots
        """
        if minutes is None:
            return list(self.history)
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [snapshot for snapshot in self.history if snapshot.timestamp >= cutoff_time]
    
    def get_average_metrics(self, minutes: int = 5) -> Dict[str, float]:
        """Get average resource metrics over specified time period.
        
        Args:
            minutes: Time period in minutes
            
        Returns:
            Dictionary of average metrics
        """
        history = self.get_history(minutes)
        
        if not history:
            return {}
        
        metrics = {
            'cpu_percent': sum(s.cpu_percent for s in history) / len(history),
            'memory_percent': sum(s.memory_percent for s in history) / len(history),
            'memory_used_gb': sum(s.memory_used_gb for s in history) / len(history),
            'disk_usage_percent': sum(s.disk_usage_percent for s in history) / len(history),
        }
        
        # GPU metrics if available
        gpu_snapshots = [s for s in history if s.gpu_usage_percent is not None]
        if gpu_snapshots:
            metrics['gpu_usage_percent'] = sum(s.gpu_usage_percent for s in gpu_snapshots) / len(gpu_snapshots)
            metrics['gpu_memory_percent'] = sum(s.gpu_memory_percent for s in gpu_snapshots) / len(gpu_snapshots)
            metrics['gpu_temperature'] = sum(s.gpu_temperature for s in gpu_snapshots) / len(gpu_snapshots)
        
        return metrics


class PerformanceTracker:
    """Tracks performance metrics for evaluation operations."""
    
    def __init__(self):
        """Initialize performance tracker."""
        self.active_operations: Dict[str, PerformanceMetrics] = {}
        self.completed_operations: deque = deque(maxlen=1000)  # Keep last 1000 operations
        self.resource_monitor = ResourceMonitor()
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        logger.info("PerformanceTracker initialized")
    
    def start_operation(self, operation_id: str, operation_type: str, **metadata) -> PerformanceMetrics:
        """Start tracking a new operation.
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation
            **metadata: Additional metadata to track
            
        Returns:
            Performance metrics object
        """
        metrics = PerformanceMetrics(
            operation_id=operation_id,
            operation_type=operation_type,
            start_time=datetime.utcnow(),
            metadata=metadata
        )
        
        self.active_operations[operation_id] = metrics
        logger.debug(f"Started tracking operation: {operation_id} ({operation_type})")
        
        return metrics
    
    def finish_operation(self, operation_id: str) -> Optional[PerformanceMetrics]:
        """Finish tracking an operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Completed performance metrics
        """
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found in active operations")
            return None
        
        metrics = self.active_operations.pop(operation_id)
        metrics.finish()
        
        # Calculate resource metrics during operation
        if metrics.duration_seconds and metrics.duration_seconds > 0:
            operation_history = self.resource_monitor.get_history(
                minutes=max(1, int(metrics.duration_seconds / 60) + 1)
            )
            
            if operation_history:
                # Filter to operation timeframe
                operation_snapshots = [
                    s for s in operation_history 
                    if metrics.start_time <= s.timestamp <= metrics.end_time
                ]
                
                if operation_snapshots:
                    metrics.cpu_avg_percent = sum(s.cpu_percent for s in operation_snapshots) / len(operation_snapshots)
                    metrics.memory_peak_mb = max(s.memory_used_gb * 1024 for s in operation_snapshots)
        
        self.completed_operations.append(metrics)
        logger.debug(f"Finished tracking operation: {operation_id} (duration: {metrics.duration_seconds:.2f}s)")
        
        return metrics
    
    def update_operation(self, operation_id: str, **kwargs):
        """Update metrics for an active operation.
        
        Args:
            operation_id: Operation identifier
            **kwargs: Metrics to update
        """
        if operation_id not in self.active_operations:
            return
        
        metrics = self.active_operations[operation_id]
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
    
    def get_operation_metrics(self, operation_id: str) -> Optional[PerformanceMetrics]:
        """Get metrics for an operation (active or completed).
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Performance metrics or None if not found
        """
        # Check active operations first
        if operation_id in self.active_operations:
            return self.active_operations[operation_id]
        
        # Check completed operations
        for metrics in self.completed_operations:
            if metrics.operation_id == operation_id:
                return metrics
        
        return None
    
    def get_recent_operations(self, operation_type: Optional[str] = None, 
                            hours: int = 24) -> List[PerformanceMetrics]:
        """Get recent operations.
        
        Args:
            operation_type: Filter by operation type
            hours: Number of hours of history
            
        Returns:
            List of performance metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        operations = [
            metrics for metrics in self.completed_operations
            if metrics.start_time >= cutoff_time
        ]
        
        if operation_type:
            operations = [op for op in operations if op.operation_type == operation_type]
        
        return sorted(operations, key=lambda x: x.start_time, reverse=True)
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary statistics.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance summary dictionary
        """
        recent_ops = self.get_recent_operations(hours=hours)
        
        if not recent_ops:
            return {'message': 'No operations in specified time period'}
        
        # Calculate summary statistics
        total_operations = len(recent_ops)
        total_prompts = sum(op.prompts_processed for op in recent_ops)
        total_tokens = sum(op.tokens_processed for op in recent_ops)
        total_requests = sum(op.requests_made for op in recent_ops)
        total_errors = sum(op.errors_count for op in recent_ops)
        
        # Average metrics
        avg_duration = sum(op.duration_seconds or 0 for op in recent_ops) / total_operations
        avg_throughput_prompts = sum(op.throughput_prompts_per_second or 0 for op in recent_ops) / total_operations
        avg_throughput_tokens = sum(op.throughput_tokens_per_second or 0 for op in recent_ops) / total_operations
        
        # Cache statistics
        total_cache_hits = sum(op.cache_hits for op in recent_ops)
        total_cache_misses = sum(op.cache_misses for op in recent_ops)
        cache_hit_rate = total_cache_hits / max(1, total_cache_hits + total_cache_misses)
        
        # Error rate
        error_rate = total_errors / max(1, total_requests)
        
        # Group by operation type
        by_type = {}
        for op in recent_ops:
            if op.operation_type not in by_type:
                by_type[op.operation_type] = []
            by_type[op.operation_type].append(op)
        
        type_stats = {}
        for op_type, ops in by_type.items():
            type_stats[op_type] = {
                'count': len(ops),
                'total_prompts': sum(op.prompts_processed for op in ops),
                'avg_duration': sum(op.duration_seconds or 0 for op in ops) / len(ops),
                'avg_throughput': sum(op.throughput_prompts_per_second or 0 for op in ops) / len(ops)
            }
        
        return {
            'time_period_hours': hours,
            'total_operations': total_operations,
            'total_prompts_processed': total_prompts,
            'total_tokens_processed': total_tokens,
            'total_requests_made': total_requests,
            'total_errors': total_errors,
            'average_duration_seconds': avg_duration,
            'average_throughput_prompts_per_second': avg_throughput_prompts,
            'average_throughput_tokens_per_second': avg_throughput_tokens,
            'cache_hit_rate': cache_hit_rate,
            'error_rate': error_rate,
            'by_operation_type': type_stats,
            'resource_averages': self.resource_monitor.get_average_metrics(minutes=hours*60)
        }


class PerformanceReporter:
    """Generates performance reports and saves metrics to files."""
    
    def __init__(self, performance_tracker: PerformanceTracker):
        """Initialize performance reporter.
        
        Args:
            performance_tracker: Performance tracker instance
        """
        self.tracker = performance_tracker
        self.reports_dir = settings.logs_dir / "performance"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("PerformanceReporter initialized")
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate daily performance report.
        
        Args:
            date: Date to generate report for (default: today)
            
        Returns:
            Daily performance report
        """
        if date is None:
            date = datetime.utcnow()
        
        # Get operations for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        day_operations = [
            op for op in self.tracker.completed_operations
            if start_of_day <= op.start_time < end_of_day
        ]
        
        if not day_operations:
            return {
                'date': date.date().isoformat(),
                'message': 'No operations found for this date'
            }
        
        # Calculate daily statistics
        total_operations = len(day_operations)
        total_duration = sum(op.duration_seconds or 0 for op in day_operations)
        total_prompts = sum(op.prompts_processed for op in day_operations)
        total_errors = sum(op.errors_count for op in day_operations)
        
        # Hourly breakdown
        hourly_stats = {}
        for hour in range(24):
            hour_start = start_of_day + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_ops = [
                op for op in day_operations
                if hour_start <= op.start_time < hour_end
            ]
            
            if hour_ops:
                hourly_stats[f"{hour:02d}:00"] = {
                    'operations': len(hour_ops),
                    'prompts': sum(op.prompts_processed for op in hour_ops),
                    'avg_duration': sum(op.duration_seconds or 0 for op in hour_ops) / len(hour_ops),
                    'errors': sum(op.errors_count for op in hour_ops)
                }
        
        # Performance peaks
        peak_throughput_op = max(day_operations, key=lambda x: x.throughput_prompts_per_second or 0)
        longest_operation = max(day_operations, key=lambda x: x.duration_seconds or 0)
        
        report = {
            'date': date.date().isoformat(),
            'summary': {
                'total_operations': total_operations,
                'total_duration_hours': total_duration / 3600,
                'total_prompts_processed': total_prompts,
                'total_errors': total_errors,
                'average_prompts_per_operation': total_prompts / total_operations,
                'error_rate': total_errors / max(1, sum(op.requests_made for op in day_operations))
            },
            'hourly_breakdown': hourly_stats,
            'performance_peaks': {
                'highest_throughput': {
                    'operation_id': peak_throughput_op.operation_id,
                    'throughput': peak_throughput_op.throughput_prompts_per_second,
                    'operation_type': peak_throughput_op.operation_type
                },
                'longest_operation': {
                    'operation_id': longest_operation.operation_id,
                    'duration_seconds': longest_operation.duration_seconds,
                    'operation_type': longest_operation.operation_type
                }
            }
        }
        
        return report
    
    def save_daily_report(self, date: Optional[datetime] = None):
        """Save daily report to file.
        
        Args:
            date: Date to generate report for
        """
        if date is None:
            date = datetime.utcnow()
        
        report = self.generate_daily_report(date)
        
        filename = f"daily_report_{date.date().isoformat()}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Daily performance report saved: {filepath}")
    
    def export_metrics_csv(self, hours: int = 24, filepath: Optional[Path] = None) -> Path:
        """Export performance metrics to CSV.
        
        Args:
            hours: Number of hours of data to export
            filepath: Output file path (optional)
            
        Returns:
            Path to exported CSV file
        """
        import csv
        
        if filepath is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filepath = self.reports_dir / f"performance_metrics_{timestamp}.csv"
        
        operations = self.tracker.get_recent_operations(hours=hours)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not operations:
                f.write("No data available\n")
                return filepath
            
            writer = csv.DictWriter(f, fieldnames=[
                'operation_id', 'operation_type', 'start_time', 'duration_seconds',
                'prompts_processed', 'tokens_processed', 'requests_made',
                'cache_hits', 'cache_misses', 'errors_count',
                'throughput_prompts_per_second', 'throughput_tokens_per_second',
                'cpu_avg_percent', 'memory_peak_mb'
            ])
            
            writer.writeheader()
            for op in operations:
                row = asdict(op)
                # Convert datetime to string
                row['start_time'] = op.start_time.isoformat()
                # Remove complex fields
                row.pop('end_time', None)
                row.pop('metadata', None)
                writer.writerow(row)
        
        logger.info(f"Performance metrics exported to CSV: {filepath}")
        return filepath


# Global performance tracker instance
performance_tracker = PerformanceTracker()
performance_reporter = PerformanceReporter(performance_tracker)