# config.py
"""
项目配置文件
专用于LLM文本因子分析流程
"""
import os

# === 文件路径配置 ===
INPUT_FILE = "data/input.csv"
OUTPUT_DIR = "output"
FACTOR_OUTPUT_DIR = "output/factors"
REPORT_OUTPUT_DIR = "output/reports"

# === 数据库配置 ===
DATABASE_PATH = "data/text_factor.db"

# === 爬虫配置 ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
REQUEST_TIMEOUT = 10  # 秒

# === LLM 配置 ===
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-xxxxxxxxxxxxxxxxxx")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_TEMPERATURE = 0.2
LLM_TIMEOUT = 60  # 秒

# === Agent 配置 ===
CLASSIFY_CONFIDENCE_THRESHOLD = 0.6  # 分类置信度阈值
MAX_CONTENT_LENGTH = 1000000  # 发送给LLM的最大内容长度
SIMILAR_EVENTS_DAYS = 30  # 查询历史同类事件的天数
SIMILAR_EVENTS_LIMIT = 5  # 返回的同类事件数量

# === 因子配置 ===
FACTOR_VALUE_MIN = -1.0
FACTOR_VALUE_MAX = 1.0
FACTOR_FREQUENCY = "D"  # 因子频率: D(日) / M(月)

# === 工作流配置 ===
WORKFLOW_RETRY_COUNT = 2  # 节点失败重试次数

# === 并行处理配置 ===
MAX_WORKERS = 5  # 并行处理的最大线程数
PARALLEL_ENABLED = True  # 是否启用并行处理