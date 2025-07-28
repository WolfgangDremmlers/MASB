"""Web interface for MASB - Flask application."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
import plotly.graph_objects as go
import plotly.utils
from werkzeug.security import generate_password_hash, check_password_hash

from src.evaluation_engine import EvaluationEngine
from src.analysis.result_analyzer import ResultAnalyzer
from src.models.data_models import Language, Category
from src.models.provider_factory import ProviderFactory
from src.config import SUPPORTED_LANGUAGES, SUPPORTED_MODELS
from src.utils.logger import logger
from src.utils.config_validator import config_manager
from src.storage.database import db_manager
from src.analysis.advanced_metrics import AdvancedMetrics, MetricsReporter
from src.localization.languages import localization_manager, EXTENDED_LANGUAGE_INFO
from src.plugins.plugin_system import plugin_manager
from src.monitoring.performance_monitor import performance_tracker, performance_reporter
from src.monitoring.health_monitor import health_monitor


class MASBWebApp:
    """MASB Web Application."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize web application.
        
        Args:
            config: Application configuration
        """
        self.config = config or {}
        self.app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
        self.app.secret_key = self.config.get('secret_key', 'masb-secret-key-change-me')
        
        # Initialize SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize components
        self.analyzer = ResultAnalyzer()
        self.metrics_calculator = AdvancedMetrics()
        self.metrics_reporter = MetricsReporter()
        self.evaluation_tasks = {}  # Track running evaluations
        
        # Initialize database
        try:
            db_manager.initialize()
            logger.info("Database initialized for web application")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
        
        # Initialize localization
        self.current_locale = self.config.get('default_locale', 'en')
        localization_manager.set_locale(self.current_locale)
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()
        
        logger.info("MASB Web Application initialized")
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.before_request
        def before_request():
            """Handle locale detection and setup before each request."""
            # Check for locale in URL parameter
            locale = request.args.get('locale')
            if locale and locale in [info['code'] for info in localization_manager.get_supported_languages()]:
                localization_manager.set_locale(locale)
                session['locale'] = locale
            # Check for locale in session
            elif 'locale' in session:
                localization_manager.set_locale(session['locale'])
            # Check Accept-Language header
            elif request.headers.get('Accept-Language'):
                preferred = request.headers.get('Accept-Language').split(',')[0].split('-')[0]
                if preferred in [info['code'] for info in localization_manager.get_supported_languages()]:
                    localization_manager.set_locale(preferred)
        
        @self.app.context_processor
        def inject_localization():
            """Inject localization functions into templates."""
            return {
                'get_text': localization_manager.get_text,
                'current_locale': localization_manager.current_locale,
                'supported_languages': localization_manager.get_supported_languages(),
                'extended_language_info': EXTENDED_LANGUAGE_INFO
            }
        
        @self.app.route('/set-locale/<locale>')
        def set_locale(locale):
            """Set user locale."""
            if locale in [info['code'] for info in localization_manager.get_supported_languages()]:
                localization_manager.set_locale(locale)
                session['locale'] = locale
                flash(localization_manager.get_text('settings.language.changed'), 'success')
            else:
                flash(localization_manager.get_text('error.invalid_language'), 'error')
            
            # Redirect back to referring page
            return redirect(request.referrer or url_for('index'))
        
        @self.app.route('/')
        def index():
            """Main dashboard."""
            try:
                # Load recent results from database
                results = db_manager.list_batch_results(limit=100)
                recent_results = sorted(results, key=lambda x: x.start_time, reverse=True)[:5]
                
                # Basic statistics
                stats = {
                    'total_evaluations': len(results),
                    'models_tested': len(set(r.model_name for r in results)),
                    'languages_tested': len(set(r.language.value for r in results)),
                    'recent_evaluations': len([r for r in results if 
                                             (datetime.utcnow() - r.start_time).days < 7])
                }
                
                return render_template('dashboard.html', 
                                     recent_results=recent_results,
                                     stats=stats,
                                     supported_models=SUPPORTED_MODELS,
                                     supported_languages=SUPPORTED_LANGUAGES)
            except Exception as e:
                logger.error(f"Dashboard error: {e}")
                return render_template('error.html', error=str(e))
        
        @self.app.route('/evaluate', methods=['GET', 'POST'])
        def evaluate():
            """Evaluation interface."""
            if request.method == 'POST':
                try:
                    # Get form data
                    model_name = request.form.get('model')
                    language = request.form.get('language')
                    category = request.form.get('category')
                    max_prompts = int(request.form.get('max_prompts', 10))
                    
                    # Validate inputs
                    if not model_name or model_name not in SUPPORTED_MODELS:
                        flash('Invalid model selected', 'error')
                        return redirect(url_for('evaluate'))
                    
                    if not language or language not in SUPPORTED_LANGUAGES:
                        flash('Invalid language selected', 'error')
                        return redirect(url_for('evaluate'))
                    
                    # Start evaluation task
                    task_id = self._start_evaluation_task(
                        model_name, language, category, max_prompts
                    )
                    
                    return redirect(url_for('evaluation_status', task_id=task_id))
                    
                except Exception as e:
                    logger.error(f"Evaluation start error: {e}")
                    flash(f'Error starting evaluation: {e}', 'error')
                    return redirect(url_for('evaluate'))
            
            return render_template('evaluate.html',
                                 supported_models=SUPPORTED_MODELS,
                                 supported_languages=SUPPORTED_LANGUAGES,
                                 evaluation_categories=[c.value for c in Category])
        
        @self.app.route('/evaluation/<task_id>')
        def evaluation_status(task_id):
            """Show evaluation status."""
            if task_id not in self.evaluation_tasks:
                flash('Evaluation not found', 'error')
                return redirect(url_for('index'))
            
            task = self.evaluation_tasks[task_id]
            return render_template('evaluation_status.html', task=task, task_id=task_id)
        
        @self.app.route('/results')
        def results():
            """Results overview."""
            try:
                # Load results from database instead of file system
                results = db_manager.list_batch_results(limit=100)
                
                # Group by model for display
                results_by_model = {}
                for result in results:
                    model = result.model_name
                    if model not in results_by_model:
                        results_by_model[model] = []
                    results_by_model[model].append(result)
                
                return render_template('results.html', 
                                     results=results, 
                                     results_by_model=results_by_model)
                                     
            except Exception as e:
                logger.error(f"Results page error: {e}")
                return render_template('error.html', error=str(e))
        
        @self.app.route('/results/<result_id>')
        def result_detail(result_id):
            """Detailed result view."""
            try:
                # Get result from database
                result = db_manager.get_batch_result(result_id)
                
                if not result:
                    flash('Result not found', 'error')
                    return redirect(url_for('results'))
                
                # Generate advanced metrics report
                metrics_report = self.metrics_reporter.generate_comprehensive_report([result])
                
                # Generate plots for visualization
                model_comparison = self.analyzer.plot_model_comparison([result])
                plot_json = json.dumps(model_comparison, cls=plotly.utils.PlotlyJSONEncoder)
                
                return render_template('result_detail.html', 
                                     result=result,
                                     metrics_report=metrics_report,
                                     plot_json=plot_json)
                                     
            except Exception as e:
                logger.error(f"Result detail error: {e}")
                flash(f'Error loading result: {e}', 'error')
                return redirect(url_for('results'))
        
        @self.app.route('/analysis')
        def analysis():
            """Analysis and comparison interface."""
            try:
                # Load results from database
                results = db_manager.list_batch_results(limit=100)
                
                if not results:
                    return render_template('analysis.html', results=[], plots={})
                
                # Generate comprehensive metrics report
                metrics_report = self.metrics_reporter.generate_comprehensive_report(results)
                
                # Generate comparison plots
                plots = {}
                
                # Model comparison
                if len(set(r.model_name for r in results)) > 1:
                    model_plot = self.analyzer.plot_model_comparison(results)
                    plots['model_comparison'] = json.dumps(model_plot, cls=plotly.utils.PlotlyJSONEncoder)
                
                # Language comparison  
                if len(set(r.language.value for r in results)) > 1:
                    lang_plot = self.analyzer.plot_language_comparison(results)
                    plots['language_comparison'] = json.dumps(lang_plot, cls=plotly.utils.PlotlyJSONEncoder)
                
                # Category breakdown
                category_plot = self.analyzer.plot_category_breakdown(results)
                plots['category_breakdown'] = json.dumps(category_plot, cls=plotly.utils.PlotlyJSONEncoder)
                
                return render_template('analysis.html', 
                                     results=results, 
                                     plots=plots,
                                     metrics_report=metrics_report)
                
            except Exception as e:
                logger.error(f"Analysis page error: {e}")
                return render_template('error.html', error=str(e))
        
        @self.app.route('/api/status/<task_id>')
        def api_status(task_id):
            """API endpoint for evaluation status."""
            if task_id not in self.evaluation_tasks:
                return jsonify({'error': 'Task not found'}), 404
            
            task = self.evaluation_tasks[task_id]
            return jsonify(task)
        
        @self.app.route('/api/models')
        def api_models():
            """API endpoint for supported models."""
            return jsonify(SUPPORTED_MODELS)
        
        @self.app.route('/api/languages')
        def api_languages():
            """API endpoint for supported languages."""
            return jsonify(SUPPORTED_LANGUAGES)
        
        @self.app.route('/api/extended-languages')
        def api_extended_languages():
            """API endpoint for extended language support."""
            return jsonify(localization_manager.get_supported_languages())
        
        @self.app.route('/api/language-info/<language_code>')
        def api_language_info(language_code):
            """API endpoint for specific language information."""
            info = localization_manager.get_language_info(language_code)
            if info:
                return jsonify({
                    'code': info.code,
                    'name': info.name,
                    'native_name': info.native_name,
                    'family': info.family,
                    'script': info.script,
                    'rtl': info.rtl,
                    'complexity': info.complexity_level,
                    'ai_support': info.ai_support_level
                })
            else:
                return jsonify({'error': 'Language not found'}), 404
        
        @self.app.route('/api/localization/<key>')
        def api_localization(key):
            """API endpoint for localized text."""
            locale = request.args.get('locale', localization_manager.current_locale)
            text = localization_manager.get_text(key, locale)
            return jsonify({'key': key, 'text': text, 'locale': locale})
        
        @self.app.route('/api/statistics')
        def api_statistics():
            """API endpoint for database statistics."""
            try:
                model_filter = request.args.get('model')
                language_filter = request.args.get('language')
                days = int(request.args.get('days', 30))
                
                stats = db_manager.get_evaluation_statistics(
                    model_name=model_filter,
                    language=language_filter,
                    days=days
                )
                
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"API statistics error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/results')
        def api_results():
            """API endpoint for evaluation results."""
            try:
                model_filter = request.args.get('model')
                language_filter = request.args.get('language')
                category_filter = request.args.get('category')
                limit = int(request.args.get('limit', 50))
                
                results = db_manager.list_batch_results(
                    model_name=model_filter,
                    language=language_filter,
                    category=category_filter,
                    limit=limit
                )
                
                # Convert to JSON-serializable format
                results_data = []
                for result in results:
                    results_data.append({
                        'batch_id': result.batch_id,
                        'model_name': result.model_name,
                        'language': result.language.value,
                        'category': result.category.value if result.category else None,
                        'start_time': result.start_time.isoformat(),
                        'duration': result.duration,
                        'total_prompts': result.total_prompts,
                        'completed_prompts': result.completed_prompts,
                        'status': result.status,
                        'summary': result.summary
                    })
                
                return jsonify(results_data)
                
            except Exception as e:
                logger.error(f"API results error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/results/<result_id>/delete', methods=['DELETE'])
        def api_delete_result(result_id):
            """API endpoint to delete a result."""
            try:
                success = db_manager.delete_batch_result(result_id)
                
                if success:
                    return jsonify({'message': 'Result deleted successfully'})
                else:
                    return jsonify({'error': 'Result not found'}), 404
                    
            except Exception as e:
                logger.error(f"API delete result error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export')
        def api_export():
            """API endpoint to export results."""
            try:
                from src.storage.migrations import DataImportExport
                import tempfile
                
                format_type = request.args.get('format', 'json')  # 'json' or 'csv'
                model_filter = request.args.get('model')
                language_filter = request.args.get('language')
                
                exporter = DataImportExport(db_manager)
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format_type}') as tmp_file:
                    tmp_path = Path(tmp_file.name)
                
                if format_type == 'json':
                    success = exporter.export_to_json(
                        tmp_path,
                        model_name=model_filter,
                        language=language_filter
                    )
                elif format_type == 'csv':
                    success = exporter.export_to_csv(
                        tmp_path,
                        model_name=model_filter,
                        language=language_filter
                    )
                else:
                    return jsonify({'error': 'Unsupported format'}), 400
                
                if success:
                    # Return file for download
                    from flask import send_file
                    return send_file(
                        tmp_path, 
                        as_attachment=True,
                        download_name=f'masb_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{format_type}'
                    )
                else:
                    return jsonify({'error': 'Export failed'}), 500
                    
            except Exception as e:
                logger.error(f"API export error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/settings', methods=['GET', 'POST'])
        def settings():
            """Settings page."""
            if request.method == 'POST':
                # Handle settings update
                try:
                    # Get settings from form
                    new_settings = {
                        'batch_size': int(request.form.get('batch_size', 10)),
                        'concurrent_requests': int(request.form.get('concurrent_requests', 5)),
                        'max_retries': int(request.form.get('max_retries', 3)),
                    }
                    
                    # Update configuration (in a real app, you'd save this)
                    self.config.update(new_settings)
                    
                    flash('Settings updated successfully', 'success')
                    
                except Exception as e:
                    flash(f'Error updating settings: {e}', 'error')
                
                return redirect(url_for('settings'))
            
            return render_template('settings.html', config=self.config)
        
        @self.app.route('/plugins')
        def plugins():
            """Plugin management interface."""
            try:
                # Load all plugins information
                plugin_infos = plugin_manager.list_plugins()
                
                # Get plugin configurations
                plugin_configs = plugin_manager.plugin_configs
                
                # Organize plugins by status
                plugins_by_status = {
                    'active': [],
                    'inactive': [],
                    'error': []
                }
                
                for plugin_info in plugin_infos:
                    status = 'active' if plugin_info.name in plugin_manager.plugins else 'inactive'
                    if plugin_info.error_message:
                        status = 'error'
                    
                    plugin_data = {
                        'info': plugin_info,
                        'config': plugin_configs.get(plugin_info.name, {}),
                        'status': status
                    }
                    plugins_by_status[status].append(plugin_data)
                
                return render_template('plugins.html', 
                                     plugins=plugins_by_status,
                                     total_plugins=len(plugin_infos))
                
            except Exception as e:
                logger.error(f"Plugins page error: {e}")
                return render_template('error.html', error=str(e))
        
        @self.app.route('/plugins/create', methods=['GET', 'POST'])
        def create_plugin():
            """Create new plugin from template."""
            if request.method == 'POST':
                try:
                    plugin_name = request.form.get('plugin_name', '').strip()
                    plugin_type = request.form.get('plugin_type', 'evaluator')
                    
                    if not plugin_name:
                        flash('Plugin name is required', 'error')
                        return redirect(url_for('create_plugin'))
                    
                    # Create plugin template
                    template_path = plugin_manager.create_plugin_template(plugin_name, plugin_type)
                    
                    flash(f'Plugin template created: {template_path}', 'success')
                    return redirect(url_for('plugins'))
                    
                except Exception as e:
                    logger.error(f"Plugin creation error: {e}")
                    flash(f'Error creating plugin: {e}', 'error')
                    return redirect(url_for('create_plugin'))
            
            return render_template('create_plugin.html')
        
        @self.app.route('/api/plugins')
        def api_plugins():
            """API endpoint for plugin information."""
            try:
                plugin_infos = plugin_manager.list_plugins()
                plugins_data = []
                
                for info in plugin_infos:
                    plugin_data = {
                        'name': info.name,
                        'version': info.version,
                        'author': info.author,
                        'description': info.description,
                        'category': info.category,
                        'status': info.status.value,
                        'enabled': info.name in plugin_manager.plugins,
                        'supported_categories': []
                    }
                    
                    # Get supported categories if it's an evaluator plugin
                    if info.name in plugin_manager.evaluator_plugins:
                        evaluator_plugin = plugin_manager.evaluator_plugins[info.name]
                        plugin_data['supported_categories'] = [
                            cat.value for cat in evaluator_plugin.get_supported_categories()
                        ]
                    
                    plugins_data.append(plugin_data)
                
                return jsonify(plugins_data)
                
            except Exception as e:
                logger.error(f"API plugins error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/plugins/<plugin_name>/enable', methods=['POST'])
        def api_enable_plugin(plugin_name):
            """API endpoint to enable a plugin."""
            try:
                success = plugin_manager.enable_plugin(plugin_name)
                
                if success:
                    # Reload plugins to activate the enabled plugin
                    plugin_manager.load_all_plugins()
                    return jsonify({'message': f'Plugin {plugin_name} enabled successfully'})
                else:
                    return jsonify({'error': 'Plugin not found'}), 404
                    
            except Exception as e:
                logger.error(f"API enable plugin error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/plugins/<plugin_name>/disable', methods=['POST'])
        def api_disable_plugin(plugin_name):
            """API endpoint to disable a plugin."""
            try:
                success = plugin_manager.disable_plugin(plugin_name)
                
                if success:
                    return jsonify({'message': f'Plugin {plugin_name} disabled successfully'})
                else:
                    return jsonify({'error': 'Plugin not found'}), 404
                    
            except Exception as e:
                logger.error(f"API disable plugin error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/plugins/<plugin_name>/config', methods=['GET', 'POST'])
        def api_plugin_config(plugin_name):
            """API endpoint to get or update plugin configuration."""
            if request.method == 'GET':
                try:
                    if plugin_name not in plugin_manager.plugin_configs:
                        return jsonify({'error': 'Plugin not found'}), 404
                    
                    config = plugin_manager.plugin_configs[plugin_name]
                    return jsonify({
                        'plugin_name': plugin_name,
                        'enabled': config.enabled,
                        'config': config.config,
                        'priority': config.priority
                    })
                    
                except Exception as e:
                    logger.error(f"API get plugin config error: {e}")
                    return jsonify({'error': str(e)}), 500
            
            elif request.method == 'POST':
                try:
                    new_config = request.get_json()
                    if not new_config:
                        return jsonify({'error': 'No configuration provided'}), 400
                    
                    success = plugin_manager.update_plugin_config(plugin_name, new_config)
                    
                    if success:
                        return jsonify({'message': f'Plugin {plugin_name} configuration updated'})
                    else:
                        return jsonify({'error': 'Failed to update configuration'}), 400
                        
                except Exception as e:
                    logger.error(f"API update plugin config error: {e}")
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/plugins/reload', methods=['POST'])
        def api_reload_plugins():
            """API endpoint to reload all plugins."""
            try:
                loaded_count = plugin_manager.load_all_plugins()
                return jsonify({
                    'message': f'Reloaded plugins successfully',
                    'loaded_count': loaded_count
                })
                
            except Exception as e:
                logger.error(f"API reload plugins error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/monitoring')
        def monitoring():
            """System monitoring dashboard."""
            try:
                # Get system status
                system_status = health_monitor.get_system_status()
                
                # Get performance summary
                performance_summary = performance_tracker.get_performance_summary(hours=24)
                
                # Get recent operations
                recent_operations = performance_tracker.get_recent_operations(hours=4)
                
                # Get active alerts
                active_alerts = health_monitor.get_active_alerts()
                
                return render_template('monitoring.html',
                                     system_status=system_status,
                                     performance_summary=performance_summary,
                                     recent_operations=recent_operations[:20],  # Show last 20
                                     active_alerts=active_alerts)
                                     
            except Exception as e:
                logger.error(f"Monitoring page error: {e}")
                return render_template('error.html', error=str(e))
        
        @self.app.route('/api/monitoring/status')
        def api_monitoring_status():
            """API endpoint for system status."""
            try:
                status = health_monitor.get_system_status()
                return jsonify(status)
                
            except Exception as e:
                logger.error(f"API monitoring status error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/monitoring/performance')
        def api_monitoring_performance():
            """API endpoint for performance metrics."""
            try:
                hours = int(request.args.get('hours', 24))
                operation_type = request.args.get('type')
                
                if operation_type:
                    operations = performance_tracker.get_recent_operations(
                        operation_type=operation_type, hours=hours
                    )
                else:
                    operations = performance_tracker.get_recent_operations(hours=hours)
                
                # Convert to serializable format
                operations_data = []
                for op in operations:
                    op_data = {
                        'operation_id': op.operation_id,
                        'operation_type': op.operation_type,
                        'start_time': op.start_time.isoformat(),
                        'duration_seconds': op.duration_seconds,
                        'prompts_processed': op.prompts_processed,
                        'tokens_processed': op.tokens_processed,
                        'requests_made': op.requests_made,
                        'errors_count': op.errors_count,
                        'throughput_prompts_per_second': op.throughput_prompts_per_second,
                        'cache_hits': op.cache_hits,
                        'cache_misses': op.cache_misses
                    }
                    operations_data.append(op_data)
                
                return jsonify({
                    'operations': operations_data,
                    'summary': performance_tracker.get_performance_summary(hours=hours)
                })
                
            except Exception as e:
                logger.error(f"API monitoring performance error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/monitoring/resources')
        def api_monitoring_resources():
            """API endpoint for resource usage."""
            try:
                minutes = int(request.args.get('minutes', 60))
                
                # Get resource history
                resource_history = health_monitor.resource_monitor.get_history(minutes=minutes)
                
                # Convert to serializable format
                history_data = []
                for snapshot in resource_history:
                    snapshot_data = {
                        'timestamp': snapshot.timestamp.isoformat(),
                        'cpu_percent': snapshot.cpu_percent,
                        'memory_percent': snapshot.memory_percent,
                        'memory_used_gb': snapshot.memory_used_gb,
                        'disk_usage_percent': snapshot.disk_usage_percent,
                        'gpu_usage_percent': snapshot.gpu_usage_percent,
                        'gpu_memory_percent': snapshot.gpu_memory_percent,
                        'gpu_temperature': snapshot.gpu_temperature
                    }
                    history_data.append(snapshot_data)
                
                # Get current snapshot
                current = health_monitor.resource_monitor.get_current_snapshot()
                current_data = {
                    'timestamp': current.timestamp.isoformat(),
                    'cpu_percent': current.cpu_percent,
                    'memory_percent': current.memory_percent,
                    'memory_used_gb': current.memory_used_gb,
                    'memory_available_gb': current.memory_available_gb,
                    'disk_usage_percent': current.disk_usage_percent,
                    'gpu_usage_percent': current.gpu_usage_percent,
                    'gpu_memory_percent': current.gpu_memory_percent,
                    'gpu_temperature': current.gpu_temperature,
                    'active_processes': current.active_processes
                }
                
                return jsonify({
                    'current': current_data,
                    'history': history_data,
                    'averages': health_monitor.resource_monitor.get_average_metrics(minutes=minutes)
                })
                
            except Exception as e:
                logger.error(f"API monitoring resources error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/monitoring/alerts')
        def api_monitoring_alerts():
            """API endpoint for system alerts."""
            try:
                hours = int(request.args.get('hours', 24))
                
                active_alerts = health_monitor.get_active_alerts()
                alert_history = health_monitor.get_alert_history(hours=hours)
                
                # Convert to serializable format
                def serialize_alert(alert):
                    return {
                        'id': alert.id,
                        'level': alert.level.value,
                        'title': alert.title,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat(),
                        'source': alert.source,
                        'resolved': alert.resolved,
                        'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                        'metadata': alert.metadata
                    }
                
                return jsonify({
                    'active_alerts': [serialize_alert(alert) for alert in active_alerts],
                    'alert_history': [serialize_alert(alert) for alert in alert_history]
                })
                
            except Exception as e:
                logger.error(f"API monitoring alerts error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/monitoring/reports/daily')
        def api_monitoring_daily_report():
            """API endpoint for daily performance report."""
            try:
                date_str = request.args.get('date')
                date = None
                if date_str:
                    date = datetime.fromisoformat(date_str)
                
                report = performance_reporter.generate_daily_report(date)
                return jsonify(report)
                
            except Exception as e:
                logger.error(f"API daily report error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/monitoring/export/csv')
        def api_monitoring_export_csv():
            """API endpoint to export performance metrics as CSV."""
            try:
                hours = int(request.args.get('hours', 24))
                
                csv_path = performance_reporter.export_metrics_csv(hours=hours)
                
                from flask import send_file
                return send_file(
                    csv_path,
                    as_attachment=True,
                    download_name=f'masb_performance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                )
                
            except Exception as e:
                logger.error(f"API export CSV error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers for real-time updates."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info('Client connected')
            emit('status', {'msg': 'Connected to MASB'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info('Client disconnected')
    
    def _start_evaluation_task(self, model_name: str, language: str, 
                              category: Optional[str], max_prompts: int) -> str:
        """Start an evaluation task in the background.
        
        Args:
            model_name: Model to evaluate
            language: Language to test
            category: Optional category filter
            max_prompts: Maximum prompts to evaluate
            
        Returns:
            Task ID
        """
        import uuid
        import threading
        
        task_id = str(uuid.uuid4())
        
        # Create task record
        task = {
            'id': task_id,
            'model': model_name,
            'language': language,
            'category': category,
            'max_prompts': max_prompts,
            'status': 'starting',
            'progress': 0,
            'total': 0,
            'completed': 0,
            'start_time': datetime.utcnow().isoformat(),
            'result': None,
            'error': None
        }
        
        self.evaluation_tasks[task_id] = task
        
        # Start evaluation in background thread
        def run_evaluation():
            try:
                # Update status
                task['status'] = 'running'
                self.socketio.emit('task_update', task)
                
                # Create evaluation engine
                engine = EvaluationEngine(model_name)
                
                # Run evaluation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    engine.evaluate_dataset(
                        language=language,
                        category=Category(category) if category else None,
                        max_prompts=max_prompts
                    )
                )
                
                # Update task with results
                task['status'] = 'completed'
                task['progress'] = 100
                task['total'] = result.total_prompts
                task['completed'] = result.completed_prompts
                task['result'] = {
                    'batch_id': result.batch_id,
                    'summary': dict(result.summary),
                    'duration': result.duration
                }
                task['end_time'] = datetime.utcnow().isoformat()
                
                self.socketio.emit('task_update', task)
                logger.info(f"Evaluation task {task_id} completed")
                
            except Exception as e:
                logger.error(f"Evaluation task {task_id} failed: {e}")
                task['status'] = 'failed'
                task['error'] = str(e)
                task['end_time'] = datetime.utcnow().isoformat()
                self.socketio.emit('task_update', task)
        
        thread = threading.Thread(target=run_evaluation)
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def run(self, host='127.0.0.1', port=8080, debug=False):
        """Run the web application.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        logger.info(f"Starting MASB Web Interface on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)


def create_app(config: Optional[Dict] = None):
    """Create MASB web application.
    
    Args:
        config: Application configuration
        
    Returns:
        Flask application instance
    """
    webapp = MASBWebApp(config)
    return webapp.app