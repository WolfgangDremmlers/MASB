#!/usr/bin/env python3
"""CLI tool for monitoring MASB system performance and health."""

import argparse
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.monitoring.performance_monitor import performance_tracker, performance_reporter
from src.monitoring.health_monitor import health_monitor
from src.utils.logger import logger


def show_system_status():
    """Show current system status."""
    print("\n🖥️  MASB System Status")
    print("=" * 60)
    
    try:
        status = health_monitor.get_system_status()
        
        # Overall status with color coding
        status_icons = {
            'healthy': '🟢',
            'warning': '🟡',
            'degraded': '🟠',
            'critical': '🔴'
        }
        
        overall_status = status['overall_status']
        status_icon = status_icons.get(overall_status, '⚪')
        
        print(f"Overall Status: {status_icon} {overall_status.upper()}")
        print(f"Last Updated: {status['timestamp']}")
        print(f"Active Alerts: {status['active_alerts']} ({status['critical_alerts']} critical, {status['warning_alerts']} warnings)")
        
        # Resource usage
        print(f"\n📊 Current Resource Usage:")
        resources = status['current_resources']
        print(f"  CPU Usage: {resources['cpu_percent']:.1f}%")
        print(f"  Memory Usage: {resources['memory_percent']:.1f}% ({resources['memory_used_gb']:.1f} GB)")
        print(f"  Disk Usage: {resources['disk_usage_percent']:.1f}%")
        
        if resources['gpu_usage_percent'] is not None:
            print(f"  GPU Usage: {resources['gpu_usage_percent']:.1f}%")
            print(f"  GPU Temperature: {resources['gpu_temperature']:.1f}°C")
        
        # Health checks
        print(f"\n🏥 Health Checks:")
        health_checks = status['health_checks']
        for name, check in health_checks.items():
            status_icon = '✅' if check['status'] == 'healthy' else ('❌' if check['status'] == 'unhealthy' else '⚠️')
            print(f"  {status_icon} {name}: {check['status']} - {check['description']}")
            if 'error' in check:
                print(f"    Error: {check['error']}")
        
        # Performance summary
        print(f"\n⚡ Performance Summary (last 24h):")
        perf = status['performance_summary']
        if 'total_operations' in perf:
            print(f"  Total Operations: {perf['total_operations']}")
            print(f"  Prompts Processed: {perf['total_prompts_processed']}")
            print(f"  Average Throughput: {perf['average_throughput_prompts_per_second']:.2f} prompts/sec")
            print(f"  Error Rate: {perf['error_rate']:.1%}")
            print(f"  Cache Hit Rate: {perf['cache_hit_rate']:.1%}")
        else:
            print(f"  {perf.get('message', 'No recent operations')}")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        print(f"❌ Error getting system status: {e}")


def show_performance_metrics(hours: int = 24, operation_type: str = None):
    """Show performance metrics."""
    print(f"\n⚡ Performance Metrics (last {hours}h)")
    if operation_type:
        print(f"   Filtered by operation type: {operation_type}")
    print("=" * 60)
    
    try:
        # Get recent operations
        if operation_type:
            operations = performance_tracker.get_recent_operations(
                operation_type=operation_type, hours=hours
            )
        else:
            operations = performance_tracker.get_recent_operations(hours=hours)
        
        if not operations:
            print("No operations found in the specified time period.")
            return
        
        # Summary statistics
        summary = performance_tracker.get_performance_summary(hours=hours)
        
        print(f"📈 Summary Statistics:")
        print(f"  Total Operations: {summary['total_operations']}")
        print(f"  Total Prompts: {summary['total_prompts_processed']}")
        print(f"  Total Tokens: {summary['total_tokens_processed']}")
        print(f"  Average Duration: {summary['average_duration_seconds']:.2f} seconds")
        print(f"  Average Throughput: {summary['average_throughput_prompts_per_second']:.2f} prompts/sec")
        print(f"  Error Rate: {summary['error_rate']:.1%}")
        print(f"  Cache Hit Rate: {summary['cache_hit_rate']:.1%}")
        
        # By operation type
        if summary['by_operation_type']:
            print(f"\n📊 By Operation Type:")
            for op_type, stats in summary['by_operation_type'].items():
                print(f"  {op_type}:")
                print(f"    Count: {stats['count']}")
                print(f"    Total Prompts: {stats['total_prompts']}")
                print(f"    Avg Duration: {stats['avg_duration']:.2f}s")
                print(f"    Avg Throughput: {stats['avg_throughput']:.2f} prompts/sec")
        
        # Recent operations
        print(f"\n📋 Recent Operations (last 10):")
        print(f"{'Operation ID':<30} {'Type':<20} {'Duration':<10} {'Prompts':<8} {'Errors':<6}")
        print("-" * 80)
        
        for op in operations[:10]:
            duration = f"{op.duration_seconds:.2f}s" if op.duration_seconds else "N/A"
            print(f"{op.operation_id[:29]:<30} {op.operation_type:<20} {duration:<10} {op.prompts_processed:<8} {op.errors_count:<6}")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        print(f"❌ Error getting performance metrics: {e}")


