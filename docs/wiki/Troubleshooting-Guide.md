# Troubleshooting Guide

This guide helps you diagnose and fix common issues with MASB. If you can't find a solution here, check our [FAQ](FAQ) or [create an issue](https://github.com/WolfgangDremmler/MASB/issues).

## 🚨 Quick Diagnostics

### System Health Check
Run this first to identify problems:

```bash
# Check system status
python monitor_system.py --status

# Verify installation
python check_installation.py

# Test API connections
python test_apis.py
```

### Common Status Indicators

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| 🟢 Healthy | All systems operational | None |
| 🟡 Warning | Minor issues detected | Monitor closely |
| 🟠 Degraded | Reduced performance | Investigation needed |
| 🔴 Critical | System failure | Immediate action required |

## 🔧 Installation Issues

### Issue: Python Version Error
```bash
Error: Python 3.8+ required, found 3.7
```

**Solutions:**
```bash
# Check current version
python --version

# Install Python 3.8+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.8 python3.8-pip

# Install Python 3.8+ (macOS with Homebrew)
brew install python@3.8

# Install Python 3.8+ (Windows)
# Download from https://www.python.org/downloads/
```

### Issue: Module Import Errors
```bash
ModuleNotFoundError: No module named 'flask'
```

**Solutions:**
```bash
# Ensure virtual environment is activated
source masb-env/bin/activate  # Linux/macOS
masb-env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Force reinstall if corrupted
pip install --force-reinstall -r requirements.txt
```

### Issue: Permission Denied
```bash
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.8'
```

**Solutions:**
```bash
# Use virtual environment (recommended)
python -m venv masb-env
source masb-env/bin/activate
pip install -r requirements.txt

# Or install with user flag
pip install --user -r requirements.txt
```

## 🔑 API Configuration Issues

### Issue: Invalid API Key
```bash
Error: Unauthorized - Invalid API key
```

**Solutions:**
```bash
# Check .env file exists
ls -la .env

# Verify API key format
cat .env | grep API_KEY

# Test API key validity
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

**Common API Key Formats:**
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Cohere
COHERE_API_KEY=...

# Google
GOOGLE_API_KEY=...
```

### Issue: API Rate Limiting
```bash
Error: Rate limit exceeded
```

**Solutions:**
```bash
# Reduce concurrent requests in .env
CONCURRENT_REQUESTS=2
BATCH_SIZE=5

# Add delays between requests
REQUEST_DELAY=1.0

# Use different API keys for parallel evaluation
```

### Issue: API Timeout
```bash
Error: Request timeout after 60 seconds
```

**Solutions:**
```bash
# Increase timeout in .env
REQUEST_TIMEOUT=120
MAX_RETRIES=5

# Check network connectivity
ping api.openai.com

# Test with smaller prompts
python evaluate_model.py --max-prompts 1
```

## 💾 Database Issues

### Issue: Database Connection Failed
```bash
Error: sqlite3.OperationalError: database is locked
```

**Solutions:**
```bash
# Check if database file exists
ls -la data/masb.db

# Remove lock and reinitialize
rm -f data/masb.db-wal data/masb.db-shm
python -m src.storage.database

# Check disk space
df -h .
```

### Issue: Migration Errors
```bash
Error: (sqlite3.OperationalError) table already exists
```

**Solutions:**
```bash
# Reset database completely
rm -f data/masb.db
python -m src.storage.database

# Or run migrations manually
python -c "
from src.storage.database import db_manager
db_manager.run_migrations()
"
```

### Issue: Database Corruption
```bash
Error: database disk image is malformed
```

**Solutions:**
```bash
# Backup existing data
cp data/masb.db data/masb.db.backup

# Try to repair
sqlite3 data/masb.db ".recover" | sqlite3 data/masb_recovered.db
mv data/masb_recovered.db data/masb.db

# If repair fails, start fresh
rm data/masb.db
python -m src.storage.database
```

## 🌐 Web Interface Issues

### Issue: Web Interface Won't Start
```bash
Error: [Errno 98] Address already in use
```

**Solutions:**
```bash
# Check what's using port 8080
lsof -i :8080  # Linux/macOS
netstat -ano | findstr :8080  # Windows

# Kill conflicting process
kill -9 <PID>

# Or change port in .env
WEB_PORT=8081
```

### Issue: Web Interface Loads But Broken
```bash
# Browser shows blank page or errors
```

**Solutions:**
```bash
# Check browser console for JavaScript errors
# Press F12 → Console tab

# Clear browser cache
# Ctrl+Shift+Delete (Chrome/Firefox)

# Try different browser

# Check logs
tail -f logs/masb.log
```

### Issue: Static Files Not Loading
```bash
Error: 404 Not Found - /static/css/style.css
```

**Solutions:**
```bash
# Check static files exist
ls -la src/web/static/

# Restart web server
python -m src.web.app

# Clear browser cache and reload
```

## 🔌 Plugin Issues

### Issue: Plugin Not Loading
```bash
Warning: Plugin 'my_plugin' failed to load
```

**Solutions:**
```bash
# Check plugin syntax
python -m py_compile plugins/plugin_my_plugin.py

# Verify plugin structure
python manage_plugins.py --info my_plugin

# Check plugin configuration
cat plugins/plugins_config.json

# Enable plugin explicitly
python manage_plugins.py --enable my_plugin
```

### Issue: Plugin Import Errors
```bash
ModuleNotFoundError: No module named 'src.evaluators'
```

