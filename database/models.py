# database/models.py
"""
数据库模型定义
仅保存文本因子相关的数据结构
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    JSON,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class TextFactorEvent(Base):
    """文本因子事件表。"""

    __tablename__ = "text_factor_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 新闻基础信息
    news_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(512), nullable=False)
    url = Column(String(1024))
    source_category = Column(String(64), index=True)
    event_date = Column(DateTime, index=True)

    # Agent1: 关联性与分类
    is_oil_related = Column(Boolean, default=False, index=True)
    factor_category = Column(String(64), index=True)
    classify_confidence = Column(Float, default=0.0)
    classify_reason = Column(Text)
    keywords_found = Column(JSON)

    # Agent2: 因子量化
    factor_value = Column(Float, default=0.0)
    impact_magnitude = Column(String(16))
    time_horizon = Column(String(16))
    quantification_logic = Column(Text)

    # Agent3: 因子校验
    is_valid = Column(Boolean, default=True)
    adjusted_factor_value = Column(Float, default=0.0)
    adjustment_reason = Column(Text)
    historical_consistency = Column(Text)

    # 原始数据
    raw_content = Column(Text)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TextFactorEvent(id={self.id}, title='{self.title[:30]}...', value={self.adjusted_factor_value})>"

    def to_dict(self) -> dict:
        """转换为字典。"""
        return {
            "id": self.id,
            "news_id": self.news_id,
            "title": self.title,
            "url": self.url,
            "source_category": self.source_category,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "is_oil_related": self.is_oil_related,
            "factor_category": self.factor_category,
            "classify_confidence": self.classify_confidence,
            "classify_reason": self.classify_reason,
            "keywords_found": self.keywords_found,
            "factor_value": self.factor_value,
            "adjusted_factor_value": self.adjusted_factor_value,
            "impact_magnitude": self.impact_magnitude,
            "time_horizon": self.time_horizon,
            "quantification_logic": self.quantification_logic,
            "is_valid": self.is_valid,
            "adjustment_reason": self.adjustment_reason,
            "historical_consistency": self.historical_consistency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DailyFactorSummary(Base):
    """日度因子汇总表。"""

    __tablename__ = "daily_factor_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_date = Column(DateTime, unique=True, nullable=False, index=True)
    total_events = Column(Integer, default=0)
    oil_related_events = Column(Integer, default=0)
    avg_factor_value = Column(Float, default=0.0)
    factor_category_counts = Column(JSON)
    summary_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DailyFactorSummary(date={self.summary_date}, avg={self.avg_factor_value})>"

    def to_dict(self) -> dict:
        """转换为字典。"""
        return {
            "id": self.id,
            "summary_date": self.summary_date.isoformat() if self.summary_date else None,
            "total_events": self.total_events,
            "oil_related_events": self.oil_related_events,
            "avg_factor_value": self.avg_factor_value,
            "factor_category_counts": self.factor_category_counts,
            "summary_text": self.summary_text,
        }


def init_database(db_path: str = "data/text_factor.db"):
    """初始化数据库连接与表结构。"""
    # 使用 check_same_thread=False 支持多线程访问 SQLite
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