def show_resource_usage(minutes: int = 60):
    """Show resource usage history."""
    print(f"\n💾 Resource Usage (last {minutes} minutes)")
    print("=" * 60)
    
    try:
        # Get current snapshot
        current = health_monitor.resource_monitor.get_current_snapshot()
        
        print(f"🔄 Current Usage:")
        print(f"  CPU: {current.cpu_percent:.1f}%")
        print(f"  Memory: {current.memory_percent:.1f}% ({current.memory_used_gb:.1f}/{current.memory_used_gb + current.memory_available_gb:.1f} GB)")
        print(f"  Disk: {current.disk_usage_percent:.1f}%")
        print(f"  Processes: {current.active_processes}")
        
        if current.gpu_usage_percent is not None:
            print(f"  GPU Usage: {current.gpu_usage_percent:.1f}%")
            print(f"  GPU Memory: {current.gpu_memory_percent:.1f}%")
            print(f"  GPU Temperature: {current.gpu_temperature:.1f}°C")
        
        # Get averages
        averages = health_monitor.resource_monitor.get_average_metrics(minutes=minutes)
        
        if averages:
            print(f"\n📊 Averages (last {minutes} minutes):")
            print(f"  CPU: {averages.get('cpu_percent', 0):.1f}%")
            print(f"  Memory: {averages.get('memory_percent', 0):.1f}%")
            print(f"  Disk: {averages.get('disk_usage_percent', 0):.1f}%")
            
            if 'gpu_usage_percent' in averages:
                print(f"  GPU Usage: {averages['gpu_usage_percent']:.1f}%")
                print(f"  GPU Memory: {averages['gpu_memory_percent']:.1f}%")
                print(f"  GPU Temperature: {averages['gpu_temperature']:.1f}°C")
        
        # Get history for trends
        history = health_monitor.resource_monitor.get_history(minutes=minutes)
        
        if len(history) > 10:
            print(f"\n📈 Trends:")
            recent_avg = sum(s.cpu_percent for s in history[-10:]) / 10
            older_avg = sum(s.cpu_percent for s in history[:10]) / 10
            cpu_trend = "↗️" if recent_avg > older_avg + 5 else ("↘️" if recent_avg < older_avg - 5 else "➡️")
            print(f"  CPU Trend: {cpu_trend} ({recent_avg:.1f}% vs {older_avg:.1f}%)")
            
            recent_mem = sum(s.memory_percent for s in history[-10:]) / 10
            older_mem = sum(s.memory_percent for s in history[:10]) / 10
            mem_trend = "↗️" if recent_mem > older_mem + 5 else ("↘️" if recent_mem < older_mem - 5 else "➡️")
            print(f"  Memory Trend: {mem_trend} ({recent_mem:.1f}% vs {older_mem:.1f}%)")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to get resource usage: {e}")
        print(f"❌ Error getting resource usage: {e}")


def show_alerts(hours: int = 24):
    """Show system alerts."""
    print(f"\n🚨 System Alerts (last {hours}h)")
    print("=" * 60)
    
    try:
        active_alerts = health_monitor.get_active_alerts()
        alert_history = health_monitor.get_alert_history(hours=hours)
        
        # Active alerts
        if active_alerts:
            print(f"🔴 Active Alerts ({len(active_alerts)}):")
            for alert in active_alerts:
                level_icons = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'error': '❌',
                    'critical': '🔥'
                }
                icon = level_icons.get(alert.level.value, '❓')
                print(f"  {icon} [{alert.level.value.upper()}] {alert.title}")
                print(f"    {alert.message}")
                print(f"    Time: {alert.timestamp}")
                print()
        else:
            print("✅ No active alerts")
        
        # Recent alert history
        if alert_history:
            print(f"\n📋 Recent Alert History ({len(alert_history)} alerts):")
            print(f"{'Level':<10} {'Title':<30} {'Time':<20} {'Status':<10}")
            print("-" * 80)
            
            for alert in alert_history[-10:]:  # Show last 10
                status = "✅ Resolved" if alert.resolved else "🔄 Active"
                print(f"{alert.level.value:<10} {alert.title[:29]:<30} {alert.timestamp.strftime('%Y-%m-%d %H:%M'):<20} {status:<10}")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        print(f"❌ Error getting alerts: {e}")


