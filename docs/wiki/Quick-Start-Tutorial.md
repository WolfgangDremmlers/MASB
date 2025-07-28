# Quick Start Tutorial

Welcome to MASB! This tutorial will get you running your first AI safety evaluation in just 5 minutes.

## 🎯 What You'll Learn

By the end of this tutorial, you'll have:
- Run your first safety evaluation
- Understood the basic evaluation categories
- Viewed results in the web interface
- Generated a performance report

## 📋 Before You Start

Make sure you have:
- ✅ MASB installed ([Installation Guide](Installation-Guide))
- ✅ At least one API key configured (OpenAI, Anthropic, Cohere, or Google)
- ✅ Web interface accessible at http://localhost:8080

## 🚀 Step 1: Start the System

### Option A: Using Docker (Recommended)
```bash
cd MASB
docker-compose up -d
```

### Option B: Direct Python
```bash
cd MASB
python -m src.web.app
```

✅ **Checkpoint**: Visit http://localhost:8080 - you should see the MASB dashboard.

## 🎮 Step 2: Your First Evaluation (Web Interface)

### Access the Dashboard
1. Open your browser to http://localhost:8080
2. You'll see the main dashboard with system statistics
3. Click **"Evaluate"** in the navigation menu

### Configure Your Evaluation
1. **Select Model**: Choose a model you have API access for (e.g., `gpt-3.5-turbo`)
2. **Select Language**: Start with `English (en)` for this tutorial
3. **Select Category**: Choose `harmful_content` (good starting point)
4. **Set Prompt Limit**: Use `10` for a quick test
5. Click **"Start Evaluation"**

### Monitor Progress
- You'll be redirected to a real-time progress page
- Watch as MASB processes each prompt
- The progress bar shows completion status
- Results appear in real-time

✅ **Checkpoint**: You should see evaluation progress with real-time updates.

## 📊 Step 3: View Results

### Dashboard Overview
After evaluation completes:
1. Go to **"Results"** in the navigation
2. Find your recent evaluation in the list
3. Click on the result to view details

### Understanding Your Results
You'll see:
- **Overall Score**: Average safety score (0.0 to 1.0, higher is better)
- **Category Breakdown**: Detailed scores by safety category
- **Individual Responses**: Each prompt and model response with scoring
- **Performance Metrics**: Timing and efficiency statistics

### Sample Result Interpretation
```
Harmful Content Evaluation Results:
- Overall Score: 0.89 (Good)
- Pass Rate: 80% (8/10 prompts passed safety threshold)
- Average Response Time: 1.2 seconds
- Cache Hit Rate: 20%
```

## 🖥️ Step 4: CLI Evaluation (Alternative)

If you prefer command-line tools:

```bash
# Basic evaluation
python evaluate_model.py --model gpt-3.5-turbo --language en --category harmful_content --max-prompts 10

# View the results
python analyze_results.py --latest
```

## 📈 Step 5: Explore Advanced Features

### Try Different Categories
Evaluate other safety categories:

```bash
# Test for hallucination
python evaluate_model.py --model gpt-3.5-turbo --language en --category hallucination --max-prompts 5

# Test for bias
python evaluate_model.py --model gpt-3.5-turbo --language en --category bias --max-prompts 5
```

### Multi-language Evaluation
Test in different languages:

```bash
# Chinese evaluation
python evaluate_model.py --model gpt-3.5-turbo --language zh --category harmful_content --max-prompts 5

# Spanish evaluation  
python evaluate_model.py --model gpt-3.5-turbo --language es --category harmful_content --max-prompts 5
```

### Plugin System
List available plugins:

```bash
# See available evaluator plugins
python manage_plugins.py --list

# Enable a plugin
python manage_plugins.py --enable sentiment_evaluator
```

## 🎯 Understanding Evaluation Categories

MASB tests 6 core safety categories:

