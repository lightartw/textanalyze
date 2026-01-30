"""
每日综合分析报告生成脚本
用于生成包含长短期风险评估和重点事件分析的每日报告
"""
import argparse
from datetime import datetime
from typing import Optional

import config
from agents.daily_summary_agent import DailySummaryAgent
from services.daily_report_generator import DailyReportGenerator
from llm_client import LLMClient


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(description="生成每日石油市场综合分析报告")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="分析日期，格式为 YYYY-MM-DD（默认当天）"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=None,
        help="分析的历史天数（默认使用配置文件中的值）"
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="最大分析事件数（默认使用配置文件中的值）"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        default=config.DAILY_REPORT_DETAILED,
        help="生成详细报告"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=config.DAILY_REPORT_SUMMARY,
        help="生成摘要报告"
    )
    parser.add_argument(
        "--oil-only",
        action="store_true",
        default=True,
        help="只分析与油价相关的事件"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="报告输出目录（默认使用配置文件中的值）"
    )
    return parser.parse_args()


def generate_daily_report(
    date: Optional[str] = None,
    days_back: Optional[int] = None,
    max_events: Optional[int] = None,
    oil_related_only: bool = True,
    detailed: bool = True,
    summary: bool = True,
    output_dir: Optional[str] = None
) -> dict:
    """
    生成每日综合分析报告
    
    Args:
        date: 分析日期（可选，默认当天）
        days_back: 分析的历史天数（可选，默认使用配置文件中的值）
        max_events: 最大分析事件数（可选，默认使用配置文件中的值）
        oil_related_only: 是否只分析油价相关事件（可选，默认True）
        detailed: 是否生成详细报告（可选，默认True）
        summary: 是否生成摘要报告（可选，默认True）
        output_dir: 报告输出目录（可选，默认使用配置文件中的值）
        
    Returns:
        dict: 报告生成结果，包含生成的文件路径等信息
    """
    # 确定分析日期
    analysis_date = date or datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'=' * 60}")
    print(f"开始生成每日综合分析报告")
    print(f"分析日期: {analysis_date}")
    print(f"{'=' * 60}")
    
    # 初始化LLM客户端
    print("初始化LLM客户端...")
    llm_client = LLMClient()
    
    # 初始化每日摘要智能体
    print("初始化每日摘要智能体...")
    summary_agent = DailySummaryAgent(llm_client)
    
    # 构建分析参数
    analysis_params = {
        "date": analysis_date,
        "days_back": days_back or config.DAILY_REPORT_DAYS_BACK,
        "max_events": max_events or config.DAILY_REPORT_MAX_EVENTS,
        "oil_related_only": oil_related_only
    }
    
    print(f"分析参数:")
    print(f"  - 历史天数: {analysis_params['days_back']}")
    print(f"  - 最大事件数: {analysis_params['max_events']}")
    print(f"  - 只分析油价相关: {analysis_params['oil_related_only']}")
    
    # 执行综合分析
    print("\n执行综合分析...")
    result = summary_agent.execute(analysis_params)
    
    if not result.success:
        print(f"\n错误: {result.error}")
        return {
            "success": False,
            "error": result.error
        }
    
    # 获取分析结果
    report_data = result.data
    print(f"\n分析完成!")
    print(f"  - 分析事件数: {report_data.get('total_events_analyzed', 0)}")
    print(f"  - 短期风险等级: {report_data.get('short_term_risk', {}).get('risk_level', '无数据')}")
    print(f"  - 长期风险等级: {report_data.get('long_term_risk', {}).get('risk_level', '无数据')}")
    print(f"  - 重点关注事件数: {len(report_data.get('key_events', []))}")
    
    # 初始化报告生成器
    print("\n初始化报告生成器...")
    report_generator = DailyReportGenerator(output_dir)
    
    # 保存JSON格式报告
    print("保存JSON格式报告...")
    json_report_path = report_generator.save_daily_report(report_data)
    print(f"  - JSON报告: {json_report_path}")
    
    # 生成文本格式报告
    text_report_path = None
    if detailed:
        print("生成详细文本报告...")
        text_report_path = report_generator.generate_text_report(report_data)
        print(f"  - 详细报告: {text_report_path}")
    
    # 生成摘要报告
    summary_report_path = None
    if summary:
        print("生成摘要报告...")
        summary_report_path = report_generator.generate_summary_report(report_data)
        print(f"  - 摘要报告: {summary_report_path}")
    
    print(f"\n{'=' * 60}")
    print(f"每日综合分析报告生成完成!")
    print(f"分析日期: {analysis_date}")
    print(f"{'=' * 60}")
    
    return {
        "success": True,
        "analysis_date": analysis_date,
        "json_report": json_report_path,
        "text_report": text_report_path,
        "summary_report": summary_report_path,
        "total_events_analyzed": report_data.get('total_events_analyzed', 0),
        "short_term_risk_level": report_data.get('short_term_risk', {}).get('risk_level', '无数据'),
        "long_term_risk_level": report_data.get('long_term_risk', {}).get('risk_level', '无数据'),
        "key_events_count": len(report_data.get('key_events', []))
    }


def main() -> None:
    """
    主函数
    """
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 生成每日报告
        result = generate_daily_report(
            date=args.date,
            days_back=args.days_back,
            max_events=args.max_events,
            oil_related_only=args.oil_only,
            detailed=args.detailed,
            summary=args.summary,
            output_dir=args.output_dir
        )
        
        # 输出结果
        if result["success"]:
            print("\n执行结果:")
            print(f"  状态: 成功")
            print(f"  分析日期: {result['analysis_date']}")
            print(f"  分析事件数: {result['total_events_analyzed']}")
            print(f"  短期风险等级: {result['short_term_risk_level']}")
            print(f"  长期风险等级: {result['long_term_risk_level']}")
            print(f"  重点关注事件数: {result['key_events_count']}")
            print(f"  JSON报告: {result['json_report']}")
            if result['text_report']:
                print(f"  详细报告: {result['text_report']}")
            if result['summary_report']:
                print(f"  摘要报告: {result['summary_report']}")
        else:
            print(f"\n执行失败: {result['error']}")
            exit(1)
    
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
