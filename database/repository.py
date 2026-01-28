# database/repository.py
"""
数据库操作封装
提供文本因子事件的读写接口
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from .models import TextFactorEvent, DailyFactorSummary, init_database


class EventRepository:
    """文本因子事件仓库。"""

    def __init__(self, db_path: str = "data/text_factor.db"):
        """初始化数据库连接。"""
        self.engine, self.SessionClass = init_database(db_path)
        self.db_path = db_path

    def get_session(self) -> Session:
        """获取数据库会话。"""
        return self.SessionClass()

    def save_event(self, event_data: Dict[str, Any]) -> TextFactorEvent:
        """保存或更新文本因子事件。"""
        session = self.get_session()
        try:
            news_id = event_data.get("news_id")
            existing = session.query(TextFactorEvent).filter_by(news_id=news_id).first()
            if existing:
                for key, value in event_data.items():
                    if hasattr(existing, key) and key != "id":
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                event = existing
            else:
                event = TextFactorEvent(**event_data)
                session.add(event)
            session.commit()
            session.refresh(event)
            return event
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_event_by_news_id(self, news_id: str) -> Optional[TextFactorEvent]:
        """根据新闻ID获取事件。"""
        session = self.get_session()
        try:
            return session.query(TextFactorEvent).filter_by(news_id=news_id).first()
        finally:
            session.close()

    def get_similar_events(
        self,
        factor_category: Optional[str] = None,
        days_back: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取历史同类文本因子事件。"""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = session.query(TextFactorEvent).filter(
                TextFactorEvent.is_oil_related == True,
                TextFactorEvent.created_at >= cutoff_date,
            )
            if factor_category:
                query = query.filter(TextFactorEvent.factor_category == factor_category)
            events = query.order_by(
                func.abs(TextFactorEvent.adjusted_factor_value).desc()
            ).limit(limit).all()
            return [e.to_dict() for e in events]
        finally:
            session.close()

    def get_events_by_date(
        self,
        target_date: datetime,
        oil_related_only: bool = True,
    ) -> List[TextFactorEvent]:
        """获取指定日期的事件列表。"""
        session = self.get_session()
        try:
            start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            query = session.query(TextFactorEvent).filter(
                and_(TextFactorEvent.event_date >= start, TextFactorEvent.event_date < end)
            )
            if oil_related_only:
                query = query.filter(TextFactorEvent.is_oil_related == True)
            return query.all()
        finally:
            session.close()

    def save_daily_summary(self, summary_data: Dict[str, Any]) -> DailyFactorSummary:
        """保存或更新日度因子汇总。"""
        session = self.get_session()
        try:
            summary_date = summary_data.get("summary_date")
            existing = session.query(DailyFactorSummary).filter_by(
                summary_date=summary_date
            ).first()
            if existing:
                for key, value in summary_data.items():
                    if hasattr(existing, key) and key != "id":
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                summary = existing
            else:
                summary = DailyFactorSummary(**summary_data)
                session.add(summary)
            session.commit()
            session.refresh(summary)
            return summary
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_daily_summary(self, target_date: datetime) -> Optional[DailyFactorSummary]:
        """获取指定日期的汇总。"""
        session = self.get_session()
        try:
            date_only = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            return session.query(DailyFactorSummary).filter_by(summary_date=date_only).first()
        finally:
            session.close()

    def get_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """获取文本因子统计信息。"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            total = session.query(func.count(TextFactorEvent.id)).filter(
                TextFactorEvent.created_at >= cutoff
            ).scalar()
            related = session.query(func.count(TextFactorEvent.id)).filter(
                TextFactorEvent.created_at >= cutoff,
                TextFactorEvent.is_oil_related == True,
            ).scalar()
            avg_value = session.query(func.avg(TextFactorEvent.adjusted_factor_value)).filter(
                TextFactorEvent.created_at >= cutoff,
                TextFactorEvent.is_oil_related == True,
            ).scalar()
            return {
                "total_events": total or 0,
                "oil_related_events": related or 0,
                "unrelated_events": (total or 0) - (related or 0),
                "avg_factor_value": round(avg_value or 0, 4),
                "period_days": days_back,
            }
        finally:
            session.close()
