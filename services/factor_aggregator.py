"""
文本因子聚合服务
按日期聚合事件因子值
"""
from datetime import datetime
from typing import Dict, Any, List


class FactorAggregator:
    """按日聚合文本因子事件。"""

    def aggregate(self, events: List[Dict[str, Any]], target_date: datetime = None) -> Dict[str, Any]:
        """计算日度因子统计信息。"""
        if target_date is None:
            target_date = datetime.now()

        related_events = [e for e in events if e.get("is_oil_related", False)]
        unrelated_events = [e for e in events if not e.get("is_oil_related", False)]
        
        if not related_events:
            return self._empty_summary(target_date, len(events), unrelated_events)

        factor_values = [
            e.get("adjusted_factor_value", e.get("factor_value", 0)) 
            for e in related_events
        ]
        avg_factor = sum(factor_values) / len(factor_values) if factor_values else 0

        # 收集各事件的 LLM 分析原因
        event_analyses = self._collect_event_analyses(related_events)
        skipped_events = self._collect_skipped_events(unrelated_events)

        return {
            "summary_date": target_date.replace(hour=0, minute=0, second=0, microsecond=0),
            "total_events": len(events),
            "oil_related_events": len(related_events),
            "avg_factor_value": round(avg_factor, 4),
            "factor_category_counts": self._count_categories(related_events),
            "event_analyses": event_analyses,
            "skipped_events": skipped_events,
        }

    def _collect_event_analyses(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """收集油价相关事件的 LLM 分析详情。"""
        analyses = []
        for e in events:
            analyses.append({
                "title": e.get("title", ""),
                "factor_category": e.get("factor_category", ""),
                "factor_value": e.get("factor_value", 0),
                "adjusted_factor_value": e.get("adjusted_factor_value", e.get("factor_value", 0)),
                "classify_confidence": e.get("classify_confidence", 0),
                "classify_reason": e.get("classify_reason", ""),
                "keywords_found": e.get("keywords_found", []),
                "quantification_logic": e.get("quantification_logic", ""),
                "impact_magnitude": e.get("impact_magnitude", ""),
                "time_horizon": e.get("time_horizon", ""),
                "is_valid": e.get("is_valid", True),
                "adjustment_reason": e.get("adjustment_reason", ""),
                "historical_consistency": e.get("historical_consistency", ""),
            })
        return analyses

    def _collect_skipped_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """收集被跳过的无关事件摘要。"""
        skipped = []
        for e in events:
            skipped.append({
                "title": e.get("title", ""),
                "skip_reason": e.get("classify_reason", "与油价无关"),
            })
        return skipped

    def _count_categories(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计因子分类数量。"""
        counts: Dict[str, int] = {}
        for event in events:
            category = event.get("factor_category", "unrelated")
            counts[category] = counts.get(category, 0) + 1
        return counts

    def _empty_summary(
        self, 
        target_date: datetime, 
        total_events: int,
        unrelated_events: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成空汇总（无油价相关事件）。"""
        skipped = []
        if unrelated_events:
            skipped = self._collect_skipped_events(unrelated_events)
        
        return {
            "summary_date": target_date.replace(hour=0, minute=0, second=0, microsecond=0),
            "total_events": total_events,
            "oil_related_events": 0,
            "avg_factor_value": 0,
            "factor_category_counts": {},
            "event_analyses": [],
            "skipped_events": skipped,
        }
