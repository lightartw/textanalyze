# workflow/pipeline.py
"""
工作流引擎
管理和执行工作流节点
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from .nodes import WorkflowNode, NodeResult, NodeStatus


@dataclass
class ExecutionRecord:
    """单个节点的执行记录"""
    node_name: str
    status: NodeStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'node_name': self.node_name,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'error': self.error
        }


@dataclass 
class PipelineResult:
    """工作流执行结果"""
    success: bool
    context: Dict[str, Any]
    execution_log: List[ExecutionRecord] = field(default_factory=list)
    total_duration_ms: float = 0
    final_node: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'final_node': self.final_node,
            'total_duration_ms': self.total_duration_ms,
            'error': self.error,
            'execution_log': [r.to_dict() for r in self.execution_log],
            'context_keys': list(self.context.keys())
        }


class WorkflowPipeline:
    """
    工作流引擎
    
    负责注册节点、管理依赖、执行工作流
    """
    
    def __init__(self, name: str = "default"):
        """
        初始化工作流
        
        Args:
            name: 工作流名称
        """
        self.name = name
        self.nodes: Dict[str, WorkflowNode] = {}
        self.start_node: Optional[str] = None
        self.hooks: Dict[str, List[Callable]] = {
            'before_node': [],
            'after_node': [],
            'on_error': [],
            'on_complete': []
        }
    
    def register(self, node: WorkflowNode) -> 'WorkflowPipeline':
        """
        注册节点
        
        Args:
            node: 工作流节点
            
        Returns:
            self: 支持链式调用
        """
        self.nodes[node.name] = node
        return self
    
    def set_start(self, node_name: str) -> 'WorkflowPipeline':
        """
        设置起始节点
        
        Args:
            node_name: 节点名称
            
        Returns:
            self
        """
        if node_name not in self.nodes:
            raise ValueError(f"节点 {node_name} 未注册")
        self.start_node = node_name
        return self
    
    def add_hook(self, event: str, callback: Callable) -> 'WorkflowPipeline':
        """
        添加钩子函数
        
        Args:
            event: 事件类型 (before_node, after_node, on_error, on_complete)
            callback: 回调函数
            
        Returns:
            self
        """
        if event in self.hooks:
            self.hooks[event].append(callback)
        return self
    
    def _trigger_hooks(self, event: str, **kwargs):
        """触发钩子"""
        for callback in self.hooks.get(event, []):
            try:
                callback(**kwargs)
            except Exception as e:
                print(f"[Pipeline] 钩子执行失败 ({event}): {e}")
    
    def run(
        self, 
        context: Dict[str, Any], 
        start_node: Optional[str] = None
    ) -> PipelineResult:
        """
        执行工作流
        
        Args:
            context: 初始上下文
            start_node: 起始节点（可覆盖默认）
            
        Returns:
            PipelineResult: 执行结果
        """
        current_node = start_node or self.start_node
        
        if not current_node:
            return PipelineResult(
                success=False,
                context=context,
                error="未设置起始节点"
            )
        
        execution_log: List[ExecutionRecord] = []
        pipeline_start = datetime.now()
        final_node = ""
        error_msg = None
        
        print(f"\n{'='*50}")
        print(f"[Pipeline:{self.name}] 开始执行")
        print(f"{'='*50}")
        
        while current_node:
            if current_node not in self.nodes:
                error_msg = f"节点 {current_node} 不存在"
                print(f"[Pipeline] 错误: {error_msg}")
                break
            
            node = self.nodes[current_node]
            final_node = current_node
            
            print(f"\n[Pipeline] >>> 执行节点: {node.name}")
            if node.description:
                print(f"[Pipeline]     描述: {node.description}")
            
            # 记录开始时间
            record = ExecutionRecord(
                node_name=node.name,
                status=NodeStatus.RUNNING,
                start_time=datetime.now()
            )
            
            # 触发前置钩子
            self._trigger_hooks('before_node', node=node, context=context)
            
            # 执行节点
            try:
                result = node.execute(context)
                record.status = result.status
                record.error = result.error
                
                # 更新上下文
                if result.data:
                    context.update(result.data)
                
                # 确定下一节点
                if result.status == NodeStatus.FAILED:
                    self._trigger_hooks('on_error', node=node, error=result.error, context=context)
                    error_msg = result.error
                    # 失败时停止执行
                    break
                elif result.status == NodeStatus.SKIPPED:
                    print(f"[Pipeline]     状态: 已跳过")
                else:
                    print(f"[Pipeline]     状态: 成功")
                
                current_node = node.get_next_node(context, result)
                
            except Exception as e:
                record.status = NodeStatus.FAILED
                record.error = str(e)
                error_msg = str(e)
                self._trigger_hooks('on_error', node=node, error=str(e), context=context)
                break
            
            finally:
                # 记录结束时间
                record.end_time = datetime.now()
                record.duration_ms = (record.end_time - record.start_time).total_seconds() * 1000
                execution_log.append(record)
                
                # 触发后置钩子
                self._trigger_hooks('after_node', node=node, result=result, context=context)
        
        # 计算总耗时
        total_duration = (datetime.now() - pipeline_start).total_seconds() * 1000
        
        success = error_msg is None
        
        print(f"\n{'='*50}")
        print(f"[Pipeline:{self.name}] 执行{'成功' if success else '失败'}")
        print(f"[Pipeline] 总耗时: {total_duration:.2f}ms")
        print(f"{'='*50}\n")
        
        result = PipelineResult(
            success=success,
            context=context,
            execution_log=execution_log,
            total_duration_ms=total_duration,
            final_node=final_node,
            error=error_msg
        )
        
        self._trigger_hooks('on_complete', result=result)
        
        return result
    
    def visualize(self) -> str:
        """
        生成工作流可视化文本
        
        Returns:
            str: 工作流结构描述
        """
        lines = [f"工作流: {self.name}", "=" * 40]
        
        if self.start_node:
            lines.append(f"起始节点: {self.start_node}")
        
        lines.append(f"节点总数: {len(self.nodes)}")
        lines.append("-" * 40)
        
        for name, node in self.nodes.items():
            lines.append(f"\n节点: {name}")
            if node.description:
                lines.append(f"  描述: {node.description}")
            if node.next_node:
                lines.append(f"  下一节点: {node.next_node}")
            if node.condition_field:
                lines.append(f"  条件分支: {node.condition_field}")
                lines.append(f"    True  -> {node.condition_true}")
                lines.append(f"    False -> {node.condition_false}")
        
        return "\n".join(lines)
