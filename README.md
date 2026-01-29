# 油价新闻分析系统

## 项目结构

```
textanalysis/
├── main.py                    # 主程序入口（分析流程）
├── generate_report.py         # 独立报告生成脚本
├── config.py                  # 配置文件
├── crawler.py                 # 网页爬虫
├── data_loader.py             # 数据加载器
├── llm_client.py              # LLM客户端（支持重试+JSON校验）
│
├── agents/                    # Agent模块
│   ├── base_agent.py          # Agent基类
│   ├── text_factor_classifier.py  # Agent1: 事件分类
│   ├── iea_analyzer.py        # Agent2: IEA分析
│   ├── sentiment_scorer.py    # Agent3: 情绪量化
│   └── factor_validator.py    # Agent4: 因果验证
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

- Agent1: EventClassifier（事件分类器）
  - 判断新闻是否与油价相关，识别事件类型（8类）。

- Agent2: IEA Analyzer（IEA 实体分析器）
  - 提取供需金三要素实体、量化指标、传导路径。

- Agent3: SentimentIntensityScorer（情绪强度评分器）
  - 量化事件的情绪极性、冲击强度、置信度。

- Agent4: CausalValidator（因果验证器）
  - 验证"相关≠因果"，校准强度评分。

## 快速开始

### 1. 安装依赖

```bash
pip install pandas requests beautifulsoup4 sqlalchemy
```

### 2. 配置

编辑 `config.py` 或设置环境变量：

```python
LLM_API_KEY = "your-api-key"
LLM_BASE_URL = "https://api.deepseek.com/v1"
LLM_MODEL = "deepseek-chat"
```

### 3. 准备数据

在 `data/input.csv` 中准备新闻：

```csv
id,title,date,category,url
1,OPEC+宣布减产,2024-01-15,geopolitical,https://...
```

### 4. 运行分析

```bash
python main.py
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

## 配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_PATH` | 数据库路径 | `data/text_factor.db` |
| `REPORT_OUTPUT_DIR` | 报告输出目录 | `output/reports` |
| `CLASSIFY_CONFIDENCE_THRESHOLD` | 分类置信度阈值 | 0.6 |
| `SIMILAR_EVENTS_DAYS` | 查询历史事件天数 | 30 |
| `SIMILAR_EVENTS_LIMIT` | 返回同类事件数量 | 5 |
| `MAX_CONTENT_LENGTH` | LLM 最大内容长度 | 1000000 |
| `PARALLEL_ENABLED` | 是否启用并行处理 | `True` |
| `MAX_WORKERS` | 最大并行线程数 | 5 |


## 其它问题

### Q: 如何查看数据库中的数据？

```python
from database import EventRepository

repo = EventRepository()
events = repo.get_all(limit=10)
for event in events:
    print(event['title'], event.get('intensity'))
```


## 许可证

MIT License
