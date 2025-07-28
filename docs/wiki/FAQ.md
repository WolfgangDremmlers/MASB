# Frequently Asked Questions (FAQ)

This page answers the most common questions about MASB. Can't find what you're looking for? Check our [GitHub Discussions](https://github.com/WolfgangDremmler/MASB/discussions) or [create an issue](https://github.com/WolfgangDremmler/MASB/issues).

## 🚀 Getting Started

### Q: What is MASB?
**A:** MASB (Multilingual Adversarial Safety Benchmark) is an enterprise-ready framework for evaluating AI model safety across multiple languages and categories. It systematically tests for hallucination, harmful content, bias, privacy leaks, and instruction following consistency.

### Q: What makes MASB different from other evaluation tools?
**A:** MASB offers:
- **50+ Language Support**: Most comprehensive multilingual evaluation
- **Plugin System**: Extensible architecture for custom evaluators
- **Enterprise Features**: Web interface, monitoring, database storage
- **Production Ready**: Docker deployment, CI/CD, comprehensive testing

### Q: Do I need programming experience to use MASB?
**A:** No! MASB provides:
- **Web Interface**: Point-and-click evaluation without coding
- **CLI Tools**: Simple command-line interfaces
- **Pre-built Evaluators**: Ready-to-use safety evaluators
- **Documentation**: Comprehensive guides for all skill levels

## 🔧 Installation & Setup

### Q: What are the system requirements?
**A:** Minimum requirements:
- Python 3.8+
- 4GB RAM (8GB+ recommended)
- 2GB free storage
- Internet connection for API calls

### Q: Which API keys do I need?
**A:** You need at least one:
- **OpenAI** (for GPT models): Most popular choice
- **Anthropic** (for Claude models): Great safety focus
- **Cohere** (for Command models): Good for enterprise
- **Google** (for Gemini models): Latest technology

### Q: Can I run MASB without API keys?
**A:** No, MASB requires API access to language models for evaluation. However, you can:
- Use the demo mode with mock responses
- Develop and test plugins without API calls
- Analyze existing evaluation results

### Q: How much do API calls cost?
**A:** Costs vary by provider and model:
- **OpenAI GPT-3.5**: ~$0.002 per 1K tokens
- **OpenAI GPT-4**: ~$0.03 per 1K tokens  
- **Anthropic Claude**: ~$0.008 per 1K tokens
- **Typical evaluation**: $0.10-$5.00 depending on model and prompt count

### Q: Can I use local/offline models?
**A:** Currently, MASB focuses on API-based models, but we're working on:
- Local model integration (Ollama, Hugging Face)
- Offline evaluation capabilities
- Custom model providers

## 🌍 Multi-language Support

### Q: How many languages does MASB support?
**A:** MASB supports 50+ languages with varying levels of AI model support:
- **Excellent Support**: English, Chinese, French, Spanish, German, Japanese
- **Good Support**: Russian, Portuguese, Italian, Hindi, Dutch, Swedish
- **Growing Support**: Many more languages being added regularly

### Q: How do I add a new language?
**A:** Follow these steps:
1. Add language definition in `src/localization/languages.py`
2. Create prompt templates for the language
3. Add localization strings for the UI
4. Test with `python generate_datasets.py --languages your_language`

### Q: Are the evaluations culturally appropriate?
**A:** Yes! MASB includes:
- **Cultural Context**: Language-specific bias and safety considerations
- **Native Speakers**: Prompt templates reviewed by native speakers
- **Regional Variations**: Support for different cultural contexts
- **Continuous Improvement**: Community feedback incorporation

## 📊 Evaluation & Results

### Q: What safety categories does MASB evaluate?
**A:** MASB evaluates six core categories:
1. **Harmful Content**: Refusal of dangerous/illegal requests
2. **Hallucination**: Factual accuracy and truthfulness
3. **Bias**: Fair treatment across different groups
4. **Privacy Leak**: Protection of personal information
5. **Refusal Consistency**: Appropriate help vs. refusal balance
6. **Instruction Following**: Adherence to given constraints

### Q: How are scores calculated?
**A:** Scores are calculated using:
- **Range**: 0.0 to 1.0 (higher is better)
- **Aggregation**: Category-specific algorithms
- **Confidence**: Statistical confidence measures
- **Thresholds**: Configurable pass/fail thresholds

### Q: How many prompts should I use for evaluation?
**A:** Recommendations by use case:
- **Quick Test**: 10-20 prompts per category
- **Development**: 50-100 prompts per category
- **Production**: 200+ prompts per category
- **Research**: 500+ prompts per category

### Q: How do I interpret the results?
**A:** Key metrics to understand:
- **Overall Score**: Average across all categories
- **Pass Rate**: Percentage meeting safety thresholds
- **Category Breakdown**: Performance in specific areas
- **Confidence Intervals**: Statistical reliability measures

## 🔌 Plugin System

### Q: What are plugins in MASB?
**A:** Plugins are custom evaluators that extend MASB's capabilities:
- **Custom Logic**: Your own evaluation algorithms
- **Specialized Domains**: Industry-specific safety checks
- **Integration**: Third-party safety tools
- **Flexibility**: Enable/disable without system restart

### Q: How do I create a custom plugin?
**A:** Simple process:
1. Generate template: `python manage_plugins.py --create my_evaluator`
2. Implement evaluation logic in the generated file
3. Configure plugin settings in JSON
4. Test: `python manage_plugins.py --test my_evaluator`

### Q: Can plugins access external services?
**A:** Yes! Plugins can:
- Make HTTP requests to external APIs
- Access databases and file systems
- Use machine learning models
- Integrate with enterprise security tools

### Q: Are there example plugins available?
**A:** Yes, MASB includes several example plugins:
- **Sentiment Evaluator**: Sentiment-based safety scoring
- **Keyword Evaluator**: Pattern-based content detection
- **Length Evaluator**: Response length analysis
- **Community Plugins**: Growing ecosystem of user contributions

## 🖥️ Web Interface

### Q: Do I need to use the web interface?
**A:** No, but it provides significant benefits:
- **User-Friendly**: No command-line knowledge required
- **Real-time Monitoring**: Live evaluation progress
- **Visualization**: Charts and graphs for results
- **Management**: Easy plugin and configuration management

### Q: Can multiple users access the web interface?
**A:** Currently, MASB is designed for single-user or team use. Enterprise features planned:
- User authentication and authorization
- Role-based access control
- Multi-tenant deployment
- Audit logging

### Q: Is the web interface mobile-friendly?
**A:** Yes! The interface is responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Various screen sizes and orientations

## 🚀 Deployment & Scaling

### Q: Can I deploy MASB in production?
**A:** Absolutely! MASB is production-ready with:
- **Docker Support**: Containerized deployment
- **Kubernetes**: Orchestration and scaling
- **Monitoring**: Health checks and metrics
- **CI/CD**: Automated testing and deployment

### Q: How do I scale MASB for large evaluations?
**A:** MASB supports horizontal scaling:
- **Docker Compose**: Scale worker containers
- **Kubernetes**: Auto-scaling based on load
- **Configuration**: Adjust concurrency and batch sizes
- **Caching**: Redis caching for performance

### Q: What about security?
**A:** MASB includes security features:
- **API Key Protection**: Encrypted storage
- **Input Validation**: Protection against malicious inputs
- **Access Control**: Configurable permissions
- **Audit Logging**: Track all system activities

## 🛠️ Development & Contributing

### Q: How can I contribute to MASB?
**A:** We welcome contributions:
1. **Issues**: Report bugs or request features
2. **Code**: Submit pull requests with improvements
3. **Documentation**: Improve guides and examples
4. **Testing**: Help test new features
5. **Community**: Answer questions and help other users

### Q: What's the development roadmap?
**A:** Key upcoming features:
- **Local Model Support**: Ollama, Hugging Face integration
- **Advanced Analytics**: ML-based result analysis
- **Enterprise Features**: SSO, RBAC, audit logs
- **API Expansion**: More comprehensive REST APIs

### Q: How do I set up a development environment?
**A:** Follow these steps:
```bash
git clone https://github.com/WolfgangDremmler/MASB.git
cd MASB
pip install -r requirements-dev.txt
pre-commit install
python -m pytest tests/
```

## 🐛 Troubleshooting

### Q: MASB won't start - what should I check?
**A:** Common issues and solutions:
1. **Python Version**: Ensure Python 3.8+
2. **Dependencies**: Run `pip install -r requirements.txt`
3. **API Keys**: Check `.env` file configuration
4. **Ports**: Ensure port 8080 is available
5. **Permissions**: Check file and directory permissions

### Q: Evaluations are failing - what's wrong?
**A:** Check these common causes:
- **API Credits**: Ensure sufficient API credits
- **Rate Limits**: Reduce concurrent requests
- **Network**: Check internet connectivity
- **Model Availability**: Verify model access permissions

### Q: The web interface is slow - how can I improve performance?
**A:** Performance optimization tips:
- **Enable Caching**: Set `CACHE_ENABLED=true`
- **Reduce Batch Size**: Lower `BATCH_SIZE` setting
- **Increase Resources**: More CPU/RAM for the system
- **Database Optimization**: Use faster storage for database

### Q: How do I reset MASB to default settings?
**A:** Reset procedures:
```bash
# Reset database
rm -f data/masb.db
python -m src.storage.database

# Reset configuration
cp .env.example .env
# Edit .env with your settings

# Reset plugins
rm -f plugins/plugins_config.json
python manage_plugins.py --reload
```

## 📊 API & Integration

### Q: Does MASB have a REST API?
**A:** Yes! MASB provides comprehensive REST APIs:
- **Evaluation API**: Start and monitor evaluations
- **Results API**: Query and export results
- **Plugin API**: Manage plugins programmatically
- **Monitoring API**: Access system metrics

### Q: Can I integrate MASB with CI/CD pipelines?
**A:** Absolutely! MASB supports automation:
- **CLI Tools**: Command-line interfaces for scripts
- **Exit Codes**: Proper exit codes for pipeline integration
- **JSON Output**: Machine-readable result formats
- **Webhooks**: Notifications for evaluation completion

### Q: How do I export results for analysis?
**A:** Multiple export options:
- **Web Interface**: Download CSV/JSON from dashboard
- **CLI Tools**: `python analyze_results.py --export-csv`
- **API**: REST endpoints for programmatic access
- **Database**: Direct SQLite database access

## 💡 Best Practices

### Q: How often should I run evaluations?
**A:** Recommended schedules:
- **Development**: Before each model deployment
- **Staging**: Daily automated evaluations
- **Production**: Weekly comprehensive evaluations
- **Critical Changes**: Immediate evaluation before release

### Q: What's the best way to organize evaluations?
**A:** Organization strategies:
- **By Model**: Separate evaluations for each model version
- **By Language**: Language-specific evaluation campaigns
- **By Category**: Focus on specific safety categories
- **By Environment**: Development vs. production evaluations

### Q: How do I ensure evaluation quality?
**A:** Quality assurance tips:
- **Sufficient Samples**: Use adequate prompt counts
- **Multiple Languages**: Test across diverse languages
- **Regular Updates**: Keep prompts and evaluators current
- **Review Results**: Manual review of concerning results

---

## 🆘 Still Need Help?

Can't find the answer you're looking for?

- 📖 **Documentation**: Browse the complete [Wiki](Home)
- 🐛 **Bug Reports**: [Create an issue](https://github.com/WolfgangDremmler/MASB/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/WolfgangDremmler/MASB/discussions)
- 📧 **Direct Contact**: wolfgang.dremmler@example.com

---

**Last Updated**: January 2024  
**Contributing**: Help improve this FAQ by [editing on GitHub](https://github.com/WolfgangDremmler/MASB/edit/main/docs/wiki/FAQ.md)