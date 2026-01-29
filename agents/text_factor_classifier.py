"""
Agent1: EventClassifier - 事件分类器
负责识别新闻是否与油价相关，判断事件类型
"""
from typing import Dict, Any, List

import config
from .base_agent import BaseAgent, AgentResult
from factor_interface.factor_schema import EVENT_TYPES


class EventClassifier(BaseAgent):
    """Agent1：事件分类与油价关联性判断。"""

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        title = context.get("title", "")
        content = context.get("content", "")
        if not title and not content:
            return AgentResult(success=False, error="缺少新闻标题或正文")

        prompt = self.build_prompt(context)
        result = self.llm.call_with_prompt(prompt, temperature=0.1, timeout=40)
        if result.get("status") != "success":
            return AgentResult(success=False, error=result.get("error", "LLM调用失败"))

        response_text = result.get("content", "")
        parsed = self.parse_json_response(response_text)
        
        event_type = parsed.get("event_type")
        is_related = bool(parsed.get("is_oil_related", False))
        keywords = parsed.get("keywords", [])

        # 验证event_type有效性
        if event_type not in EVENT_TYPES and event_type is not None:
            event_type = None
            is_related = False

        return AgentResult(
            success=True,
            data={
                "event_type": event_type,
                "keywords": keywords,
                "is_oil_related": is_related,
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建事件分类提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        
        # TODO: 后续完善详细的分类提示词
        return f"""你是油价市场事件分类专家。请判断新闻是否与油价相关，并识别事件类型。

事件类型（8类）：
- geopolitical: 地缘政治（战争、冲突、制裁、OPEC决策）
- macro: 宏观经济（GDP、利率、PMI、通胀）
- sentiment: 市场情绪（恐慌、抛售、投机）
- weather: 极端天气（飓风、寒潮、炼厂停工）
- inventory: 库存变化（EIA/API库存、战略储备）
- policy: 政策因素（能源政策、税收、配额）
- technology: 技术进步（开采技术、炼油技术）
- other: 其他因素（替代能源、供需基本面）

新闻标题：{title}
新闻正文：
{content}

请严格输出JSON格式：
{{
  "event_type": "geopolitical|macro|sentiment|weather|inventory|policy|technology|other|null",
  "keywords": ["关键词1", "关键词2"],
  "is_oil_related": true|false
}}
仅输出JSON，不要添加任何解释。"""
