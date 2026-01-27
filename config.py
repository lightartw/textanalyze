# config.py
import os

# === 文件路径配置 ===
INPUT_FILE = "data/input.csv"
OUTPUT_FILE = "output/analysis_result.csv" 

# === 爬虫配置 ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
REQUEST_TIMEOUT = 10  # 秒

# === LLM 配置 ===
LLM_API_KEY = "sk-dc31a90804d34975a78a244912d4d4f5"  
LLM_BASE_URL = "https://api.deepseek.com/v1"
LLM_MODEL = "deepseek-chat"

# 每个类别新闻数量限制
MAX_NEWS_PER_CATEGORY = 5

# === 并发配置 ===
MAX_WORKERS = 5 