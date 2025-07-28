"""System health monitoring and alerting for MASB."""

import asyncio
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from enum import Enum

from src.monitoring.performance_monitor import ResourceMonitor, performance_tracker
from src.utils.logger import logger
from src.config import settings


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check definition."""
    name: str
    description: str
    check_function: Callable[[], bool]
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    enabled: bool = True
    check_interval_seconds: int = 60


@dataclass
class Alert:
    """System alert."""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SystemHealthMonitor:
    """Monitors system health and generates alerts."""
    
    def __init__(self, resource_monitor: ResourceMonitor):
        """Initialize system health monitor.
        
        Args:
            resource_monitor: Resource monitor instance
        """
        self.resource_monitor = resource_monitor
        self.health_checks: Dict[str, HealthCheck] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.monitoring = False
        self.monitor_task = None
        
        # Setup default health checks
        self._setup_default_health_checks()
        
        logger.info("SystemHealthMonitor initialized")
    
    def _setup_default_health_checks(self):
        """Setup default system health checks."""
        
        # CPU usage check
        def check_cpu_usage():
            metrics = self.resource_monitor.get_average_metrics(minutes=5)
            cpu_percent = metrics.get('cpu_percent', 0)
            return cpu_percent < 90  # Warning at 80%, critical at 90%
        
        self.add_health_check(HealthCheck(
            name="cpu_usage",
            description="Monitor CPU usage levels",
            check_function=check_cpu_usage,
            threshold_warning=80.0,
            threshold_critical=90.0,
            check_interval_seconds=30
        ))
        
        # Memory usage check
        def check_memory_usage():
            metrics = self.resource_monitor.get_average_metrics(minutes=5)
            memory_percent = metrics.get('memory_percent', 0)
            return memory_percent < 85  # Warning at 80%, critical at 85%
        
        self.add_health_check(HealthCheck(
            name="memory_usage",
            description="Monitor memory usage levels",
            check_function=check_memory_usage,
            threshold_warning=80.0,
            threshold_critical=85.0,
            check_interval_seconds=30
        ))
        
        # Disk usage check
        def check_disk_usage():
            metrics = self.resource_monitor.get_average_metrics(minutes=5)
            disk_percent = metrics.get('disk_usage_percent', 0)
            return disk_percent < 90  # Warning at 80%, critical at 90%
        
        self.add_health_check(HealthCheck(
            name="disk_usage",
            description="Monitor disk usage levels",
            check_function=check_disk_usage,
            threshold_warning=80.0,
            threshold_critical=90.0,
            check_interval_seconds=300  # Check every 5 minutes
        ))
        
        # GPU temperature check (if GPU available)
        if self.resource_monitor.gpu_available:
            def check_gpu_temperature():
                metrics = self.resource_monitor.get_average_metrics(minutes=5)
                gpu_temp = metrics.get('gpu_temperature', 0)
                return gpu_temp < 85  # Warning at 80°C, critical at 85°C
            
            self.add_health_check(HealthCheck(
                name="gpu_temperature",
                description="Monitor GPU temperature",
                check_function=check_gpu_temperature,
                threshold_warning=80.0,
                threshold_critical=85.0,
                check_interval_seconds=60
            ))
        
        # Error rate check
        def check_error_rate():
            summary = performance_tracker.get_performance_summary(hours=1)
            error_rate = summary.get('error_rate', 0)
            return error_rate < 0.1  # Warning at 5%, critical at 10%
        
        self.add_health_check(HealthCheck(
            name="error_rate",
            description="Monitor evaluation error rate",
            check_function=check_error_rate,
            threshold_warning=0.05,
            threshold_critical=0.10,
            check_interval_seconds=300
        ))
        
        # Database connectivity check
        def check_database_connectivity():
            try:
                from src.storage.database import db_manager
                # Simple check - try to get a count of results
                results = db_manager.list_batch_results(limit=1)
                return True
            except Exception as e:
                logger.error(f"Database connectivity check failed: {e}")
                return False
        
        self.add_health_check(HealthCheck(
            name="database_connectivity",
            description="Check database connectivity",
            check_function=check_database_connectivity,
            check_interval_seconds=120
        ))
    
    def add_health_check(self, health_check: HealthCheck):
        """Add a health check.
        
        Args:
            health_check: Health check to add
        """
        self.health_checks[health_check.name] = health_check
        logger.info(f"Added health check: {health_check.name}")
    
    def remove_health_check(self, name: str):
        """Remove a health check.
        
        Args:
            name: Name of health check to remove
        """
        if name in self.health_checks:
            del self.health_checks[name]
            logger.info(f"Removed health check: {name}")
    
    async def start_monitoring(self):
        """Start health monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("System health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System health monitoring stopped")
    
    async def _monitor_loop(self):
        """Main health monitoring loop."""
        last_check_times = {}
        
        while self.monitoring:
            try:
                current_time = datetime.utcnow()
                
                for name, health_check in self.health_checks.items():
                    if not health_check.enabled:
                        continue
                    
                    # Check if it's time to run this health check
                    last_check = last_check_times.get(name, datetime.min)
                    if (current_time - last_check).total_seconds() >= health_check.check_interval_seconds:
                        await self._run_health_check(health_check)
                        last_check_times[name] = current_time
                
                # Sleep for 10 seconds before next loop
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _run_health_check(self, health_check: HealthCheck):
        """Run a single health check.
        
        Args:
            health_check: Health check to run
        """
        try:
            # Run the check function
            result = health_check.check_function()
            
            # Handle the result
            if result:
                # Check passed - resolve any existing alerts
                await self._resolve_alert(health_check.name)
            else:
                # Check failed - generate alert
                await self._generate_alert(health_check)
                
        except Exception as e:
            logger.error(f"Health check '{health_check.name}' failed with exception: {e}")
            await self._generate_alert(
                health_check,
                level=AlertLevel.ERROR,
                message=f"Health check failed with exception: {str(e)}"
            )
    
    async def _generate_alert(self, health_check: HealthCheck, 
                            level: Optional[AlertLevel] = None,
                            message: Optional[str] = None):
        """Generate an alert.
        
        Args:
            health_check: Health check that failed
            level: Alert level (auto-determined if None)
            message: Custom message (auto-generated if None)
        """
        alert_id = f"health_check_{health_check.name}"
        
        # Don't generate duplicate alerts
        if alert_id in self.active_alerts:
            return
        
        # Determine alert level
        if level is None:
            level = AlertLevel.WARNING  # Default level
            
            # Try to get current metric value for threshold comparison
            try:
                if health_check.name in ['cpu_usage', 'memory_usage', 'disk_usage']:
                    metrics = self.resource_monitor.get_average_metrics(minutes=5)
                    metric_key = health_check.name.replace('_usage', '_percent')
                    current_value = metrics.get(metric_key, 0)
                    
                    if health_check.threshold_critical and current_value >= health_check.threshold_critical:
                        level = AlertLevel.CRITICAL
                    elif health_check.threshold_warning and current_value >= health_check.threshold_warning:
                        level = AlertLevel.WARNING
                
                elif health_check.name == 'error_rate':
                    summary = performance_tracker.get_performance_summary(hours=1)
                    error_rate = summary.get('error_rate', 0)
                    
                    if health_check.threshold_critical and error_rate >= health_check.threshold_critical:
                        level = AlertLevel.CRITICAL
                    elif health_check.threshold_warning and error_rate >= health_check.threshold_warning:
                        level = AlertLevel.WARNING
                        
            except Exception as e:
                logger.error(f"Error determining alert level: {e}")
        
        # Generate message
        if message is None:
            message = f"Health check '{health_check.name}' failed: {health_check.description}"
        
        # Create alert
        alert = Alert(
            id=alert_id,
            level=level,
            title=f"System Health Alert: {health_check.name}",
            message=message,
            timestamp=datetime.utcnow(),
            source="health_monitor",
            metadata={
                'health_check': health_check.name,
                'check_description': health_check.description
            }
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Generated {level.value} alert: {alert.title}")
        
        # Send notifications
        await self._send_alert_notifications(alert)
    
    async def _resolve_alert(self, health_check_name: str):
        """Resolve an alert.
        
        Args:
            health_check_name: Name of health check
        """
        alert_id = f"health_check_{health_check_name}"
        
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            del self.active_alerts[alert_id]
            
            logger.info(f"Resolved alert: {alert.title}")
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications.
        
        Args:
            alert: Alert to send notifications for
        """
        # For now, just log the alert
        # In a production system, you might send emails, Slack messages, etc.
        
        logger.warning(f"🚨 ALERT [{alert.level.value.upper()}]: {alert.title}")
        logger.warning(f"   Message: {alert.message}")
        logger.warning(f"   Time: {alert.timestamp}")
        
        # Could add email notifications here
        # await self._send_email_alert(alert)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status.
        
        Returns:
            System status dictionary
        """
        # Run all health checks synchronously for status
        health_status = {}
        for name, health_check in self.health_checks.items():
            if not health_check.enabled:
                continue
                
            try:
                result = health_check.check_function()
                health_status[name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'description': health_check.description,
                    'last_checked': datetime.utcnow().isoformat()
                }
            except Exception as e:
                health_status[name] = {
                    'status': 'error',
                    'description': health_check.description,
                    'error': str(e),
                    'last_checked': datetime.utcnow().isoformat()
                }
        
        # Get current resource metrics
        current_resources = self.resource_monitor.get_current_snapshot()
        
        # Overall system status
        active_critical_alerts = [a for a in self.active_alerts.values() if a.level == AlertLevel.CRITICAL]
        active_warning_alerts = [a for a in self.active_alerts.values() if a.level == AlertLevel.WARNING]
        
        overall_status = "healthy"
        if active_critical_alerts:
            overall_status = "critical"
        elif active_warning_alerts:
            overall_status = "warning"
        elif any(h['status'] == 'unhealthy' for h in health_status.values()):
            overall_status = "degraded"
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'health_checks': health_status,
            'active_alerts': len(self.active_alerts),
            'critical_alerts': len(active_critical_alerts),
            'warning_alerts': len(active_warning_alerts),
            'current_resources': {
                'cpu_percent': current_resources.cpu_percent,
                'memory_percent': current_resources.memory_percent,
                'memory_used_gb': current_resources.memory_used_gb,
                'disk_usage_percent': current_resources.disk_usage_percent,
                'gpu_usage_percent': current_resources.gpu_usage_percent,
                'gpu_temperature': current_resources.gpu_temperature
            },
            'performance_summary': performance_tracker.get_performance_summary(hours=1)
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts.
        
        Returns:
            List of active alerts
        """
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history.
        
        Args:
            hours: Number of hours of history
            
        Returns:
            List of historical alerts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]


# Global health monitor instance
from src.monitoring.performance_monitor import ResourceMonitor
resource_monitor = ResourceMonitor()
health_monitor = SystemHealthMonitor(resource_monitor)