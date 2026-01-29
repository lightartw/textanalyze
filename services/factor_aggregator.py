# services/factor_aggregator.py
"""
简化的聚合服务 - 基本统计
"""
from datetime import datetime
from typing import Dict, Any, List


class FactorAggregator:
    """事件聚合统计。"""

    def aggregate(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算基本统计信息。
        
        Args:
            events: 事件列表
            
        Returns:
            统计信息字典
        """
        if not events:
            return {
                "total": 0,
                "oil_related": 0,
                "skipped": 0,
                "by_type": {},
            }
        
        oil_related = [e for e in events if e.get("is_oil_related", False)]
        skipped = [e for e in events if not e.get("is_oil_related", False)]
        
        # 按人工分类统计
        by_type: Dict[str, int] = {}
        for e in oil_related:
            category = e.get("category") or "other"
            by_type[category] = by_type.get(category, 0) + 1
        
        return {
            "total": len(events),
            "oil_related": len(oil_related),
            "skipped": len(skipped),
            "by_type": by_type,
        }
