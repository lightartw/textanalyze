"""
LLM文本因子分析主流程
工作流：抓取 -> Agent1(事件分类) -> Agent2(IEA分析) -> Agent3(量化评估) -> Agent4(因果验证) -> 保存
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import config
from data_loader import DataLoader
from crawler import SimpleCrawler
from llm_client import LLMClient
from workflow import WorkflowPipeline, WorkflowNode, NodeResult
from workflow.nodes import NodeStatus
from agents import EventClassifier, IEAAnalyzer, SentimentIntensityScorer, CausalValidator
from database import EventRepository


class TextFactorAnalyzer:
    """文本因子分析器，4-Agent工作流。"""

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.crawler = SimpleCrawler()
        self.repository = EventRepository(config.DATABASE_PATH)

        # 4个Agent
        self.event_classifier = EventClassifier(self.llm)       # Agent1
        self.iea_analyzer = IEAAnalyzer(self.llm)               # Agent2
        self.sentiment_scorer = SentimentIntensityScorer(self.llm)  # Agent3
        self.causal_validator = CausalValidator(self.llm)       # Agent4

        self.pipeline = self._build_pipeline()
        
        # 线程安全锁
        self._print_lock = threading.Lock()

    def _build_pipeline(self) -> WorkflowPipeline:
        """构建4-Agent文本因子工作流。"""
        pipeline = WorkflowPipeline(name="TextFactorPipeline")

        # 1. 抓取新闻正文
        pipeline.register(
            WorkflowNode(
                name="crawl",
                handler=self._node_crawl,
                description="抓取新闻正文",
                next_node="agent1_classify",
            )
        )
        
        # 2. Agent1: 事件分类
        pipeline.register(
            WorkflowNode(
                name="agent1_classify",
                handler=self._node_agent1_classify,
                description="Agent1: 事件分类与油价关联判断",
                condition_field="is_oil_related",
                condition_true="agent2_iea_analyze",
                condition_false="mark_skip",
            )
        )
        
        # 3. 标记跳过（非油价相关）
        pipeline.register(
            WorkflowNode(
                name="mark_skip",
                handler=self._node_mark_skip,
                description="标记非油价相关新闻",
                next_node="save_event",
            )
        )
        
        # 4. Agent2: IEA分析
        pipeline.register(
            WorkflowNode(
                name="agent2_iea_analyze",
                handler=self._node_agent2_iea_analyze,
                description="Agent2: IEA实体与传导路径分析",
                next_node="agent3_sentiment_score",
            )
        )
        
        # 5. Agent3: 情绪量化
        pipeline.register(
            WorkflowNode(
                name="agent3_sentiment_score",
                handler=self._node_agent3_sentiment_score,
                description="Agent3: 情绪极性与冲击强度评估",
                next_node="db_query",
            )
        )
        
        # 6. 查询历史同类事件
        pipeline.register(
            WorkflowNode(
                name="db_query",
                handler=self._node_query_similar,
                description="查询历史同类事件",
                next_node="agent4_causal_validate",
            )
        )
        
        # 7. Agent4: 因果验证
        pipeline.register(
            WorkflowNode(
                name="agent4_causal_validate",
                handler=self._node_agent4_causal_validate,
                description="Agent4: 因果验证与强度校准",
                next_node="save_event",
            )
        )
        
        # 8. 保存结果
        pipeline.register(
            WorkflowNode(
                name="save_event",
                handler=self._node_save_event,
                description="保存事件到数据库",
                next_node=None,
            )
        )

        pipeline.set_start("crawl")
        return pipeline

    def _node_crawl(self, context: Dict[str, Any]) -> NodeResult:
        """抓取新闻正文。"""
        url = context.get("url", "")
        if not url:
            return NodeResult(status=NodeStatus.FAILED, error="URL为空")

        content = self.crawler.fetch_text(url)
        if not content:
            # 抓取失败时，使用标题作为内容，以便工作流继续执行
            title = context.get("title", "")
            print(f"[Crawler] 使用标题作为内容: {title[:50]}...")
            content = f"标题: {title}\n内容: 无法从URL获取正文，使用标题作为内容。"

        return NodeResult(status=NodeStatus.SUCCESS, data={"content": content})

    def _node_agent1_classify(self, context: Dict[str, Any]) -> NodeResult:
        """Agent1: 事件分类与油价关联判断。"""
        result = self.event_classifier.execute({
            "title": context.get("title", ""),
            "content": context.get("content", ""),
        })
        if not result.success:
            return NodeResult(status=NodeStatus.FAILED, error=result.error)

        return NodeResult(status=NodeStatus.SUCCESS, data=result.data)

    def _node_mark_skip(self, context: Dict[str, Any]) -> NodeResult:
        """标记非油价相关新闻。"""
        return NodeResult(
            status=NodeStatus.SKIPPED,
            data={"skip_reason": "与油价无关"},
        )

    def _node_agent2_iea_analyze(self, context: Dict[str, Any]) -> NodeResult:
        """Agent2: IEA实体与传导路径分析。"""
        result = self.iea_analyzer.execute({
            "title": context.get("title", ""),
            "content": context.get("content", ""),
            "event_type": context.get("event_type", ""),
            "keywords": context.get("keywords", []),
        })
        if not result.success:
            return NodeResult(status=NodeStatus.FAILED, error=result.error)

        return NodeResult(status=NodeStatus.SUCCESS, data=result.data)

    def _node_agent3_sentiment_score(self, context: Dict[str, Any]) -> NodeResult:
        """Agent3: 情绪极性与冲击强度评估。"""
        result = self.sentiment_scorer.execute({
            "title": context.get("title", ""),
            "content": context.get("content", ""),
            "event_type": context.get("event_type", ""),
            "key_entities": context.get("key_entities", []),
            "quantitative_metrics": context.get("quantitative_metrics", {}),
            "transmission_path": context.get("transmission_path", ""),
        })
        if not result.success:
            return NodeResult(status=NodeStatus.FAILED, error=result.error)

        return NodeResult(status=NodeStatus.SUCCESS, data=result.data)

    def _node_query_similar(self, context: Dict[str, Any]) -> NodeResult:
        """查询历史同类事件。"""
        category = context.get("category", "")
        similar_events = self.repository.get_similar_events(
            category=category,
            days_back=config.SIMILAR_EVENTS_DAYS,
            limit=config.SIMILAR_EVENTS_LIMIT,
        )
        return NodeResult(status=NodeStatus.SUCCESS, data={"similar_events": similar_events})

    def _node_agent4_causal_validate(self, context: Dict[str, Any]) -> NodeResult:
        """Agent4: 因果验证与强度校准。"""
        result = self.causal_validator.execute({
            "title": context.get("title", ""),
            "content": context.get("content", ""),
            "event_type": context.get("event_type", ""),
            "transmission_path": context.get("transmission_path", ""),
            "sentiment": context.get("sentiment", 0),
            "intensity": context.get("intensity", 0),
            "confidence": context.get("confidence", 0),
            "reasoning": context.get("reasoning", {}),
            "similar_events": context.get("similar_events", []),
        })
        if not result.success:
            # 失败时使用Agent3的原始值
            return NodeResult(
                status=NodeStatus.SUCCESS,
                data={
                    "is_causal": False,
                    "adjusted_intensity": context.get("intensity", 0),
                    "logic_analysis": {},
                    "final_confidence": context.get("confidence", 0),
                    "warning": result.error or "因果验证失败",
                },
            )

        return NodeResult(status=NodeStatus.SUCCESS, data=result.data)

    def _node_save_event(self, context: Dict[str, Any]) -> NodeResult:
        """保存事件到数据库。"""
        try:
            # 直接保存完整的context到数据库
            self.repository.save(context)
            return NodeResult(status=NodeStatus.SUCCESS, data={"saved": True})
        except Exception as e:
            return NodeResult(status=NodeStatus.FAILED, error=f"保存失败: {e}")

    def _process_single_item(self, item: Any, item_index: int, total: int) -> bool:
        """处理单条新闻。"""
        try:
            context = self._build_context(item)
            title = context.get("title", "未知")
            
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

    def _build_context(self, item: Any) -> Dict[str, Any]:
        """将NewsItem对象展开为context字典。"""
        if hasattr(item, "id"):
            return {
                "id": item.id,
                "title": item.title,
                "date": item.date,
                "category": item.category,
                "url": item.url,
            }
        else:
            return {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "date": item.get("date", ""),
                "category": item.get("category", ""),
                "url": item.get("url", ""),
            }

    def analyze_batch(
        self, 
        news_items: List[Any], 
        max_workers: Optional[int] = None,
        parallel: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        批量分析新闻并保存到数据库。
        
        Args:
            news_items: 新闻列表
            max_workers: 最大并行线程数
            parallel: 是否启用并行
            
        Returns:
            分析统计结果（仅包含处理统计，不包含报告）
        """
        total = len(news_items)
        
        if parallel is None:
            parallel = config.PARALLEL_ENABLED
        if max_workers is None:
            max_workers = config.MAX_WORKERS
        
        # 执行分析
        success_count = 0
        fail_count = 0
        
        if parallel and total > 1:
            print(f"\n{'='*60}")
            print(f"[Parallel] 启动并行处理模式，线程数: {max_workers}，任务数: {total}")
            print(f"{'='*60}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._process_single_item, item, idx, total): idx
                    for idx, item in enumerate(news_items)
                }
                
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
            print(f"\n[Serial] 串行处理模式，任务数: {total}")
            for idx, item in enumerate(news_items):
                print(f"\n[Serial] 处理 [{idx + 1}/{total}]")
                context = self._build_context(item)
                result = self.pipeline.run(context)
                if result.success:
                    success_count += 1
                else:
                    fail_count += 1
        
        return {
            "total": total,
            "success": success_count,
            "failed": fail_count,
        }


