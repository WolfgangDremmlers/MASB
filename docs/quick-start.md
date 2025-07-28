# Quick Start Guide

Get MASB running in 5 minutes and perform your first AI safety evaluation!

## 🚀 Quick Installation

### Option 1: Docker (Recommended for Production)

```bash
# Clone the repository
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section below)

# Start all services
docker-compose up -d

# Access the web interface
open http://localhost:8080
```

### Option 2: Python Installation

```bash
# Clone and setup
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB

# Quick installer
python install.py --quick-setup

# Start web interface
python -m src.web.app
```

## ⚙️ Initial Configuration

### 1. Configure API Keys

Edit the `.env` file with your API keys:

```bash
# Required: At least one API key
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
COHERE_API_KEY=your-cohere-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
```

### 2. Verify Installation

```bash
# Run system check
python check_installation.py

# Expected output: ✅ All checks passed! MASB is ready to use.
```

## 🎯 Your First Evaluation

### Method 1: Web Interface (Easiest)

1. **Open Dashboard**: Navigate to http://localhost:8080
2. **Select Model**: Choose a model (e.g., "gpt-3.5-turbo")
3. **Choose Language**: Select evaluation language (e.g., "English")
4. **Pick Category**: Select safety category (e.g., "Harmful Content")
5. **Start Evaluation**: Click "Start Evaluation"
6. **Monitor Progress**: Watch real-time progress updates
7. **View Results**: See comprehensive safety scores and analysis

### Method 2: Command Line Interface

```bash
# Basic evaluation
python evaluate_model.py \
  --model gpt-3.5-turbo \
  --language en \
  --category harmful_content \
  --max-prompts 20

# Expected output:
# 🎯 Starting evaluation for gpt-3.5-turbo in English
# 📊 Category: Harmful Content (20 prompts)
# ⏳ Progress: [████████████████████] 100%
# 
# 📈 Results Summary:
# Overall Score: 0.89/1.00 (Excellent)
# Pass Rate: 92% (18/20 prompts passed)
# 
# 💾 Results saved to: results/batch_20240115_103045.json
# 🌐 View in dashboard: http://localhost:8080/results/batch_20240115_103045
```

### Method 3: Python API

```python
import asyncio
from src.evaluation_engine import EvaluationEngine

async def run_evaluation():
    # Initialize engine
    engine = EvaluationEngine("gpt-3.5-turbo")
    
    # Run evaluation
    result = await engine.evaluate_batch(
        language="en",
        category="harmful_content",
        max_prompts=10
    )
    
    print(f"Overall Score: {result.summary.overall_score:.2f}")
    print(f"Pass Rate: {result.summary.pass_rate:.2%}")

# Run the evaluation
asyncio.run(run_evaluation())
```

## 📊 Understanding Results

### Score Interpretation

| Score Range | Safety Level | Description |
|-------------|--------------|-------------|
| 0.90 - 1.00 | Excellent | Model shows excellent safety behavior |
| 0.80 - 0.89 | Good | Model is generally safe with minor issues |
| 0.70 - 0.79 | Fair | Model needs improvement in some areas |
| 0.60 - 0.69 | Poor | Significant safety concerns detected |
| 0.00 - 0.59 | Critical | Major safety issues require immediate attention |

### Key Metrics

- **Overall Score**: Average safety score across all categories
- **Pass Rate**: Percentage of prompts that met safety thresholds
- **Category Scores**: Performance in specific safety areas
- **Confidence**: Statistical confidence in the results

### Result Categories

1. **Harmful Content**: Refusal of dangerous/illegal requests
2. **Hallucination**: Factual accuracy and truthfulness
3. **Bias**: Fair treatment across different groups  
4. **Privacy Leak**: Protection of personal information
5. **Refusal Consistency**: Appropriate help vs. refusal balance
6. **Instruction Following**: Adherence to given constraints

## 🌍 Multi-Language Testing

Test your model across multiple languages:

```bash
# Test across major languages
python evaluate_model.py \
  --model gpt-4 \
  --languages en,zh,fr,es,de \
  --category harmful_content \
  --max-prompts 50

# Generate language-specific datasets
python generate_datasets.py \
  --generate \
  --languages zh,ja,ko \
  --categories harmful_content,bias
```

## 🔌 Using Plugins

Extend MASB with custom evaluators:

```bash
# List available plugins
python manage_plugins.py --list

# Enable a plugin
python manage_plugins.py --enable sentiment_evaluator

# Create custom plugin
python manage_plugins.py --create my_custom_evaluator

# Test plugin
python manage_plugins.py --test my_custom_evaluator
```

## 📈 Monitoring & Analysis

### Real-time Monitoring

Access monitoring dashboard at: http://localhost:8080/monitoring

- **System Health**: CPU, memory, disk usage
- **Evaluation Progress**: Real-time updates
- **Performance Metrics**: Throughput, error rates
- **Resource Usage**: API calls, costs

### Result Analysis

```bash
# Analyze recent results
python analyze_results.py --days 7

# Compare models
python analyze_results.py --compare gpt-3.5-turbo,gpt-4

# Export results
python analyze_results.py --export-csv --output results.csv

# Generate report
python analyze_results.py --report --format pdf
```

## 🔧 Common Configurations

### High-Volume Evaluation

```bash
# .env configurations for high throughput
CONCURRENT_REQUESTS=10
BATCH_SIZE=50
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

### Development Testing

```bash
# Quick testing setup
DEFAULT_MAX_PROMPTS=5
CONCURRENT_REQUESTS=2
LOG_LEVEL=DEBUG
```

### Production Deployment

```bash
# Production optimizations
CACHE_ENABLED=true
PERFORMANCE_MONITORING=true
DATABASE_URL=postgresql://user:pass@localhost/masb
WEB_HOST=0.0.0.0
WEB_PORT=80
```

## 🚨 Troubleshooting Quick Fixes

### Installation Issues

```bash
# Fix Python path issues
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Reset database
rm -f data/masb.db && python -m src.storage.database
```

### API Issues

```bash
# Test API connectivity
python test_apis.py

# Check API key format
cat .env | grep API_KEY

# Reduce rate limits
echo "CONCURRENT_REQUESTS=1" >> .env
```

### Performance Issues

```bash
# Enable caching
echo "CACHE_ENABLED=true" >> .env

# Monitor resources
python monitor_system.py --status

# Clear cache
rm -rf __pycache__ && redis-cli FLUSHALL
```

## 📚 Next Steps

Now that you have MASB running:

1. **[Web Interface Guide](web-interface.md)** - Master the dashboard
2. **[API Documentation](api.md)** - Integrate with your systems
3. **[Plugin Development](plugin-development.md)** - Create custom evaluators
4. **[Multi-language Guide](multilingual.md)** - Expand language coverage
5. **[Production Deployment](production.md)** - Scale for enterprise use

## 💡 Pro Tips

### Optimization Tips

- **Start Small**: Begin with 10-20 prompts per category
- **Use Caching**: Enable caching for repeated evaluations
- **Monitor Costs**: Track API usage in the dashboard
- **Regular Updates**: Keep prompts and evaluators current

### Best Practices

- **Multiple Languages**: Test in languages your users speak
- **All Categories**: Evaluate across all safety categories
- **Version Control**: Track model versions and results
- **Continuous Testing**: Integrate into CI/CD pipelines

### Getting Help

- **Documentation**: Browse the complete [Wiki](README.md)
- **Issues**: Report problems on [GitHub](https://github.com/WolfgangDremmler/MASB/issues)
- **Community**: Join [Discussions](https://github.com/WolfgangDremmler/MASB/discussions)
- **Support**: Contact wolfgang.dremmler@example.com

---

🎉 **Congratulations!** You're now ready to evaluate AI model safety with MASB. Start with a small evaluation and gradually expand to more comprehensive testing.

**What's next?** Try evaluating different models, explore the plugin system, or contribute to the community!