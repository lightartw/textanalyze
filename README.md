# 国际油价因子风险分析系统

## 项目简介

这是一个基于大语言模型（LLM）的国际油价因子风险分析系统，通过四个专业Agent组件对新闻事件进行深度分析，评估其对油价的潜在影响。

## 项目结构

```
textanalyze/
├── main.py                    # 主程序入口（分析流程）
├── generate_report.py         # 独立报告生成脚本
├── config.py                  # 配置文件
├── crawler.py                 # 网页爬虫
├── data_loader.py             # 数据加载器
├── llm_client.py              # LLM客户端（支持重试+JSON校验）
├── clear_database.py          # 数据库清理脚本
│
├── agents/                    # Agent模块
│   ├── base_agent.py          # Agent基类
│   ├── text_factor_classifier.py  # Agent1: 事件分类
│   ├── iea_analyzer.py        # Agent2: IEA分析
│   ├── sentiment_scorer.py    # Agent3: 情绪量化
│   └── factor_validator.py    # Agent4: 因果验证
│   ├── prompt/                # Agent提示词目录
│       ├── text_factor_classifier/  # 事件分类提示词
│       ├── sentiment_scorer/        # 情绪评分提示词
│       ├── iea_analyzer/            # IEA分析提示词
│       └── factor_validator/        # 因果验证提示词
│
├── database/                  # 数据库模块（通用JSON存储）
│   ├── models.py              # EventRecord模型
│   └── repository.py          # 数据库操作接口
│
├── workflow/                  # 工作流引擎
│   ├── nodes.py               # 工作流节点定义
│   └── pipeline.py            # 流水线管理
│
├── services/                  # 报告服务（从DB读取）
│   ├── factor_aggregator.py  # 统计聚合
│   └── report_generator.py   # 报告生成
│
├── factor_interface/          # 事件类型定义
│   └── factor_schema.py       # 8类事件类型常量
│
├── data/
│   ├── input.csv              # 输入数据
│   ├── test_input.csv         # 测试输入数据
│   └── text_factor.db         # SQLite数据库
│
└── output/
    └── reports/               # 报告输出目录
```

---

## 架构设计

### 分析与报告解耦

```
新闻数据 → 4-Agent分析 → 数据库（单一数据源）
                              ↓
                       报告模块（随时可生成）
```

## Agent 说明

- **Agent1: EventClassifier（事件分类器）**
  - 判断新闻是否与油价相关，识别事件类型（8类）
  - 提取关键实体和关键词
  - 支持多语言新闻分析

- **Agent2: IEAAnalyzer（IEA 实体分析器）**
  - 提取供需金三要素实体、量化指标、传导路径
  - 分析事件对供应链的影响
  - 评估市场信心和不确定性

- **Agent3: SentimentIntensityScorer（情绪强度评分器）**
  - 量化事件的情绪极性（-1到1）
  - 评估冲击强度（0到1）
  - 计算分析置信度（0到1）

- **Agent4: CausalValidator（因果验证器）**
  - 验证"相关≠因果"，校准强度评分
  - 分析传导路径的完整性
  - 识别混杂变量和历史一致性

## 快速开始

### 1. 安装依赖

```bash
# 使用系统Python环境
python -m pip install pandas requests beautifulsoup4 sqlalchemy

# 或使用特定Python环境
D:/PYTHON/python.exe -m pip install pandas requests beautifulsoup4 sqlalchemy
```

### 2. 配置

编辑 `config.py` 或设置环境变量：

#### 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_API_KEY` | LLM API密钥 | 从环境变量获取 |
| `LLM_BASE_URL` | LLM API基础URL | 支持多个LLM服务 |
| `LLM_MODEL` | LLM模型名称 | 支持多种模型 |
| `DATABASE_PATH` | 数据库路径 | `data/text_factor.db` |
| `REPORT_OUTPUT_DIR` | 报告输出目录 | `output/reports` |
| `CLASSIFY_CONFIDENCE_THRESHOLD` | 分类置信度阈值 | 0.6 |
| `SIMILAR_EVENTS_DAYS` | 查询历史事件天数 | 30 |
| `SIMILAR_EVENTS_LIMIT` | 返回同类事件数量 | 5 |
| `MAX_CONTENT_LENGTH` | LLM 最大内容长度 | 1000000 |
| `PARALLEL_ENABLED` | 是否启用并行处理 | `True` |
| `MAX_WORKERS` | 最大并行线程数 | 5 |

