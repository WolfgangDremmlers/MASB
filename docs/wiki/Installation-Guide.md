# Installation Guide

This guide will walk you through installing and setting up MASB on your system.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: At least 2GB free space
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)

### Required API Keys
MASB requires API keys for the AI models you want to evaluate:

- **OpenAI API Key** (for GPT models)
- **Anthropic API Key** (for Claude models)  
- **Cohere API Key** (for Command models)
- **Google API Key** (for Gemini models)

## 🚀 Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB

# Install with automatic setup
python install.py --quick-setup
```

### Method 2: Manual Installation

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

#### Step 4: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
nano .env  # or use your preferred editor
```

#### Step 5: Initialize Database
```bash
# Initialize SQLite database
python -m src.storage.database
```

#### Step 6: Verify Installation
```bash
# Run system check
python check_installation.py

# Start web interface
python -m src.web.app
```

### Method 3: Docker Installation

#### Prerequisites
- Docker 20.0+
- Docker Compose 2.0+

#### Quick Docker Setup
```bash
# Clone repository
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

#### Access Services
- **Web Interface**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Monitoring Dashboard**: http://localhost:8080/monitoring

## ⚙️ Configuration

### Environment Variables

Edit your `.env` file with the following configuration:

```bash
# API Keys (Required)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Model Configuration
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1000
REQUEST_TIMEOUT=60
MAX_RETRIES=3

# Performance Settings
BATCH_SIZE=10
CONCURRENT_REQUESTS=5
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# Database
DATABASE_URL=sqlite:///./data/masb.db

# Plugin System
ENABLE_PLUGINS=true
PLUGIN_AUTO_LOAD=true

# Monitoring
ENABLE_PERFORMANCE_MONITORING=true
RESOURCE_MONITORING_INTERVAL=1.0

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=8080
SECRET_KEY=your-secret-key-here
```

### Directory Structure

After installation, your directory should look like this:

```
MASB/
├── src/                    # Source code
├── plugins/               # Plugin directory
├── tests/                 # Test files
├── data/                  # Data directory
├── logs/                  # Log files
├── docs/                  # Documentation
├── .env                   # Environment configuration
├── requirements.txt       # Python dependencies
└── docker-compose.yml     # Docker configuration
```

## 🧪 Verification

### Test Installation

```bash
# Run system diagnostics
python check_installation.py

# Test API connections
python test_apis.py

# Run basic evaluation
python -c "
import asyncio
from src.evaluation_engine import EvaluationEngine

async def test():
    engine = EvaluationEngine('gpt-3.5-turbo')
    print('✅ MASB installation successful!')

asyncio.run(test())
"
```

### Expected Output
```
✅ System check passed
✅ Dependencies installed
✅ Database initialized
✅ API keys configured
✅ Web interface accessible
✅ MASB installation successful!
```

## 🔧 Troubleshooting

### Common Issues

#### Issue: Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Ensure virtual environment is activated
source masb-env/bin/activate  # or masb-env\Scripts\activate on Windows
pip install -r requirements.txt
```

#### Issue: API Key Errors
```bash
# Error: Invalid API key
# Solution: Check your .env file
cat .env | grep API_KEY
# Ensure keys are valid and have proper permissions
```

#### Issue: Database Errors
```bash
# Error: Database connection failed
# Solution: Reinitialize database
rm -f data/masb.db
python -m src.storage.database
```

#### Issue: Port Already in Use
```bash
# Error: Port 8080 already in use
# Solution: Change port in .env file
echo "WEB_PORT=8081" >> .env
```

### System Check Script

Create a `check_installation.py` file to verify everything is working:

```python
#!/usr/bin/env python3
"""Installation verification script for MASB."""

import sys
import os
from pathlib import Path
import importlib

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check required dependencies."""
    required = [
        'flask', 'fastapi', 'sqlalchemy', 'pydantic', 
        'asyncio', 'aiohttp', 'pytest', 'redis'
    ]
    
    missing = []
    for package in required:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    return len(missing) == 0

def check_environment():
    """Check environment configuration."""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    print("✅ .env file exists")
    
    # Check for at least one API key
    with open(env_file) as f:
        content = f.read()
        if 'API_KEY=' in content:
            print("✅ API keys configured")
            return True
    
    print("⚠️  No API keys found in .env")
    return False

def check_directories():
    """Check required directories."""
    required_dirs = ['src', 'data', 'logs', 'plugins', 'tests']
    
    for directory in required_dirs:
        path = Path(directory)
        if path.exists():
            print(f"✅ {directory}/ directory")
        else:
            print(f"❌ {directory}/ directory missing")
            return False
    
    return True

def main():
    """Run all checks."""
    print("🔍 MASB Installation Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment", check_environment),
        ("Directories", check_directories),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n{name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! MASB is ready to use.")
        print("\nNext steps:")
        print("1. Start web interface: python -m src.web.app")
        print("2. Visit: http://localhost:8080")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## 📚 Next Steps

After successful installation:

1. **Read the [Quick Start Tutorial](Quick-Start-Tutorial)** to run your first evaluation
2. **Explore the [Web Interface Guide](Web-Interface-Guide)** to use the dashboard
3. **Check out [Configuration Guide](Configuration-Guide)** for advanced setup
4. **Visit [Plugin Development](Creating-Custom-Evaluators)** to create custom evaluators

## 🆘 Getting Help

If you encounter issues during installation:

- Check the [Troubleshooting Guide](Troubleshooting-Guide)
- Search [GitHub Issues](https://github.com/WolfgangDremmler/MASB/issues)
- Ask questions in [GitHub Discussions](https://github.com/WolfgangDremmler/MASB/discussions)
- Contact support: wolfgang.dremmler@example.com

---

**Next**: [Quick Start Tutorial](Quick-Start-Tutorial) →