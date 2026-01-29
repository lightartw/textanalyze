# agents/__init__.py
from .base_agent import BaseAgent, AgentResult
from .text_factor_classifier import EventClassifier
from .iea_analyzer import IEAAnalyzer
from .sentiment_scorer import SentimentIntensityScorer
from .factor_validator import CausalValidator

__all__ = [
    "BaseAgent",
    "AgentResult",
    "EventClassifier",           # Agent1: 事件分类
    "IEAAnalyzer",               # Agent2: IEA实体分析
    "SentimentIntensityScorer",  # Agent3: 情绪量化
    "CausalValidator",           # Agent4: 因果验证
]
