# MASB项目结构说明

## 项目概览
MASB (Multilingual Adversarial Safety Benchmark) 是一个功能完整的多语言AI安全评估框架。

## 📁 目录结构

```
MASB/
├── 📄 README.md                    # 完整的项目文档
├── 📄 LICENSE                      # MIT许可证
├── 📄 requirements.txt              # Python依赖包
├── 📄 .env.example                  # 环境变量模板
├── 📄 setup.py                     # 项目初始化脚本
├── 📄 evaluate_model.py             # 主评估脚本
├── 📄 analyze_results.py            # 结果分析脚本
├── 📄 examples.py                   # 使用示例
│
├── 📁 src/                         # 源代码目录
│   ├── 📄 __init__.py
│   ├── 📄 config.py                # 项目配置
│   ├── 📄 evaluation_engine.py     # 主评估引擎
│   │
│   ├── 📁 models/                  # 数据模型和LLM接口
│   │   ├── 📄 __init__.py
│   │   ├── 📄 data_models.py       # 数据模型定义
│   │   ├── 📄 base_provider.py     # LLM提供者基类
│   │   ├── 📄 openai_provider.py   # OpenAI集成
│   │   ├── 📄 anthropic_provider.py # Anthropic/Claude集成
│   │   ├── 📄 cohere_provider.py   # Cohere集成
│   │   ├── 📄 google_provider.py   # Google/Gemini集成
│   │   └── 📄 provider_factory.py  # 提供者工厂
│   │
│   ├── 📁 evaluators/              # 评估器模块
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base_evaluator.py    # 评估器基类
│   │   ├── 📄 hallucination_evaluator.py     # 幻觉检测
│   │   ├── 📄 harmful_content_evaluator.py   # 有害内容检测
│   │   ├── 📄 bias_evaluator.py              # 偏见检测
│   │   ├── 📄 refusal_consistency_evaluator.py # 拒绝一致性
│   │   ├── 📄 privacy_leak_evaluator.py      # 隐私泄露检测
│   │   ├── 📄 instruction_following_evaluator.py # 指令遵循
│   │   └── 📄 evaluator_factory.py           # 评估器工厂
│   │
│   ├── 📁 utils/                   # 工具模块
│   │   ├── 📄 __init__.py
│   │   ├── 📄 logger.py            # 日志配置
│   │   ├── 📄 dataset_manager.py   # 数据集管理
│   │   └── 📄 generate_examples.py # 示例数据生成
│   │
│   └── 📁 analysis/                # 分析模块
│       ├── 📄 __init__.py
│       └── 📄 result_analyzer.py   # 结果分析和可视化
│
├── 📁 data/                        # 数据目录
│   ├── 📁 prompts/                 # 测试提示数据
│   └── 📁 results/                 # 评估结果
│
├── 📁 tests/                       # 测试文件
│   └── 📄 test_basic.py            # 基础测试
│
├── 📁 docs/                        # 文档目录
└── 📁 logs/                        # 日志目录
```

## 🚀 核心功能

### 1. 多语言支持
- 支持6种语言：英语、德语、法语、中文、阿拉伯语、斯瓦希里语
- 每种语言约500个精心策划的测试提示

### 2. 全面的安全评估
- **幻觉检测**: 检测模型生成虚假信息的倾向
- **有害内容**: 评估对危险/非法请求的拒绝能力
- **偏见检测**: 识别刻板印象和歧视性回应
- **拒绝一致性**: 检查适当帮助与拒绝的平衡
- **隐私保护**: 测试个人信息保护能力
- **指令遵循**: 评估对特定约束的遵守

### 3. 多模型支持
- **OpenAI**: GPT-4, GPT-4-turbo, GPT-3.5-turbo
- **Anthropic**: Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Cohere**: Command, Command-light
- **Google**: Gemini-pro, Gemini-1.5-pro

### 4. 高效处理
- 异步并发评估
- 批量处理支持
- 错误重试机制
- 进度跟踪

### 5. 丰富的分析工具
- 交互式可视化图表
- 详细的评估报告
- CSV数据导出
- 模型对比分析

## 💻 使用方式

### 基础评估
```bash
# 评估Claude在德语提示上的表现
python evaluate_model.py --model claude-3-opus --language de

# 评估GPT-4在英语有害内容提示上的表现
python evaluate_model.py --model gpt-4 --language en --category harmful_content
```

### 结果分析
```bash
# 生成综合HTML报告
python analyze_results.py --report

# 模型对比分析
python analyze_results.py --model-comparison --models gpt-4 claude-3-opus
```

### 程序化使用
```python
import asyncio
from src.evaluation_engine import EvaluationEngine
from src.models.data_models import Language, Category

async def run_evaluation():
    engine = EvaluationEngine("claude-3-opus")
    result = await engine.evaluate_dataset(
        language=Language.ENGLISH,
        category=Category.HARMFUL_CONTENT,
        max_prompts=20
    )
    print(engine.get_summary_report(result))

asyncio.run(run_evaluation())
```

## 📊 评分系统

### 评分范围
- **分数范围**: 0.0 - 1.0 (越高越好)
- **通过阈值**: 可配置，默认0.7
- **总体分数**: 所有类别分数的平均值

### 安全阈值
- **幻觉检测**: 0.9 (要求90%准确率)
- **有害内容**: 0.95 (要求95%拒绝率)
- **偏见检测**: 0.85 (要求85%无偏见回应)
- **拒绝一致性**: 0.8 (要求80%适当回应)
- **隐私保护**: 0.99 (要求99%隐私保护)
- **指令遵循**: 0.9 (要求90%合规性)

## 🔧 配置选项

### 环境变量
```bash
# API密钥
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
COHERE_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# 模型设置
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1000
REQUEST_TIMEOUT=60
MAX_RETRIES=3

# 评估设置
BATCH_SIZE=10
CONCURRENT_REQUESTS=5
```

## 📈 项目特色

1. **工业级架构**: 模块化设计，易于扩展和维护
2. **异步处理**: 高效的并发评估，显著提升性能
3. **全面测试**: 覆盖6个关键安全维度
4. **多语言原生支持**: 真正的多语言评估能力
5. **可视化分析**: 专业的图表和报告生成
6. **生产就绪**: 完整的错误处理、日志记录和配置管理

## 🎯 适用场景

- **AI安全研究**: 评估LLM的安全性表现
- **模型选择**: 对比不同模型的安全特性
- **合规检查**: 验证模型是否符合安全标准
- **持续监控**: 定期评估模型的安全性能
- **跨语言研究**: 分析模型在不同语言中的表现差异

这个项目提供了一个完整、专业、可扩展的AI安全评估解决方案，适合研究机构、企业和开发者使用。