#### 支持的LLM配置

##### DeepSeek
```python
LLM_API_KEY = "your-deepseek-api-key"
LLM_BASE_URL = "https://api.deepseek.com/v1"
LLM_MODEL = "deepseek-chat"
```

##### 豆包
```python
LLM_API_KEY = "your-doubao-api-key"
LLM_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
LLM_MODEL = "ep-xxxxxx"  # 模型部署ID
```

##### Qwen3-plus (DashScope)
```python
LLM_API_KEY = "your-dashscope-api-key"
LLM_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
LLM_MODEL = "qwen3-plus"
```

### 3. 准备数据

在 `data/input.csv` 中准备新闻：

```csv
id,title,date,category,url
1,Saudi Arabia announces surprise oil production cut,2026-01-28,oil,https://example.com/saudi-cut
2,US Federal Reserve raises interest rates,2026-01-27,finance,https://example.com/fed-rate-hike
```

### 4. 运行分析

```bash
# 使用系统Python环境
python main.py

# 或使用特定Python环境
D:/PYTHON/python.exe main.py
```

**功能**：
- 分析所有新闻
- 保存到数据库
- 自动生成报告

### 5. 生成报告（独立）

```bash
# 生成所有报告
python generate_report.py

# 只生成详细报告
python generate_report.py --type detailed

# 只统计油价相关事件
python generate_report.py --oil-only

# 生成特定类型事件报告
python generate_report.py --event-type geopolitical
```

### 6. 数据库管理

```bash
# 清理数据库历史记录
python clear_database.py
```

## 数据库结构
- EventRecord 表（通用 JSON 存储）

```
├── id              (Integer, 主键)
├── news_id         (String, 唯一索引) ← 快速查询
├── event_date      (DateTime, 索引)   ← 按时间查询
├── is_oil_related  (Boolean, 索引)    ← 按相关性过滤
├── event_type      (String, 索引)     ← 按类型分组
├── data            (JSON)             ← 存储完整工作流输出
├── created_at      (DateTime)
└── updated_at      (DateTime)
```

## 报告输出

分析完成后，报告将保存在 `output/reports/` 目录中，文件名格式为 `results_YYYYMMDD_HHMMSS.json`。

报告包含以下信息：
- 事件分类结果
- IEA分析详情
- 情绪极性和冲击强度评分
- 因果验证结果
- 详细的推理过程

## 故障排除

### 常见问题

1. **ModuleNotFoundError: No module named 'pandas'**
   - 解决方案：安装依赖项 `pip install pandas`

2. **LLM API调用失败**
   - 解决方案：检查API密钥是否正确，确保网络连接正常

3. **数据库连接失败**
   - 解决方案：确保SQLite数据库文件存在且可写

4. **爬虫404错误**
   - 解决方案：系统会自动使用标题作为内容，无需手动干预

### 调试模式

```bash
# 启用详细日志
python main.py --verbose

# 禁用并行处理（便于调试）
# 修改config.py中的PARALLEL_ENABLED = False
```

## 高级功能

### 自定义Agent提示词

您可以在 `agents/prompt/` 目录下修改各个Agent的提示词，以适应不同的分析场景。

### 扩展支持的事件类型

在 `factor_interface/factor_schema.py` 中添加新的事件类型定义。

### 集成新的LLM服务

在 `config.py` 中添加新的LLM服务配置，并确保 `llm_client.py` 支持该服务的API格式。

## 性能优化

- **并行处理**：默认启用5线程并行处理，可根据系统性能调整
- **缓存机制**：系统会缓存LLM响应，减少重复调用
- **错误处理**：完善的错误处理机制，确保系统稳定性

## 未来计划

- [ ] 加强爬虫能力，支持更多新闻源
- [ ] 增加实时数据集成
- [ ] 开发Web界面，提供可视化分析结果
- [ ] 支持更多语言的新闻分析
- [ ] 增加历史数据分析和预测功能

## 贡献指南

欢迎提交Issue和Pull Request，帮助改进这个项目。

## 许可证

本项目采用MIT许可证。