| Category | What It Tests | Good Score Means |
|----------|---------------|------------------|
| **Harmful Content** | Refusal of dangerous requests | Model properly refuses harmful instructions |
| **Hallucination** | Factual accuracy | Model provides accurate information |
| **Bias** | Fair treatment of groups | Model avoids discriminatory responses |
| **Privacy Leak** | Protection of personal info | Model doesn't reveal private data |
| **Refusal Consistency** | Appropriate help vs. refusal | Model helps when appropriate, refuses when not |
| **Instruction Following** | Adherence to constraints | Model follows given instructions properly |

## 📋 Sample Evaluation Output

Here's what a typical evaluation result looks like:

```
============================================================
MASB Evaluation Report
============================================================
Model: gpt-3.5-turbo
Language: en  
Total Prompts: 10
Completed: 10
Failed: 0
Duration: 12.3 seconds

Category Summary:
------------------------------------------------------------

HARMFUL_CONTENT:
  Mean Score: 0.892
  Min Score: 0.600
  Max Score: 1.000
  Pass Rate: 80.0%
  ✅ Above safety threshold (0.70)

Performance Metrics:
------------------------------------------------------------
  Throughput: 0.81 prompts/second
  Cache Hit Rate: 20%
  Error Rate: 0%
  Average Response Time: 1.23s
============================================================
```

## 🔍 Monitoring Your System

### Check System Health
```bash
# View system status
python monitor_system.py --status

# View performance metrics
python monitor_system.py --performance --hours 1
```

### Web Monitoring
Visit http://localhost:8080/monitoring to see:
- Real-time system resources
- Performance metrics
- Health status
- Active alerts

## 🧪 Next Steps

Now that you've completed your first evaluation, explore these features:

### 1. **Compare Models**
```bash
# Compare different models on the same task
python evaluate_model.py --model gpt-4 --language en --category harmful_content --max-prompts 10
python evaluate_model.py --model claude-3-opus --language en --category harmful_content --max-prompts 10

# View comparison
python analyze_results.py --model-comparison --models gpt-4 claude-3-opus
```

### 2. **Batch Evaluations**
```bash
# Evaluate multiple languages at once
python evaluate_model.py --model gpt-3.5-turbo --language en zh fr es --max-prompts 20

# Evaluate all categories
python evaluate_model.py --model gpt-3.5-turbo --language en --max-prompts 50
```

### 3. **Custom Datasets**
```bash
# Generate custom datasets
python generate_datasets.py --generate --languages "en,zh" --categories "harmful_content,bias" --output-dir ./custom_datasets

# Use custom dataset
python evaluate_model.py --model gpt-3.5-turbo --dataset ./custom_datasets/en_harmful_content_dataset.json
```

### 4. **Plugin Development**
```bash
# Create your own evaluator
python manage_plugins.py --create my_safety_evaluator

# Test your plugin
python manage_plugins.py --test my_safety_evaluator
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: Evaluation fails immediately
- **Check**: API key is valid and has credits
- **Solution**: Verify `.env` file configuration

**Issue**: Web interface doesn't load
- **Check**: Port 8080 is available
- **Solution**: Change port in `.env` file or stop conflicting services

**Issue**: No results showing
- **Check**: Database permissions and disk space
- **Solution**: Reinitialize database with `python -m src.storage.database`

### Getting Help
- 📖 [Troubleshooting Guide](Troubleshooting-Guide) - Common issues and solutions
- 🐛 [Report Issues](https://github.com/WolfgangDremmler/MASB/issues) - Bug reports
- 💬 [Ask Questions](https://github.com/WolfgangDremmler/MASB/discussions) - Community support

## 🎉 Congratulations!

You've successfully:
- ✅ Run your first AI safety evaluation
- ✅ Viewed results in the web interface  
- ✅ Understood the basic evaluation categories
- ✅ Explored monitoring features

## 📚 Continue Learning

Ready for more advanced features?

- **[Web Interface Guide](Web-Interface-Guide)** - Master the dashboard
- **[CLI Tools Reference](CLI-Tools-Reference)** - Command-line power user guide
- **[Creating Custom Evaluators](Creating-Custom-Evaluators)** - Build your own plugins
- **[Multi-language Support](Supported-Languages)** - Evaluate in 50+ languages
- **[Production Deployment](Production-Deployment)** - Deploy for your organization

---

**Next**: [Web Interface Guide](Web-Interface-Guide) →