# services/report_generator.py
"""
报告生成服务 - 从数据库读取数据生成报告
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import json


class ReportGenerator:
    """生成分析报告，数据源来自数据库。"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def save_results(
        self, 
        results: List[Dict[str, Any]], 
        filename: Optional[str] = None
    ) -> str:
        """
        保存结果到JSON文件。
        
        Args:
            results: 结果列表
            filename: 文件名（默认按时间生成）
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        return filepath

    def print_summary(self, stats: Dict[str, Any]) -> None:
        """
        打印统计摘要。
        
        Args:
            stats: 统计信息字典
        """
        print("\n" + "=" * 60)
        print("分析摘要")
        print("=" * 60)
        print(f"总数: {stats.get('total', 0)}")
        print(f"油价相关: {stats.get('oil_related', 0)}")
        print(f"已跳过: {stats.get('skipped', 0)}")
        
        by_type = stats.get("by_type", {})
        if by_type:
            print("\n按人工分类分布:")
            for category, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {category}: {count}")
        print("=" * 60)

    def generate_detailed_report(
        self, 
        events: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        生成详细的文本报告。
        
        Args:
            events: 事件列表
            filename: 文件名（默认按时间生成）
            
        Returns:
            报告文件路径
        """
        if filename is None:
            filename = f"detailed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        lines = [
            "=" * 80,
            "油价事件详细分析报告",
            "=" * 80,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"事件总数: {len(events)}",
            "",
        ]
        
        # 按人工分类分组
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for event in events:
            category = event.get("category") or "other"
            by_type.setdefault(category, []).append(event)
        
        # 为每个类型生成报告
        for category, type_events in sorted(by_type.items()):
            lines.extend([
                "-" * 80,
                f"【{category.upper()}】 ({len(type_events)} 条)",
                "-" * 80,
            ])
            
            for idx, event in enumerate(type_events, 1):
                lines.append(f"\n{idx}. {event.get('title', '未知标题')}")
                lines.append(f"   日期: {event.get('date', 'N/A')}")
                
                # 如果是油价相关，显示详细分析
                if event.get("is_oil_related"):
                    lines.append(f"   关键词: {', '.join(event.get('keywords', []))}")
                    
                    if event.get("sentiment") is not None:
                        lines.append(f"   情绪极性: {event.get('sentiment', 0):.2f}")
                    
                    if event.get("intensity") is not None:
                        lines.append(f"   冲击强度: {event.get('intensity', 0):.2f}")
                    
                    if event.get("adjusted_intensity") is not None:
                        lines.append(f"   校准强度: {event.get('adjusted_intensity', 0):.2f}")
                    
                    if event.get("transmission_path"):
                        lines.append(f"   传导路径: {event.get('transmission_path')}")
                else:
                    lines.append(f"   跳过原因: {event.get('skip_reason', '与油价无关')}")
        
        lines.extend([
            "",
            "=" * 80,
            "报告结束",
            "=" * 80,
        ])
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return filepath

    def generate_category_report(
        self,
        events: List[Dict[str, Any]],
        category: str,
        filename: Optional[str] = None
    ) -> str:
        """
        生成特定人工分类的报告。
        
        Args:
            events: 事件列表
            category: 人工分类
            filename: 文件名
            
        Returns:
            报告文件路径
        """
        filtered = [e for e in events if e.get("category") == category]
        
        if filename is None:
            filename = f"{category}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        report = {
            "category": category,
            "count": len(filtered),
            "generated_at": datetime.now().isoformat(),
            "events": filtered,
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        return filepath

    def generate_statistics_summary(
        self,
        events: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        生成统计摘要JSON。
        
        Args:
            events: 事件列表
            filename: 文件名
            
        Returns:
            文件路径
        """
        if filename is None:
            filename = f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 计算统计信息
        oil_related = [e for e in events if e.get("is_oil_related")]
        
        by_type: Dict[str, int] = {}
        intensities: List[float] = []
        sentiments: List[float] = []
        
        for event in oil_related:
            category = event.get("category") or "other"
            by_type[category] = by_type.get(category, 0) + 1
            
            if event.get("intensity") is not None:
                intensities.append(event.get("intensity"))
            
            if event.get("sentiment") is not None:
                sentiments.append(event.get("sentiment"))
        
        stats = {
            "generated_at": datetime.now().isoformat(),
            "total_events": len(events),
            "oil_related_events": len(oil_related),
            "skipped_events": len(events) - len(oil_related),
            "event_types": by_type,
            "intensity": {
                "count": len(intensities),
                "avg": sum(intensities) / len(intensities) if intensities else 0,
                "max": max(intensities) if intensities else 0,
                "min": min(intensities) if intensities else 0,
            },
            "sentiment": {
                "count": len(sentiments),
                "avg": sum(sentiments) / len(sentiments) if sentiments else 0,
                "max": max(sentiments) if sentiments else 0,
                "min": min(sentiments) if sentiments else 0,
            },
        }
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        return filepath
