"""
LLM文本因子分析主流程
按照流程图执行：抓取 -> 分类 -> 量化 -> 校验 -> 聚合 -> 输出
"""
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import config
from data_loader import DataLoader
from crawler import SimpleCrawler
from llm_client import LLMClient
from workflow import WorkflowPipeline, WorkflowNode, NodeResult
from workflow.nodes import NodeStatus
from agents import TextFactorClassifier, FactorQuantifier, FactorValidator
from database import EventRepository
from services import FactorAggregator, ReportGenerator
from factor_interface import build_factor_series, export_factor_csv, export_factor_doc


class TextFactorAnalyzer:
    """文本因子分析器，聚焦非结构化新闻因子输出。"""

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.crawler = SimpleCrawler()
        self.repository = EventRepository(config.DATABASE_PATH)
        self.aggregator = FactorAggregator()
        self.reporter = ReportGenerator(config.REPORT_OUTPUT_DIR)

        self.classifier = TextFactorClassifier(self.llm)
        self.quantifier = FactorQuantifier(self.llm)
        self.validator = FactorValidator(self.llm)

        self.pipeline = self._build_pipeline()
        self.daily_results: List[Dict[str, Any]] = []
        
        # 线程安全锁
        self._results_lock = threading.Lock()
        self._print_lock = threading.Lock()

    def _build_pipeline(self) -> WorkflowPipeline:
        """构建文本因子工作流。"""
        pipeline = WorkflowPipeline(name="TextFactorPipeline")

        pipeline.register(
            WorkflowNode(
                name="crawl",
                handler=self._node_crawl,
                description="抓取新闻正文",
                next_node="agent_classify",
            )
        )
        pipeline.register(
            WorkflowNode(
                name="agent_classify",
                handler=self._node_classify,
                description="Agent1: 文本因子分类",
                condition_field="is_oil_related",
                condition_true="agent_quantify",
                condition_false="mark_skip",
            )
        )
        pipeline.register(
            WorkflowNode(
                name="mark_skip",
                handler=self._node_mark_skip,
                description="标记无关新闻",
                next_node="save_event",
            )
        )
        pipeline.register(
            WorkflowNode(
                name="agent_quantify",
                handler=self._node_quantify,
                description="Agent2: 因子量化",
                next_node="db_query",
            )
        )
        pipeline.register(
            WorkflowNode(
                name="db_query",
                handler=self._node_query_similar,
                description="查询历史同类事件",
                next_node="agent_validate",
            )
        )
        pipeline.register(
            WorkflowNode(
                name="agent_validate",
                handler=self._node_validate,
                description="Agent3: 因子校验",
                next_node="save_event",
            )
        )
        pipeline.register(
            WorkflowNode(
                name="save_event",
                handler=self._node_save_event,
                description="保存事件",
                next_node=None,
            )
        )

        pipeline.set_start("crawl")
        return pipeline

    def _node_crawl(self, context: Dict[str, Any]) -> NodeResult:
        """抓取新闻正文。"""
        news_item = context.get("news_item")
        url = news_item.url if hasattr(news_item, "url") else news_item.get("url", "")
        if not url:
            return NodeResult(status=NodeStatus.FAILED, error="URL为空")

        content = self.crawler.fetch_text(url)
        if not content:
            return NodeResult(status=NodeStatus.FAILED, error="抓取内容为空")

        return NodeResult(status=NodeStatus.SUCCESS, data={"content": content})

    def _node_classify(self, context: Dict[str, Any]) -> NodeResult:
        """文本因子分类。"""
        news_item = context.get("news_item")
        title = news_item.title if hasattr(news_item, "title") else news_item.get("title", "")
        content = context.get("content", "")

        result = self.classifier.execute({"title": title, "content": content})
        if not result.success:
            return NodeResult(status=NodeStatus.FAILED, error=result.error)

        return NodeResult(status=NodeStatus.SUCCESS, data=result.data)

    def _node_mark_skip(self, context: Dict[str, Any]) -> NodeResult:
        """标记无关新闻。"""
        return NodeResult(
            status=NodeStatus.SKIPPED,
            data={"status": "skipped", "skip_reason": "与油价无关"},
        )

    def _node_quantify(self, context: Dict[str, Any]) -> NodeResult:
        """量化因子值。"""
        news_item = context.get("news_item")
        title = news_item.title if hasattr(news_item, "title") else news_item.get("title", "")
        content = context.get("content", "")
        category = context.get("factor_category", "unrelated")

        result = self.quantifier.execute(
            {"title": title, "content": content, "factor_category": category}
        )
        if not result.success:
            return NodeResult(status=NodeStatus.FAILED, error=result.error)

        return NodeResult(status=NodeStatus.SUCCESS, data=result.data)

    def _node_query_similar(self, context: Dict[str, Any]) -> NodeResult:
        """查询历史同类事件。"""
        factor_category = context.get("factor_category", "unrelated")
        similar_events = self.repository.get_similar_events(
            factor_category=factor_category,
            days_back=config.SIMILAR_EVENTS_DAYS,
            limit=config.SIMILAR_EVENTS_LIMIT,
        )
        return NodeResult(status=NodeStatus.SUCCESS, data={"similar_events": similar_events})

    def _node_validate(self, context: Dict[str, Any]) -> NodeResult:
        """校验因子量化结果。"""
        news_item = context.get("news_item")
        title = news_item.title if hasattr(news_item, "title") else news_item.get("title", "")
        content = context.get("content", "")

        result = self.validator.execute(
            {
                "title": title,
                "content": content,
                "factor_category": context.get("factor_category", "unrelated"),
                "factor_value": context.get("factor_value", 0),
                "similar_events": context.get("similar_events", []),
            }
        )
        if not result.success:
            return NodeResult(
                status=NodeStatus.SUCCESS,
                data={
                    "is_valid": False,
                    "adjusted_factor_value": context.get("factor_value", 0),
                    "adjustment_reason": result.error or "校验失败",
                },
            )

        return NodeResult(status=NodeStatus.SUCCESS, data=result.data)

    def _node_save_event(self, context: Dict[str, Any]) -> NodeResult:
        """保存事件到数据库，并收集结果。"""
        news_item = context.get("news_item")
        event_data = {
            "news_id": news_item.id if hasattr(news_item, "id") else news_item.get("id", ""),
            "title": news_item.title if hasattr(news_item, "title") else news_item.get("title", ""),
            "url": news_item.url if hasattr(news_item, "url") else news_item.get("url", ""),
            "source_category": news_item.category
            if hasattr(news_item, "category")
            else news_item.get("category", ""),
            "event_date": self._parse_date(
                news_item.date if hasattr(news_item, "date") else news_item.get("date", "")
            ),
            "raw_content": context.get("content", ""),
            "is_oil_related": context.get("is_oil_related", False),
            "factor_category": context.get("factor_category", "unrelated"),
            "classify_confidence": context.get("confidence", 0),
            "classify_reason": context.get("brief_reason", ""),
            "keywords_found": context.get("keywords_found", []),
            "factor_value": context.get("factor_value", 0),
            "impact_magnitude": context.get("impact_magnitude", ""),
            "time_horizon": context.get("time_horizon", ""),
            "quantification_logic": context.get("quantification_logic", ""),
            "is_valid": context.get("is_valid", True),
            "adjusted_factor_value": context.get("adjusted_factor_value", context.get("factor_value", 0)),
            "adjustment_reason": context.get("adjustment_reason", ""),
            "historical_consistency": context.get("historical_consistency", ""),
        }

        try:
            self.repository.save_event(event_data)
            # 线程安全地添加结果
            with self._results_lock:
                self.daily_results.append(event_data)
            return NodeResult(status=NodeStatus.SUCCESS, data={"saved": True})
        except Exception as e:
            return NodeResult(status=NodeStatus.FAILED, error=f"保存失败: {e}")

    def _process_single_item(self, item: Any, item_index: int, total: int) -> bool:
        """
        处理单条新闻（供线程池调用）。
        
        Args:
            item: 新闻条目
            item_index: 当前索引（用于日志）
            total: 总数（用于日志）
            
        Returns:
            bool: 是否处理成功
        """
        try:
            context = {"news_item": item}
            title = item.title if hasattr(item, "title") else item.get("title", "未知")
            
            with self._print_lock:
                print(f"\n[Parallel] 开始处理 [{item_index + 1}/{total}]: {title[:50]}...")
            
            result = self.pipeline.run(context)
            
            with self._print_lock:
                status = "成功" if result.success else "失败"
                print(f"[Parallel] 完成 [{item_index + 1}/{total}]: {title[:30]}... - {status}")
            
            return result.success
        except Exception as e:
            with self._print_lock:
                print(f"[Parallel] 处理异常 [{item_index + 1}/{total}]: {e}")
            return False

    def analyze_batch(
        self, 
        news_items: List[Any], 
        max_workers: int = None,
        parallel: bool = None
    ) -> Dict[str, Any]:
        """
        批量分析新闻并输出因子文件。
        
        Args:
            news_items: 新闻列表
            max_workers: 最大并行线程数（默认从config读取）
            parallel: 是否启用并行（默认从config读取）
            
        Returns:
            分析结果摘要
        """
        self.daily_results = []
        total = len(news_items)
        
        # 读取配置
        if parallel is None:
            parallel = config.PARALLEL_ENABLED
        if max_workers is None:
            max_workers = config.MAX_WORKERS
        
        if parallel and total > 1:
            # 并行处理模式
            print(f"\n{'='*60}")
            print(f"[Parallel] 启动并行处理模式，线程数: {max_workers}，任务数: {total}")
            print(f"{'='*60}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                futures = {
                    executor.submit(self._process_single_item, item, idx, total): idx
                    for idx, item in enumerate(news_items)
                }
                
                # 收集结果
                success_count = 0
                fail_count = 0
                for future in as_completed(futures):
                    try:
                        if future.result():
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as e:
                        fail_count += 1
                        print(f"[Parallel] 任务异常: {e}")
            
            print(f"\n{'='*60}")
            print(f"[Parallel] 并行处理完成，成功: {success_count}，失败: {fail_count}")
            print(f"{'='*60}\n")
        else:
            # 串行处理模式（保持兼容）
            print(f"\n[Serial] 串行处理模式，任务数: {total}")
            for idx, item in enumerate(news_items):
                print(f"\n[Serial] 处理 [{idx + 1}/{total}]")
                context = {"news_item": item}
                self.pipeline.run(context)

        summary = self.aggregator.aggregate(self.daily_results)
        self.repository.save_daily_summary(summary)

        report_text = self.reporter.generate_summary(summary)
        report_name = f"factor_summary_{datetime.now().strftime('%Y%m%d')}.txt"
        self.reporter.save_text_report(report_text, report_name)

        factor_outputs = self._export_factor_series()
        return {"summary": summary, "factor_outputs": factor_outputs}

    def _export_factor_series(self) -> Dict[str, str]:
        """导出各类因子序列和说明文档。"""
        outputs: Dict[str, str] = {}
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for event in self.daily_results:
            if not event.get("is_oil_related", False):
                continue
            category = event.get("factor_category", "unrelated")
            by_category.setdefault(category, []).append(event)

        for category, events in by_category.items():
            factor_name = f"{category}_factor_v1"
            series = build_factor_series(events, factor_name, config.FACTOR_FREQUENCY)
            csv_path = export_factor_csv(series, config.FACTOR_OUTPUT_DIR)
            doc_path = export_factor_doc(
                {
                    "factor_name": factor_name,
                    "data_source": "新闻数据",
                    "logic": "LLM文本因子分类与量化",
                    "coverage": "按输入新闻覆盖范围",
                    "frequency": config.FACTOR_FREQUENCY,
                    "formula": "factor_value = LLM_quantify(text)",
                },
                config.REPORT_OUTPUT_DIR,
            )
            outputs[factor_name] = f"{csv_path} | {doc_path}"

        return outputs

    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串。"""
        if not date_str:
            return datetime.now()
        formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y-%m-%d %H:%M:%S"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.now()


def main() -> None:
    """主入口函数。"""
    items = DataLoader.load_data(config.INPUT_FILE)
    if not items:
        print("[Error] 没有加载到任何数据")
        return

    analyzer = TextFactorAnalyzer()
    result = analyzer.analyze_batch(items)
    summary = result["summary"]
    print("文本因子分析完成")
    print(f"总事件数: {summary.get('total_events', 0)}")
    print(f"油价相关事件: {summary.get('oil_related_events', 0)}")
    print(f"平均因子值: {summary.get('avg_factor_value', 0)}")


if __name__ == "__main__":
    main()
