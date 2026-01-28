# services/report_generator.py
"""
因子报告生成服务
生成包含 LLM 分析原因的详细因子报告
"""
from datetime import datetime
from typing import Dict, Any, List
import os


class ReportGenerator:
    """生成文本因子摘要报告。"""

    # 影响程度映射
    IMPACT_MAGNITUDE_MAP = {
        "low": "低",
        "medium": "中",
        "high": "高",
    }
    
    # 时间范围映射
    TIME_HORIZON_MAP = {
        "short": "短期",
        "medium": "中期",
        "long": "长期",
    }

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """确保输出目录存在。"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_summary(self, summary: Dict[str, Any]) -> str:
        """生成日度因子摘要文本（包含 LLM 分析详情）。"""
        date_str = summary.get("summary_date")
        if isinstance(date_str, datetime):
            date_str = date_str.strftime("%Y-%m-%d")

        counts = summary.get("factor_category_counts", {})
        counts_text = ", ".join([f"{k}:{v}" for k, v in counts.items()]) or "无"
        
        # 计算整体市场倾向
        avg_value = summary.get("avg_factor_value", 0)
        market_trend = self._get_market_trend(avg_value)

        lines = [
            "=" * 70,
            "文本因子日度分析报告",
            "=" * 70,
            "",
            "【基础统计】",
            f"  报告日期: {date_str}",
            f"  总事件数: {summary.get('total_events', 0)}",
            f"  油价相关事件: {summary.get('oil_related_events', 0)}",
            f"  平均因子值: {avg_value}",
            f"  市场倾向: {market_trend}",
            f"  分类统计: {counts_text}",
            "",
        ]

        # 添加详细事件分析
        event_analyses = summary.get("event_analyses", [])
        if event_analyses:
            lines.extend(self._render_event_analyses(event_analyses))
        
        # 添加被跳过的事件
        skipped_events = summary.get("skipped_events", [])
        if skipped_events:
            lines.extend(self._render_skipped_events(skipped_events))
        
        lines.append("=" * 70)
        lines.append("报告结束")
        lines.append("=" * 70)
        
        return "\n".join(lines)

    def _get_market_trend(self, avg_value: float) -> str:
        """根据平均因子值判断市场倾向。"""
        if avg_value > 0.3:
            return "强烈利多"
        elif avg_value > 0.1:
            return "温和利多"
        elif avg_value > -0.1:
            return "中性"
        elif avg_value > -0.3:
            return "温和利空"
        else:
            return "强烈利空"

    def _render_event_analyses(self, events: List[Dict[str, Any]]) -> List[str]:
        """渲染油价相关事件的详细分析。"""
        lines = [
            "-" * 70,
            "【油价相关事件详细分析】",
            "-" * 70,
        ]
        
        for i, event in enumerate(events, 1):
            title = event.get("title", "未知标题")
            # 截断过长标题
            if len(title) > 60:
                title = title[:57] + "..."
            
            category = event.get("factor_category", "未分类")
            confidence = event.get("classify_confidence", 0)
            factor_value = event.get("factor_value", 0)
            adjusted_value = event.get("adjusted_factor_value", factor_value)
            
            impact = self.IMPACT_MAGNITUDE_MAP.get(
                event.get("impact_magnitude", ""), 
                event.get("impact_magnitude", "未知")
            )
            horizon = self.TIME_HORIZON_MAP.get(
                event.get("time_horizon", ""),
                event.get("time_horizon", "未知")
            )
            
            keywords = event.get("keywords_found", [])
            keywords_text = ", ".join(keywords) if keywords else "无"
            
            classify_reason = event.get("classify_reason", "") or "无"
            quant_logic = event.get("quantification_logic", "") or "无"
            adjustment_reason = event.get("adjustment_reason", "") or "无调整"
            hist_consistency = event.get("historical_consistency", "") or "无历史参考"
            
            # 因子值是否被调整
            value_adjusted = abs(adjusted_value - factor_value) > 0.001
            value_display = f"{adjusted_value}"
            if value_adjusted:
                value_display = f"{adjusted_value} (原值: {factor_value})"
            
            lines.extend([
                "",
                f"事件 {i}: {title}",
                f"  ├─ 因子分类: {category}",
                f"  ├─ 分类置信度: {confidence:.2f}",
                f"  ├─ 关键词: {keywords_text}",
                f"  ├─ 因子值: {value_display}",
                f"  ├─ 影响程度: {impact}",
                f"  ├─ 影响周期: {horizon}",
                f"  │",
                f"  ├─ [分类原因]",
                f"  │  {self._indent_text(classify_reason, 5)}",
                f"  │",
                f"  ├─ [量化依据]",
                f"  │  {self._indent_text(quant_logic, 5)}",
                f"  │",
                f"  ├─ [校验调整]",
                f"  │  {self._indent_text(adjustment_reason, 5)}",
                f"  │",
                f"  └─ [历史一致性]",
                f"     {self._indent_text(hist_consistency, 5)}",
            ])
        
        lines.append("")
        return lines

    def _render_skipped_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """渲染被跳过的无关事件。"""
        lines = [
            "-" * 70,
            "【已跳过的无关事件】",
            "-" * 70,
        ]
        
        for i, event in enumerate(events, 1):
            title = event.get("title", "未知标题")
            if len(title) > 50:
                title = title[:47] + "..."
            reason = event.get("skip_reason", "与油价无关")
            lines.append(f"  {i}. {title}")
            lines.append(f"     跳过原因: {reason}")
        
        lines.append("")
        return lines

    def _indent_text(self, text: str, indent: int = 3) -> str:
        """处理多行文本的缩进。"""
        if not text:
            return "无"
        # 将长文本按适当宽度换行
        max_width = 60
        words = text.replace("\n", " ").split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # 添加缩进
        indent_str = " " * indent
        return ("\n" + "  │" + indent_str).join(lines) if lines else "无"

    def save_text_report(self, report_text: str, filename: str) -> str:
        """保存文本报告到文件。"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_text)
        return filepath
