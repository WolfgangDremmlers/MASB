# Installation Guide

This comprehensive guide will help you install and set up MASB on your system.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended for large evaluations)
- **Storage**: At least 2GB free disk space
- **Network**: Internet connection for API calls to model providers
- **Operating System**: 
  - Windows 10+ 
  - macOS 10.14+
  - Linux (Ubuntu 18.04+, CentOS 7+, or equivalent)

### Required API Keys
You'll need API keys for at least one AI model provider:

| Provider | Models Available | Get API Key |
|----------|------------------|-------------|
| **OpenAI** | GPT-4, GPT-3.5-turbo | [platform.openai.com](https://platform.openai.com) |
| **Anthropic** | Claude 3 (Opus, Sonnet, Haiku) | [console.anthropic.com](https://console.anthropic.com) |
| **Cohere** | Command, Command-Light | [dashboard.cohere.ai](https://dashboard.cohere.ai) |
| **Google** | Gemini Pro, Gemini Pro Vision | [ai.google.dev](https://ai.google.dev) |

## 🚀 Installation Methods

### Method 1: Quick Install (Recommended)

The fastest way to get MASB running:

```bash
# Clone the repository
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB

# Run the quick installer
python install.py --quick-setup
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up the database
- Create configuration templates
- Verify the installation

### Method 2: Docker Installation (Production Ready)

For production deployments or if you prefer containerization:

#### Prerequisites
- Docker 20.0+ 
- Docker Compose 2.0+

#### Quick Docker Setup
```bash
# Clone repository
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section)

# Start all services
docker-compose up -d

# Verify installation
docker-compose ps
```

#### Access the Application
- **Web Interface**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **System Monitoring**: http://localhost:8080/monitoring

### Method 3: Manual Installation (Advanced)

For developers or custom installations:

#### Step 1: Clone Repository
```bash
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB
```

#### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv masb-env

# Activate virtual environment
# On Windows:
masb-env\Scripts\activate

# On macOS/Linux:
source masb-env/bin/activate
```

#### Step 3: Install Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

#### Step 4: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

#### Step 5: Initialize Database
```bash
# Create and initialize SQLite database
python -m src.storage.database

# Run migrations
python -c "
from src.storage.database import db_manager
db_manager.run_migrations()
print('✅ Database initialized successfully')
"
```

#### Step 6: Verify Installation
```bash
# Run comprehensive system check
python check_installation.py

# Test API connections
python test_apis.py

# Start web interface
python -m src.web.app
```

## ⚙️ Configuration

### Environment Variables (.env file)

Create and configure your `.env` file:

```bash
# ===== API CONFIGURATION =====
# At least one API key is required

# OpenAI (for GPT models)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic (for Claude models)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Cohere (for Command models)
COHERE_API_KEY=your-cohere-api-key-here

# Google (for Gemini models)
GOOGLE_API_KEY=your-google-api-key-here

# ===== MODEL CONFIGURATION =====
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1000
REQUEST_TIMEOUT=60
MAX_RETRIES=3

# ===== PERFORMANCE SETTINGS =====
BATCH_SIZE=10
CONCURRENT_REQUESTS=5
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000

# ===== DATABASE CONFIGURATION =====
DATABASE_URL=sqlite:///./data/masb.db

# ===== WEB INTERFACE =====
WEB_HOST=0.0.0.0
WEB_PORT=8080
SECRET_KEY=your-secret-key-change-this-in-production

# ===== PLUGIN SYSTEM =====
ENABLE_PLUGINS=true
PLUGIN_AUTO_LOAD=true
PLUGIN_CACHE_ENABLED=true

# ===== MONITORING =====
ENABLE_PERFORMANCE_MONITORING=true
RESOURCE_MONITORING_INTERVAL=1.0

# ===== LOGGING =====
LOG_LEVEL=INFO
LOG_FILE=logs/masb.log
```

### Directory Structure

After installation, your project structure should look like:

```
MASB/
├── src/                      # Source code
│   ├── analysis/            # Result analysis tools
│   ├── evaluators/          # Safety evaluators
│   ├── localization/        # Multi-language support
│   ├── models/              # AI model providers
│   ├── monitoring/          # Performance monitoring
│   ├── plugins/             # Plugin system
│   ├── storage/             # Database and persistence
│   ├── utils/               # Utility functions
│   └── web/                 # Web interface
├── plugins/                  # Custom plugins directory
├── tests/                    # Test files
├── data/                     # Data and databases
├── logs/                     # Log files
├── docs/                     # Documentation
├── .env                      # Environment configuration
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker configuration
└── README.md                 # Project overview
```

## 🧪 Verification and Testing

### Installation Verification

Run the built-in system check:

```bash
python check_installation.py
```

Expected output:
```
🔍 MASB Installation Check
==================================================

Python Version:
✅ Python 3.9.7

Dependencies:
✅ flask
✅ fastapi
✅ sqlalchemy
✅ pydantic
✅ asyncio
✅ aiohttp
✅ pytest
✅ redis

Environment:
✅ .env file exists
✅ API keys configured

Directories:
✅ src/ directory
✅ data/ directory
✅ logs/ directory
✅ plugins/ directory
✅ tests/ directory

==================================================
🎉 All checks passed! MASB is ready to use.

Next steps:
1. Start web interface: python -m src.web.app
2. Visit: http://localhost:8080
```

### Test Your First Evaluation

```bash
# Quick test with minimal setup
python -c "
import asyncio
from src.evaluation_engine import EvaluationEngine

async def test_evaluation():
    try:
        engine = EvaluationEngine('gpt-3.5-turbo')
        print('✅ Evaluation engine initialized successfully')
        print('🎉 MASB is ready for evaluations!')
    except Exception as e:
        print(f'❌ Error: {e}')
        print('Check your API key configuration in .env file')

asyncio.run(test_evaluation())
"
```

### Web Interface Test

1. Start the web interface:
```bash
python -m src.web.app
```

2. Open your browser to: http://localhost:8080

3. You should see the MASB dashboard with:
   - System status indicators
   - Recent evaluation results (initially empty)
   - Navigation menu with Evaluate, Results, Analysis, etc.

## 🔧 Troubleshooting Installation

### Common Issues and Solutions

#### Issue: Python Version Error
```
Error: Python 3.8+ required, found 3.7
```
**Solution**: Install Python 3.8 or higher:
- **Ubuntu/Debian**: `sudo apt install python3.8`
- **macOS**: `brew install python@3.8`
- **Windows**: Download from python.org

#### Issue: Permission Denied
```
PermissionError: [Errno 13] Permission denied
```
**Solution**: Use virtual environment or user installation:
```bash
python -m venv masb-env
source masb-env/bin/activate  # or masb-env\Scripts\activate on Windows
pip install -r requirements.txt
```

#### Issue: Module Not Found
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: Ensure virtual environment is active and dependencies installed:
```bash
source masb-env/bin/activate  # Activate environment
pip install -r requirements.txt  # Install dependencies
```

#### Issue: Database Connection Error
```
sqlite3.OperationalError: unable to open database file
```
**Solution**: Create data directory and reinitialize:
```bash
mkdir -p data logs
python -m src.storage.database
```

#### Issue: Port Already in Use
```
OSError: [Errno 98] Address already in use
```
**Solution**: Change port or kill existing process:
```bash
# Change port in .env file
echo "WEB_PORT=8081" >> .env

# Or find and kill existing process
lsof -ti:8080 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8080  # Windows (note the PID and use Task Manager)
```

#### Issue: API Key Invalid
```
Error: Unauthorized - Invalid API key
```
**Solution**: Verify API key in .env file:
```bash
# Check if .env file exists and has correct format
cat .env | grep API_KEY

# Test API key directly
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: `tail -f logs/masb.log`
2. **Run diagnostics**: `python check_installation.py`
3. **Search existing issues**: [GitHub Issues](https://github.com/WolfgangDremmler/MASB/issues)
4. **Ask for help**: [GitHub Discussions](https://github.com/WolfgangDremmler/MASB/discussions)
5. **Contact support**: wolfgang.dremmler@example.com

## 📚 Next Steps

After successful installation:

1. **[Quick Start Tutorial](quick-start.md)** - Run your first evaluation
2. **[Web Interface Guide](web-interface.md)** - Learn the dashboard
3. **[Configuration Guide](configuration.md)** - Advanced configuration
4. **[API Documentation](api.md)** - Integrate with your systems

## 🔄 Updating MASB

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run database migrations
python -c "
from src.storage.database import db_manager
db_manager.run_migrations()
"

# Restart services
docker-compose restart  # if using Docker
# or restart Python processes
```

---

**Installation complete!** 🎉 You're ready to start evaluating AI model safety with MASB.

**Next**: [Quick Start Tutorial](quick-start.md) →