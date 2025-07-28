# MASB - Multilingual Adversarial Safety Benchmark

MASB is a comprehensive, enterprise-ready framework for evaluating AI model safety across multiple languages and categories. It provides systematic testing for hallucination, harmful content, bias, privacy leaks, and instruction following consistency.

## 🌟 Features

### Core Evaluation Framework
- **Multi-language Support**: 50+ languages with comprehensive localization
- **Multiple Safety Categories**: Hallucination, harmful content, bias, privacy leaks, refusal consistency, instruction following
- **Advanced Metrics**: Statistical analysis, confidence intervals, performance tracking
- **Caching System**: Intelligent result caching for improved performance
- **Database Integration**: SQLite with Alembic migrations for persistent storage

### Plugin System
- **Extensible Architecture**: Custom evaluator plugins for specialized assessments
- **Template Generation**: Automated plugin template creation
- **Configuration Management**: JSON-based plugin configuration with validation
- **Runtime Management**: Enable/disable plugins without restart

### Web Interface
- **Interactive Dashboard**: Real-time evaluation monitoring and results visualization
- **Multi-language UI**: Localized interface in multiple languages
- **Plugin Management**: Web-based plugin configuration and control
- **Export Capabilities**: CSV/JSON export with filtering options

### Performance Monitoring
- **Resource Tracking**: CPU, memory, disk, and GPU usage monitoring
- **Performance Metrics**: Throughput, latency, error rates, and cache statistics
- **Health Monitoring**: Automated health checks with alerting
- **Daily Reports**: Comprehensive performance and usage reports

### Development & Operations
- **CI/CD Pipeline**: Automated testing, building, and deployment
- **Docker Support**: Complete containerization with docker-compose
- **Comprehensive Testing**: Unit, integration, API, and performance tests
- **API Documentation**: OpenAPI/Swagger documentation

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python -m src.storage.database

# Start the web interface
python -m src.web.app
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f masb-app

# Scale evaluation workers
docker-compose up -d --scale masb-worker=3
```

### Basic Usage

```python
from src.evaluation_engine import EvaluationEngine

# Initialize evaluation engine
engine = EvaluationEngine("gpt-4")

# Evaluate a single prompt in Chinese
result = await engine.evaluate_dataset(
    language="zh",
    category="harmful_content",
    max_prompts=50
)

print(engine.get_summary_report(result))
```

## 🔧 CLI Tools

### Dataset Management
```bash
# Generate multi-language datasets
python generate_datasets.py --generate --languages "en,zh,fr,es" --output-dir ./datasets

# List supported languages
python generate_datasets.py --list-languages

# Validate existing datasets
python generate_datasets.py --validate ./datasets
```

### Plugin Management
```bash
# List all plugins
python manage_plugins.py --list

# Create a new plugin
python manage_plugins.py --create sentiment_analyzer

# Enable/disable plugins
python manage_plugins.py --enable keyword_evaluator
python manage_plugins.py --disable length_evaluator

# Test a plugin
python manage_plugins.py --test sentiment_evaluator
```

### System Monitoring
```bash
# Show system status
python monitor_system.py --status

# View performance metrics
python monitor_system.py --performance --hours 24

# Monitor resource usage
python monitor_system.py --resources --minutes 60

# Generate daily report
python monitor_system.py --daily-report --date 2024-01-15

# Start continuous monitoring
python monitor_system.py --start-monitoring
```

## 📊 Web Interface

Access the web interface at `http://localhost:8080` after starting the application.

### Main Sections

- **Dashboard**: Overview of recent evaluations and system statistics
- **Evaluate**: Interactive evaluation interface with real-time progress
- **Results**: Browse and analyze evaluation results with filtering
- **Analysis**: Advanced analytics with comparative visualizations
- **Plugins**: Manage and configure evaluation plugins
- **Monitoring**: System health and performance monitoring
- **Settings**: Application configuration and preferences

### API Endpoints

```bash
# System status
GET /api/monitoring/status

# Evaluation results
GET /api/results?model=gpt-4&language=en&limit=50

# Plugin management
GET /api/plugins
POST /api/plugins/{name}/enable
POST /api/plugins/{name}/disable

# Performance metrics
GET /api/monitoring/performance?hours=24
GET /api/monitoring/resources?minutes=60
```

## 🔌 Plugin Development

### Creating a Custom Evaluator

1. **Generate Template**
```bash
python manage_plugins.py --create my_evaluator
```

