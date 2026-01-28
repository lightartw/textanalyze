# agents/base_agent.py
"""
Agent基类定义
所有Agent都继承自BaseAgent，实现统一的接口规范
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import json
import re


@dataclass
class AgentResult:
    """Agent执行结果的标准数据结构"""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""  # LLM推理过程
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "reasoning": self.reasoning,
            "error": self.error
        }


class BaseAgent(ABC):
    """
    Agent基类
    
    每个Agent负责一个特定的分析任务，通过LLM完成推理
    """
    
    def __init__(self, llm_client):
        """
        初始化Agent
        
        Args:
            llm_client: LLM客户端实例，用于调用大模型
        """
        self.llm = llm_client
        self.name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行Agent的核心逻辑
        
        Args:
            context: 包含所有必要信息的上下文字典
            
        Returns:
            AgentResult: 包含执行结果的标准化对象
        """
        pass
    
    @abstractmethod
    def build_prompt(self, context: Dict[str, Any]) -> str:
        """
        构建发送给LLM的提示词
        
        Args:
            context: 上下文信息
            
        Returns:
            str: 格式化后的提示词
        """
        pass
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        从LLM响应中解析JSON
        
        Args:
            response: LLM返回的原始文本
            
        Returns:
            Dict: 解析后的JSON对象，解析失败返回空字典
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试从markdown代码块中提取
        json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, response)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # 尝试提取 {...} 部分
        brace_pattern = r'\{[\s\S]*\}'
        matches = re.findall(brace_pattern, response)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        return {}
    
    def log(self, message: str):
        """输出日志信息"""
        print(f"[{self.name}] {message}")