**Solutions:**
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Or add to plugin file
import sys
sys.path.append('/path/to/MASB')
```

### Issue: Plugin Configuration Errors
```bash
Error: Plugin configuration validation failed
```

**Solutions:**
```bash
# Check configuration schema
python manage_plugins.py --info plugin_name

# Validate configuration manually
python -c "
import json
with open('plugins/plugins_config.json') as f:
    config = json.load(f)
    print(json.dumps(config, indent=2))
"

# Reset plugin configuration
python manage_plugins.py --disable plugin_name
python manage_plugins.py --enable plugin_name
```

## 📊 Evaluation Issues

### Issue: Evaluation Fails Immediately
```bash
Error: No prompts found for language 'xx'
```

**Solutions:**
```bash
# Check available languages
python generate_datasets.py --list-languages

# Generate datasets for missing language
python generate_datasets.py --generate --languages xx

# Use existing language
python evaluate_model.py --model gpt-3.5-turbo --language en
```

### Issue: Evaluation Stalls/Hangs
```bash
# Evaluation starts but never completes
```

**Solutions:**
```bash
# Check system resources
python monitor_system.py --resources

# Reduce batch size
echo "BATCH_SIZE=1" >> .env

# Check API status
curl -I https://api.openai.com/v1/models

# Kill and restart evaluation
pkill -f "python.*evaluate"
```

### Issue: High Error Rate
```bash
Warning: Error rate: 50% (5/10 evaluations failed)
```

**Solutions:**
```bash
# Check error details in logs
tail -f logs/masb.log | grep ERROR

# Test with single prompt
python evaluate_model.py --max-prompts 1

# Verify model availability
python -c "
from src.models.provider_factory import ProviderFactory
provider = ProviderFactory.create_provider('gpt-3.5-turbo')
print('Provider created successfully')
"
```

## 💻 Performance Issues

### Issue: Slow Evaluation Speed
```bash
# Taking too long to complete evaluations
```

**Solutions:**
```bash
# Enable caching
echo "CACHE_ENABLED=true" >> .env

# Increase concurrency (carefully)
echo "CONCURRENT_REQUESTS=8" >> .env
echo "BATCH_SIZE=20" >> .env

# Check system resources
python monitor_system.py --status

# Use faster model for testing
python evaluate_model.py --model gpt-3.5-turbo  # instead of gpt-4
```

### Issue: High Memory Usage
```bash
Warning: Memory usage: 95%
```

**Solutions:**
```bash
# Reduce batch size
echo "BATCH_SIZE=5" >> .env

# Clear cache
redis-cli FLUSHALL  # if using Redis
rm -rf __pycache__

# Restart application
docker-compose restart  # or kill Python processes
```

### Issue: High CPU Usage
```bash
Warning: CPU usage: 90%
```

**Solutions:**
```bash
# Reduce concurrent requests
echo "CONCURRENT_REQUESTS=2" >> .env

# Check for runaway processes
top -p $(pgrep -f python)

# Scale horizontally if using Docker
docker-compose up --scale masb-worker=2
```

## 🐳 Docker Issues

### Issue: Docker Build Fails
```bash
Error: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**Solutions:**
```bash
# Clean Docker cache
docker system prune -a

# Build with no cache
docker-compose build --no-cache

# Check Dockerfile syntax
docker build --dry-run .

# Build step by step
docker build --target development .
```

### Issue: Container Won't Start
```bash
Error: container "masb-app" is unhealthy
```

**Solutions:**
```bash
# Check container logs
docker-compose logs masb-app

# Check container health
docker inspect masb-app | grep Health -A 10

# Debug container
docker-compose exec masb-app bash
```

### Issue: Volume Mount Problems
```bash
Error: bind source path does not exist
```

**Solutions:**
```bash
# Check volume paths in docker-compose.yml
cat docker-compose.yml | grep volumes -A 5

# Create missing directories
mkdir -p data logs plugins

# Fix permissions
chmod 755 data logs plugins
```

## 🔍 Debugging Tools

### Enable Debug Mode
```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start with verbose logging
python -m src.web.app --debug
```

### Log Analysis
```bash
# Watch logs in real-time
tail -f logs/masb.log

# Search for specific errors
grep -i error logs/masb.log

# Filter by timestamp
grep "2024-01-15" logs/masb.log
```

### Network Debugging
```bash
# Test API connectivity
curl -v https://api.openai.com/v1/models

# Check DNS resolution
nslookup api.openai.com

# Test local services
curl -v http://localhost:8080/health
```

## 📋 Support Information

When reporting issues, please include:

### System Information
```bash
# Generate system report
python -c "
import sys, platform, os
print(f'Python: {sys.version}')
print(f'OS: {platform.system()} {platform.release()}')
print(f'Architecture: {platform.machine()}')
print(f'MASB Directory: {os.getcwd()}')
"
```

### Error Details
- Full error message and stack trace
- Steps to reproduce the issue
- Configuration files (with API keys removed)
- Log files from the time of the error
- System resource usage during the issue

### Get Help
- 📖 **Wiki**: [Complete documentation](Home)
- 🐛 **Issues**: [Report bugs](https://github.com/WolfgangDremmler/MASB/issues)
- 💬 **Discussions**: [Ask questions](https://github.com/WolfgangDremmler/MASB/discussions)
- 📧 **Email**: wolfgang.dremmler@example.com

---

**Still having issues?** Don't hesitate to reach out - we're here to help! 🤝