def generate_report(
    repository: EventRepository,
    oil_related_only: bool = False,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    从数据库读取数据生成报告。
    
    Args:
        repository: 数据库仓库实例
        oil_related_only: 是否只统计油价相关事件
        limit: 限制返回数量
        
    Returns:
        报告统计信息
    """
    from services import FactorAggregator, ReportGenerator
    
    aggregator = FactorAggregator()
    reporter = ReportGenerator(config.REPORT_OUTPUT_DIR)
    
    # 从数据库读取数据
    print("\n从数据库读取数据...")
    events = repository.get_all(oil_related_only=oil_related_only, limit=limit)
    print(f"读取到 {len(events)} 条记录")
    
    if not events:
        print("数据库中没有数据")
        return {
            "stats": {"total": 0, "oil_related": 0, "skipped": 0, "by_type": {}},
            "total_in_db": 0,
            "output_file": None,
        }
    
    # 统计
    stats = aggregator.aggregate(events)
    
    # 保存JSON报告
    output_file = reporter.save_results(events)
    
    # 打印摘要
    reporter.print_summary(stats)
    
    return {
        "stats": stats,
        "total_in_db": len(events),
        "output_file": output_file,
    }


def main() -> None:
    """主入口函数。"""
    # 1. 加载数据
    items = DataLoader.load_data(config.INPUT_FILE)
    if not items:
        print("[Error] 没有加载到任何数据")
        return

    # 2. 初始化分析器
    analyzer = TextFactorAnalyzer()
    
    # 3. 执行分析（只做分析和存储）
    print("\n开始分析...")
    analysis_result = analyzer.analyze_batch(items)
    
    print(f"\n分析完成！")
    print(f"总计: {analysis_result['total']} 条")
    print(f"成功: {analysis_result['success']} 条")
    print(f"失败: {analysis_result['failed']} 条")
    
    # 4. 生成报告（独立的报告生成逻辑）
    print("\n生成报告...")
    report_result = generate_report(analyzer.repository)
    
    print(f"\n报告生成完成！")
    print(f"数据库中共有: {report_result['total_in_db']} 条记录")
    if report_result['output_file']:
        print(f"报告已保存至: {report_result['output_file']}")


if __name__ == "__main__":
    main()
