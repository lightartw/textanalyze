"""
每日报告生成服务 - 生成和管理每日综合分析报告
"""
from datetime import datetime
from typing import Dict, Any, Optional
import os
import json

import config


class DailyReportGenerator:
    """每日报告生成器，负责生成和管理每日综合分析报告。"""

    def __init__(self, output_dir: str = None):
        """
        初始化每日报告生成器
        
        Args:
            output_dir: 报告输出目录（可选，默认使用配置文件中的值）
        """
        self.output_dir = output_dir or config.DAILY_REPORT_OUTPUT_DIR
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def save_daily_report(
        self, 
        report_data: Dict[str, Any], 
        filename: Optional[str] = None
    ) -> str:
        """
        保存每日综合分析报告
        
        Args:
            report_data: 报告数据字典
            filename: 文件名（可选，默认按日期生成）
            
        Returns:
            str: 保存的文件路径
        """
        if filename is None:
            analysis_date = report_data.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))
            filename = f"daily_report_{analysis_date}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        return filepath

    def generate_text_report(
        self, 
        report_data: Dict[str, Any], 
        filename: Optional[str] = None
    ) -> str:
        """
        生成文本格式的每日报告
        
        Args:
            report_data: 报告数据字典
            filename: 文件名（可选，默认按日期生成）
            
        Returns:
            str: 保存的文件路径
        """
        if filename is None:
            analysis_date = report_data.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))
            filename = f"daily_report_{analysis_date}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 构建报告内容
        lines = [
            "=" * 80,
            "每日石油市场综合分析报告",
            "=" * 80,
            f"分析日期: {report_data.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"分析事件数: {report_data.get('total_events_analyzed', 0)}",
            "",
        ]
        
        # 市场总体概况
        lines.extend([
            "-" * 80,
            "一、市场总体概况",
            "-" * 80,
            report_data.get("market_overview", "无数据"),
            "",
        ])
        
        # 短期风险评估
        short_term = report_data.get("short_term_risk", {})
        lines.extend([
            "-" * 80,
            "二、短期风险评估（1-7天）",
            "-" * 80,
            f"风险等级: {short_term.get('risk_level', '无数据')}",
            f"置信度: {short_term.get('confidence', '无数据')}",
            "",
        ])
        
        # 短期风险关键指标
        short_term_metrics = short_term.get("key_metrics", {})
        if short_term_metrics:
            lines.extend([
                "关键指标:",
                f"  - 情绪平均值: {short_term_metrics.get('sentiment_average', '无数据')}",
                f"  - 强度平均值: {short_term_metrics.get('intensity_average', '无数据')}",
                f"  - 市场波动性: {short_term_metrics.get('market_volatility', '无数据')}",
                "",
            ])
        
        lines.extend([
            "评估结果:",
            short_term.get("assessment", "无数据"),
            "",
            "走势预测:",
            short_term.get("forecast", "无数据"),
            "",
            "主要风险因素:",
        ])
        for factor in short_term.get("risk_factors", []):
            lines.append(f"  - {factor}")
        lines.append("")
        
        # 长期风险评估
        long_term = report_data.get("long_term_risk", {})
        lines.extend([
            "-" * 80,
            "三、长期风险评估（7-30天）",
            "-" * 80,
            f"风险等级: {long_term.get('risk_level', '无数据')}",
            f"置信度: {long_term.get('confidence', '无数据')}",
            "",
        ])
        
        # 长期风险关键指标
        long_term_metrics = long_term.get("key_metrics", {})
        if long_term_metrics:
            lines.extend([
                "关键指标:",
                f"  - 趋势强度: {long_term_metrics.get('trend_strength', '无数据')}",
                f"  - 基本面平衡: {long_term_metrics.get('fundamental_balance', '无数据')}",
                f"  - 地缘政治稳定性: {long_term_metrics.get('geopolitical_stability', '无数据')}",
                "",
            ])
        
        lines.extend([
            "评估结果:",
            long_term.get("assessment", "无数据"),
            "",
            "走势预测:",
            long_term.get("forecast", "无数据"),
            "",
            "主要风险因素:",
        ])
        for factor in long_term.get("risk_factors", []):
            lines.append(f"  - {factor}")
        lines.append("")
        
        # 重点关注事件
        key_events = report_data.get("key_events", [])
        lines.extend([
            "-" * 80,
            "四、重点关注事件",
            "-" * 80,
        ])
        if key_events:
            for i, event in enumerate(key_events, 1):
                lines.extend([
                    f"{i}. {event.get('title', '无标题')}",
                    f"   关注原因: {event.get('reason', '无数据')}",
                    f"   潜在影响: {event.get('potential_impact', '无数据')}",
                    f"   建议行动: {event.get('suggested_action', '无数据')}",
                ])
                # 监控指标
                monitoring_metrics = event.get("monitoring_metrics", [])
                if monitoring_metrics:
                    lines.append(f"   监控指标: {', '.join(monitoring_metrics)}")
                lines.append("")
        else:
            lines.append("无重点关注事件")
            lines.append("")
        
        # 事件关联性分析
        lines.extend([
            "-" * 80,
            "五、事件关联性分析",
            "-" * 80,
            report_data.get("event_correlation", "无数据"),
            "",
        ])
        
        # 油价风险应对策略
        oil_price_strategies = report_data.get("oil_price_strategies", {})
        if oil_price_strategies:
            lines.extend([
                "-" * 80,
                "六、油价风险应对策略",
                "-" * 80,
            ])
            
            # 短期应对策略
            short_term_strategy = oil_price_strategies.get("short_term", "")
            if short_term_strategy:
                lines.extend([
                    "短期应对策略:",
                    short_term_strategy,
                    "",
                ])
            
            # 长期战略建议
            long_term_strategy = oil_price_strategies.get("long_term", "")
            if long_term_strategy:
                lines.extend([
                    "长期战略建议:",
                    long_term_strategy,
                    "",
                ])
            
            # 按利益相关者分类的建议
            by_stakeholder = oil_price_strategies.get("by_stakeholder", {})
            if by_stakeholder:
                lines.append("按利益相关者分类建议:")
                if by_stakeholder.get("producers"):
                    lines.extend([
                        "  生产者建议:",
                        f"    {by_stakeholder.get('producers')}",
                    ])
                if by_stakeholder.get("consumers"):
                    lines.extend([
                        "  消费者建议:",
                        f"    {by_stakeholder.get('consumers')}",
                    ])
                if by_stakeholder.get("investors"):
                    lines.extend([
                        "  投资者建议:",
                        f"    {by_stakeholder.get('investors')}",
                    ])
                if by_stakeholder.get("policymakers"):
                    lines.extend([
                        "  政策制定者建议:",
                        f"    {by_stakeholder.get('policymakers')}",
                    ])
                lines.append("")
            
            # 监控系统建议
            monitoring_system = oil_price_strategies.get("monitoring_system", "")
            if monitoring_system:
                lines.extend([
                    "监控指标与预警系统:",
                    monitoring_system,
                    "",
                ])
        else:
            # 传统风险缓解建议
            lines.extend([
                "-" * 80,
                "六、风险缓解建议",
                "-" * 80,
                report_data.get("risk_mitigation", "无数据"),
                "",
            ])
        
        # 报告结尾
        lines.extend([
            "=" * 80,
            "报告结束",
            "=" * 80,
        ])
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return filepath

    def generate_summary_report(
        self, 
        report_data: Dict[str, Any], 
        filename: Optional[str] = None
    ) -> str:
        """
        生成摘要版每日报告
        
        Args:
            report_data: 报告数据字典
            filename: 文件名（可选，默认按日期生成）
            
        Returns:
            str: 保存的文件路径
        """
        if filename is None:
            analysis_date = report_data.get("analysis_date", datetime.now().strftime("%Y-%m-%d"))
            filename = f"daily_summary_{analysis_date}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # 构建摘要内容
        lines = [
            "=" * 60,
            "每日石油市场分析摘要",
            "=" * 60,
            f"分析日期: {report_data.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        # 市场概况摘要
        market_overview = report_data.get("market_overview", "")
        if market_overview:
            # 提取前200个字符作为摘要
            overview_summary = market_overview[:200] + ("..." if len(market_overview) > 200 else "")
            lines.extend([
                "市场概况:",
                overview_summary,
                "",
            ])
        
        # 风险评估摘要
        short_term = report_data.get("short_term_risk", {})
        long_term = report_data.get("long_term_risk", {})
        lines.extend([
            "风险评估:",
            f"短期风险: {short_term.get('risk_level', '无数据')} (置信度: {short_term.get('confidence', '无数据')})",
            f"长期风险: {long_term.get('risk_level', '无数据')} (置信度: {long_term.get('confidence', '无数据')})",
            "",
        ])
        
        # 重点事件摘要
        key_events = report_data.get("key_events", [])
        if key_events:
            lines.extend([
                "重点关注事件:",
            ])
            for i, event in enumerate(key_events[:3], 1):  # 只显示前3个
                lines.append(f"{i}. {event.get('title', '无标题')}")
            if len(key_events) > 3:
                lines.append(f"... 等{len(key_events)}个事件")
            lines.append("")
        
        # 报告结尾
        lines.extend([
            "=" * 60,
            "详细报告请查看完整版",
            "=" * 60,
        ])
        
        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return filepath

    def get_report_path(self, date: str) -> str:
        """
        获取指定日期的报告路径
        
        Args:
            date: 日期字符串，格式为 "YYYY-MM-DD"
            
        Returns:
            str: 报告文件路径
        """
        filename = f"daily_report_{date}.json"
        return os.path.join(self.output_dir, filename)

    def list_reports(self) -> list:
        """
        列出所有已生成的每日报告
        
        Returns:
            list: 报告文件路径列表
        """
        reports = []
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                if file.startswith("daily_report_") and (file.endswith(".json") or file.endswith(".txt")):
                    reports.append(os.path.join(self.output_dir, file))
        return reports
