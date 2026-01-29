# database/repository.py
"""
数据库操作封装 - 通用事件存储接口
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from .models import EventRecord, init_database


class EventRepository:
    """事件存储仓库 - 通用接口。"""

    def __init__(self, db_path: str = "data/text_factor.db"):
        """初始化数据库连接。"""
        self.engine, self.SessionClass = init_database(db_path)
        self.db_path = db_path

    def get_session(self) -> Session:
        """获取数据库会话。"""
        return self.SessionClass()

    def save(self, data: Dict[str, Any]) -> EventRecord:
        """
        保存事件数据。
        
        Args:
            data: 完整的事件数据字典，必须包含 'id' 字段作为 news_id
            
        Returns:
            EventRecord: 保存的记录
        """
        session = self.get_session()
        try:
            news_id = str(data.get("id", ""))
            if not news_id:
                raise ValueError("数据必须包含 'id' 字段")
            
            # 提取索引字段
            event_date = self._parse_date(data.get("date", ""))
            is_oil_related = bool(data.get("is_oil_related", False))
            category = data.get("category")
            
            # 查找是否已存在
            existing = session.query(EventRecord).filter_by(news_id=news_id).first()
            
            if existing:
                # 更新
                existing.event_date = event_date
                existing.is_oil_related = is_oil_related
                existing.category = category
                existing.data = data
                existing.updated_at = datetime.now(timezone.utc)
                record = existing
            else:
                # 新建
                record = EventRecord(
                    news_id=news_id,
                    event_date=event_date,
                    is_oil_related=is_oil_related,
                    category=category,
                    data=data,
                )
                session.add(record)
            
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_by_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """根据新闻ID获取事件数据。"""
        session = self.get_session()
        try:
            record = session.query(EventRecord).filter_by(news_id=news_id).first()
            return record.to_dict() if record else None
        finally:
            session.close()

    def get_similar_events(
        self,
        category: Optional[str] = None,
        days_back: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取历史同类事件。"""
        session = self.get_session()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            query = session.query(EventRecord).filter(
                EventRecord.is_oil_related == True,
                EventRecord.created_at >= cutoff_date,
            )
            if category:
                query = query.filter(EventRecord.category == category)
            
            records = query.order_by(EventRecord.created_at.desc()).limit(limit).all()
            return [r.to_dict() for r in records]
        finally:
            session.close()

    def get_all(
        self,
        oil_related_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """获取所有事件。"""
        session = self.get_session()
        try:
            query = session.query(EventRecord)
            if oil_related_only:
                query = query.filter(EventRecord.is_oil_related == True)
            query = query.order_by(EventRecord.created_at.desc())
            if limit:
                query = query.limit(limit)
            return [r.to_dict() for r in query.all()]
        finally:
            session.close()

    def count(self, oil_related_only: bool = False) -> int:
        """统计事件数量。"""
        session = self.get_session()
        try:
            query = session.query(EventRecord)
            if oil_related_only:
                query = query.filter(EventRecord.is_oil_related == True)
            return query.count()
        finally:
            session.close()

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串。"""
        if not date_str:
            return None
        if isinstance(date_str, datetime):
            return date_str
        formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        return None