def generate_daily_report(date_str: str = None):
    """Generate and show daily performance report."""
    print("\n📊 Daily Performance Report")
    print("=" * 60)
    
    try:
        date = None
        if date_str:
            date = datetime.fromisoformat(date_str)
        
        report = performance_reporter.generate_daily_report(date)
        
        if 'message' in report:
            print(f"📝 {report['message']}")
            return
        
        print(f"📅 Date: {report['date']}")
        
        # Summary
        summary = report['summary']
        print(f"\n📈 Summary:")
        print(f"  Total Operations: {summary['total_operations']}")
        print(f"  Total Duration: {summary['total_duration_hours']:.2f} hours")
        print(f"  Prompts Processed: {summary['total_prompts_processed']}")
        print(f"  Average Prompts/Operation: {summary['average_prompts_per_operation']:.1f}")
        print(f"  Error Rate: {summary['error_rate']:.1%}")
        print(f"  Total Errors: {summary['total_errors']}")
        
        # Hourly breakdown
        if report['hourly_breakdown']:
            print(f"\n⏰ Hourly Activity (top 5 hours):")
            hourly = sorted(report['hourly_breakdown'].items(), 
                           key=lambda x: x[1]['operations'], reverse=True)[:5]
            
            print(f"{'Hour':<6} {'Operations':<10} {'Prompts':<8} {'Avg Duration':<12} {'Errors':<6}")
            print("-" * 50)
            
            for hour, stats in hourly:
                duration = f"{stats['avg_duration']:.1f}s"
                print(f"{hour:<6} {stats['operations']:<10} {stats['prompts']:<8} {duration:<12} {stats['errors']:<6}")
        
        # Performance peaks
        peaks = report['performance_peaks']
        print(f"\n🏆 Performance Peaks:")
        print(f"  Highest Throughput: {peaks['highest_throughput']['throughput']:.2f} prompts/sec")
        print(f"    Operation: {peaks['highest_throughput']['operation_id'][:40]}")
        print(f"  Longest Operation: {peaks['longest_operation']['duration_seconds']:.1f} seconds")
        print(f"    Operation: {peaks['longest_operation']['operation_id'][:40]}")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        print(f"❌ Error generating daily report: {e}")


def export_metrics(hours: int = 24, format_type: str = "csv"):
    """Export performance metrics."""
    print(f"\n💾 Exporting Performance Metrics ({hours}h, {format_type.upper()})")
    print("=" * 60)
    
    try:
        if format_type.lower() == "csv":
            csv_path = performance_reporter.export_metrics_csv(hours=hours)
            print(f"✅ Metrics exported to: {csv_path}")
        else:
            print(f"❌ Unsupported format: {format_type}")
            print("Supported formats: csv")
        
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        print(f"❌ Error exporting metrics: {e}")


async def start_monitoring():
    """Start health monitoring."""
    print("\n🚀 Starting Health Monitoring")
    print("=" * 60)
    
    try:
        # Start resource monitoring
        health_monitor.resource_monitor.start_monitoring()
        print("✅ Resource monitoring started")
        
        # Start health monitoring
        await health_monitor.start_monitoring()
        print("✅ Health monitoring started")
        
        print("\n🔄 Monitoring is now active. Press Ctrl+C to stop.")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(10)
                # Could add periodic status updates here
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping monitoring...")
            
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        print(f"❌ Error starting monitoring: {e}")
    finally:
        # Cleanup
        await health_monitor.stop_monitoring()
        health_monitor.resource_monitor.stop_monitoring()
        print("✅ Monitoring stopped")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MASB System Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current system status
  python monitor_system.py --status
  
  # Show performance metrics for last 24 hours
  python monitor_system.py --performance --hours 24
  
  # Show resource usage for last hour
  python monitor_system.py --resources --minutes 60
  
  # Show system alerts
  python monitor_system.py --alerts --hours 48
  
  # Generate daily report
  python monitor_system.py --daily-report --date 2024-01-15
  
  # Export metrics to CSV
  python monitor_system.py --export csv --hours 72
  
  # Start continuous monitoring
  python monitor_system.py --start-monitoring
        """
    )
    
    parser.add_argument('--status', action='store_true',
                       help='Show current system status')
    
    parser.add_argument('--performance', action='store_true',
                       help='Show performance metrics')
    
    parser.add_argument('--resources', action='store_true',
                       help='Show resource usage')
    
    parser.add_argument('--alerts', action='store_true',
                       help='Show system alerts')
    
    parser.add_argument('--daily-report', action='store_true',
                       help='Generate daily performance report')
    
    parser.add_argument('--export', choices=['csv'],
                       help='Export performance metrics')
    
    parser.add_argument('--start-monitoring', action='store_true',
                       help='Start continuous health monitoring')
    
    parser.add_argument('--hours', type=int, default=24,
                       help='Hours of history to analyze (default: 24)')
    
    parser.add_argument('--minutes', type=int, default=60,
                       help='Minutes of history for resource usage (default: 60)')
    
    parser.add_argument('--operation-type', type=str,
                       help='Filter performance metrics by operation type')
    
    parser.add_argument('--date', type=str,
                       help='Date for daily report (YYYY-MM-DD format)')
    
    args = parser.parse_args()
    
    if args.status:
        show_system_status()
    elif args.performance:
        show_performance_metrics(args.hours, args.operation_type)
    elif args.resources:
        show_resource_usage(args.minutes)
    elif args.alerts:
        show_alerts(args.hours)
    elif args.daily_report:
        generate_daily_report(args.date)
    elif args.export:
        export_metrics(args.hours, args.export)
    elif args.start_monitoring:
        asyncio.run(start_monitoring())
    else:
        parser.print_help()


if __name__ == '__main__':
    main()