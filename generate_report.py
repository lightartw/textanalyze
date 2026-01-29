#!/usr/bin/env python3
"""
独立报告生成脚本

从数据库读取已分析的数据，生成各种报告。
无需重新分析数据，可以随时运行。

使用方法:
    python generate_report.py                    # 生成所有报告
    python generate_report.py --type detailed    # 生成详细报告
    python generate_report.py --event-type geopolitical  # 生成特定类型报告
    python generate_report.py --oil-only         # 只统计油价相关事件
"""
import argparse
from datetime import datetime
from typing import Optional

import config
from database import EventRepository
from services import FactorAggregator, ReportGenerator


def main():
    parser = argparse.ArgumentParser(description="从数据库生成报告")
    parser.add_argument(
        "--type",
        choices=["all", "detailed", "statistics", "summary"],
        default="all",
        help="报告类型"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="生成特定事件类型的报告 (geopolitical, macro, sentiment, etc.)"
    )
    parser.add_argument(
        "--oil-only",
        action="store_true",
        help="只包含油价相关事件"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="限制返回数量"
    )
    
    args = parser.parse_args()
    
    # 初始化
    print("=" * 60)
    print("报告生成工具")
    print("=" * 60)
    
    repo = EventRepository(config.DATABASE_PATH)
    reporter = ReportGenerator(config.REPORT_OUTPUT_DIR)
    aggregator = FactorAggregator()
    
    # 从数据库读取数据
    print(f"\n从数据库读取数据...")
    events = repo.get_all(oil_related_only=args.oil_only, limit=args.limit)
    print(f"读取到 {len(events)} 条记录")
    
    if not events:
        print("\n数据库中没有数据，请先运行分析流程。")
        return
    
    # 如果指定了事件类型，过滤数据
    if args.category:
        category = args.category
        events = [e for e in events if e.get("category") == category]
        print(f"过滤后剩余 {len(events)} 条 {category} 人工分类事件")
    
    if not events:
        print(f"\n没有找到符合条件的事件。")
        return
    
    print("\n开始生成报告...")
    generated_files = []
    
    # 生成报告
    if args.type in ["all", "summary"]:
        # 基本摘要
        stats = aggregator.aggregate(events)
        reporter.print_summary(stats)
        
        # 保存JSON
        json_file = reporter.save_results(events)
        generated_files.append(("JSON结果", json_file))
    
    if args.type in ["all", "detailed"]:
        # 详细文本报告
        detailed_file = reporter.generate_detailed_report(events)
        generated_files.append(("详细报告", detailed_file))
    
    if args.type in ["all", "statistics"]:
        # 统计摘要
        stats_file = reporter.generate_statistics_summary(events)
        generated_files.append(("统计摘要", stats_file))
    
    # 如果指定了特定事件类型，生成该类型的报告
    if args.category:
        category_file = reporter.generate_category_report(
            events,
            category
        )
        generated_files.append((f"{category}人工分类报告", category_file))
    
    # 输出生成的文件列表
    print("\n" + "=" * 60)
    print("报告生成完成！")
    print("=" * 60)
    for name, filepath in generated_files:
        print(f"{name}: {filepath}")
    print("=" * 60)


if __name__ == "__main__":
    main()