2. **Implement Evaluator**
```python
class MyCustomEvaluator(BaseEvaluator):
    async def evaluate(self, prompt: TestPrompt, response: ModelResponse) -> EvaluationScore:
        # Your custom evaluation logic
        score = self.calculate_safety_score(response.text)
        
        return EvaluationScore(
            category=Category.HARMFUL_CONTENT,
            score=score,
            reasoning="Custom evaluation reasoning",
            confidence=0.8,
            details={"custom_metric": score}
        )
```

3. **Configure Plugin**
```json
{
  "my_evaluator": {
    "enabled": true,
    "config": {
      "threshold": 0.7,
      "custom_param": "value"
    },
    "priority": 1
  }
}
```

## 🌍 Multi-language Support

### Supported Languages (50+)

MASB supports evaluation in 50+ languages including:

- **High Support**: English, Chinese, French, Spanish, German, Japanese, Korean, Arabic
- **Good Support**: Russian, Portuguese, Italian, Hindi, Dutch, Swedish, Polish
- **Fair Support**: Turkish, Thai, Vietnamese, Hebrew, Greek, Czech, Hungarian
- **Growing Support**: Many more languages with varying levels of AI model support

### Language-Specific Features

- **Localized Prompts**: Native prompt templates for each language
- **Cultural Context**: Culture-aware bias and safety evaluation
- **Script Support**: Latin, Cyrillic, Arabic, CJK, Devanagari, and more
- **RTL Languages**: Proper support for right-to-left languages

## 📈 Performance Monitoring

### Real-time Metrics

- **Throughput**: Prompts/second processing rate
- **Latency**: Response time distribution
- **Resource Usage**: CPU, memory, disk, GPU utilization
- **Error Rates**: Failed evaluations and their causes
- **Cache Performance**: Hit rates and efficiency

### Health Monitoring

- **Automated Checks**: System health validation
- **Alert System**: Configurable thresholds and notifications
- **Trend Analysis**: Performance trend detection
- **Resource Limits**: Proactive monitoring of resource constraints

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/api/           # API tests
pytest tests/performance/   # Performance tests

# Run with coverage
pytest --cov=src --cov-report=html
```

## 🚀 Deployment

### Production Deployment

```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Using Kubernetes
kubectl apply -f k8s/

# Manual deployment
gunicorn --bind 0.0.0.0:8080 src.web.app:app
```

### Environment Configuration

```bash
# .env file
DATABASE_URL=postgresql://user:pass@localhost/masb
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Scaling configuration
BATCH_SIZE=20
CONCURRENT_REQUESTS=10
CACHE_TTL_SECONDS=7200

# Plugin System
ENABLE_PLUGINS=true
PLUGIN_AUTO_LOAD=true

# Monitoring
ENABLE_PERFORMANCE_MONITORING=true
RESOURCE_MONITORING_INTERVAL=1.0
```

## 📚 Configuration

### Main Configuration File

Configuration is managed through `src/config.py` using Pydantic settings:

```python
# API Keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Performance Settings
BATCH_SIZE=10
CONCURRENT_REQUESTS=5
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# Plugin System
ENABLE_PLUGINS=true
PLUGIN_AUTO_LOAD=true

# Monitoring
ENABLE_PERFORMANCE_MONITORING=true
RESOURCE_MONITORING_INTERVAL=1.0
```

## 🤝 Contributing

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run development server
python -m src.web.app --debug
```

### Code Quality

- **Linting**: Black, Flake8, MyPy for code quality
- **Testing**: Comprehensive test coverage requirement
- **Documentation**: Docstring requirements for all public functions
- **Type Hints**: Full type annotation coverage

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Citation

If you use MASB in your research, please cite:

```bibtex
@software{masb2024,
  title={MASB: Multilingual Adversarial Safety Benchmark},
  author={Wolfgang Dremmler},
  year={2024},
  url={https://github.com/WolfgangDremmler/MASB}
}
```

## 📞 Support

- **Documentation**: [Wiki](https://github.com/WolfgangDremmler/MASB/wiki)
- **Issues**: [GitHub Issues](https://github.com/WolfgangDremmler/MASB/issues)
- **Discussions**: [GitHub Discussions](https://github.com/WolfgangDremmler/MASB/discussions)
- **Email**: wolfgang.dremmler@example.com

---

**MASB** - Making AI Safety Evaluation Accessible and Comprehensive 🚀