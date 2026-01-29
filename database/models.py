# database/models.py
"""
数据库模型定义
不绑定具体业务字段，使用JSON存储完整数据
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    JSON,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class EventRecord(Base):
    """
    事件记录表 - 通用存储。
    
    使用JSON字段存储完整的工作流输出，不绑定具体字段。
    """
    __tablename__ = "event_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基础索引字段（用于查询）
    news_id = Column(String(64), unique=True, nullable=False, index=True)
    event_date = Column(DateTime, index=True)
    is_oil_related = Column(Boolean, default=False, index=True)
    category = Column(String(64), index=True)
    
    # 完整数据（JSON格式存储所有工作流输出）
    data = Column(JSON, nullable=False)
    
    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EventRecord(id={self.id}, news_id='{self.news_id}')>"

    def to_dict(self) -> dict:
        """返回完整数据。"""
        result = self.data.copy() if self.data else {}
        result.update({
            "id": self.id,
            "news_id": self.news_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        })
        return result


def init_database(db_path: str = "data/text_factor.db"):
    """初始化数据库连接与表结构。"""
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    _ensure_schema(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def _ensure_schema(engine) -> None:
    """为存量数据库补齐缺失列。"""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(event_records)"))
        columns = {row[1] for row in result.fetchall()}
        if "category" not in columns:
            conn.execute(text("ALTER TABLE event_records ADD COLUMN category VARCHAR(64)"))
            conn.commit()
