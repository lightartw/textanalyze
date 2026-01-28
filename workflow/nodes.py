# workflow/nodes.py
"""
工作流节点定义
每个节点代表工作流中的一个处理步骤
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any, List
from enum import Enum


class NodeStatus(Enum):
    """节点执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    """节点执行结果"""
    status: NodeStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    next_node: Optional[str] = None  # 动态指定下一节点
    
    @property
    def success(self) -> bool:
        return self.status == NodeStatus.SUCCESS
    
    @property
    def should_skip(self) -> bool:
        return self.status == NodeStatus.SKIPPED


@dataclass
class WorkflowNode:
    """
    工作流节点
    
    Attributes:
        name: 节点唯一标识
        handler: 节点处理函数，接收context返回NodeResult
        description: 节点描述
        next_node: 默认下一个节点
        condition_field: 条件判断字段名
        condition_true: 条件为True时的下一节点
        condition_false: 条件为False时的下一节点
        retry_count: 失败重试次数
    """
    name: str
    handler: Callable[[Dict[str, Any]], NodeResult]
    description: str = ""
    next_node: Optional[str] = None
    condition_field: Optional[str] = None
    condition_true: Optional[str] = None
    condition_false: Optional[str] = None
    retry_count: int = 0
    
    def execute(self, context: Dict[str, Any]) -> NodeResult:
        """
        执行节点
        
        Args:
            context: 工作流上下文
            
        Returns:
            NodeResult: 执行结果
        """
        attempts = 0
        max_attempts = self.retry_count + 1
        last_error = None
        
        while attempts < max_attempts:
            try:
                result = self.handler(context)
                return result
            except Exception as e:
                last_error = str(e)
                attempts += 1
                if attempts < max_attempts:
                    print(f"[{self.name}] 执行失败，重试 {attempts}/{self.retry_count}: {e}")
        
        return NodeResult(
            status=NodeStatus.FAILED,
            error=f"节点执行失败（重试{self.retry_count}次）: {last_error}"
        )
    
    def get_next_node(self, context: Dict[str, Any], result: NodeResult) -> Optional[str]:
        """
        确定下一个节点
        
        Args:
            context: 当前上下文
            result: 当前节点执行结果
            
        Returns:
            str: 下一个节点名称，None表示结束
        """
        # 优先使用结果中动态指定的下一节点
        if result.next_node:
            return result.next_node
        
        # 条件分支
        if self.condition_field:
            condition_value = context.get(self.condition_field, False)
            if condition_value:
                return self.condition_true
            else:
                return self.condition_false
        
        # 默认下一节点
        return self.next_node


class NodeBuilder:
    """
    节点构建器，提供流式API创建节点
    """
    
    def __init__(self, name: str):
        self._name = name
        self._handler = None
        self._description = ""
        self._next_node = None
        self._condition_field = None
        self._condition_true = None
        self._condition_false = None
        self._retry_count = 0
    
    def handler(self, func: Callable) -> 'NodeBuilder':
        self._handler = func
        return self
    
    def description(self, desc: str) -> 'NodeBuilder':
        self._description = desc
        return self
    
    def then(self, next_node: str) -> 'NodeBuilder':
        self._next_node = next_node
        return self
    
    def branch(
        self, 
        condition_field: str, 
        if_true: str, 
        if_false: str
    ) -> 'NodeBuilder':
        self._condition_field = condition_field
        self._condition_true = if_true
        self._condition_false = if_false
        return self
    
    def retry(self, count: int) -> 'NodeBuilder':
        self._retry_count = count
        return self
    
    def build(self) -> WorkflowNode:
        if not self._handler:
            raise ValueError(f"节点 {self._name} 缺少处理函数")
        
        return WorkflowNode(
            name=self._name,
            handler=self._handler,
            description=self._description,
            next_node=self._next_node,
            condition_field=self._condition_field,
            condition_true=self._condition_true,
            condition_false=self._condition_false,
            retry_count=self._retry_count
        )
