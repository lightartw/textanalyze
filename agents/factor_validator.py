"""
因子有效性验证Agent
负责结合历史事件对因子量化结果进行校验
"""
from typing import Dict, Any, List

import config
from .base_agent import BaseAgent, AgentResult


class FactorValidator(BaseAgent):
    """Agent3：因子有效性校验与调整。"""

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        if not context.get("content"):
            return AgentResult(success=False, error="缺少新闻正文")

        prompt = self.build_prompt(context)
        result = self.llm.call_with_prompt(prompt, temperature=0.1, timeout=40)
        if result.get("status") != "success":
            return AgentResult(success=False, error=result.get("error", "LLM调用失败"))

        response_text = result.get("content", "")
        parsed = self.parse_json_response(response_text)
        adjusted_value = float(parsed.get("adjusted_factor_value", context.get("factor_value", 0)))
        adjusted_value = max(config.FACTOR_VALUE_MIN, min(config.FACTOR_VALUE_MAX, adjusted_value))

        return AgentResult(
            success=True,
            data={
                "is_valid": bool(parsed.get("is_valid", True)),
                "adjusted_factor_value": adjusted_value,
                "adjustment_reason": parsed.get("adjustment_reason", ""),
                "historical_consistency": parsed.get("historical_consistency", ""),
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建因子校验提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        category = context.get("factor_category", "unrelated")
        factor_value = context.get("factor_value", 0)
        similar_events = context.get("similar_events", [])

        history_lines: List[str] = []
        for event in similar_events[: config.SIMILAR_EVENTS_LIMIT]:
            history_lines.append(
                f"- {event.get('title', '')} | 值={event.get('factor_value', 0)}"
            )
        history_text = "\n".join(history_lines) if history_lines else "无"

        return (
            "你是因子质量审核专家，请验证因子量化结果。\n\n"
            f"因子分类：{category}\n"
            f"当前因子值：{factor_value}\n"
            f"历史同类事件：\n{history_text}\n\n"
            f"新闻标题：{title}\n"
            "新闻正文：\n"
            f"{content}\n\n"
            "输出JSON：\n"
            "{\n"
            '  "is_valid": true/false,\n'
            '  "adjusted_factor_value": 数值,\n'
            '  "adjustment_reason": "调整原因(如有)",\n'
            '  "historical_consistency": "与历史的一致性说明"\n'
            "}\n"
            "仅输出JSON。"
        )
