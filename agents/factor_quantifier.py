"""
文本因子量化Agent
负责将新闻事件量化为因子值
"""
from typing import Dict, Any

import config
from .base_agent import BaseAgent, AgentResult


class FactorQuantifier(BaseAgent):
    """Agent2：因子强度量化（-1到+1）。"""

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        title = context.get("title", "")
        content = context.get("content", "")
        category = context.get("factor_category", "unrelated")

        if not content:
            return AgentResult(success=False, error="缺少新闻正文")

        prompt = self.build_prompt(context)
        result = self.llm.call_with_prompt(prompt, temperature=0.2, timeout=40)
        if result.get("status") != "success":
            return AgentResult(success=False, error=result.get("error", "LLM调用失败"))

        response_text = result.get("content", "")
        parsed = self.parse_json_response(response_text)
        factor_value = float(parsed.get("factor_value", 0))
        factor_value = max(config.FACTOR_VALUE_MIN, min(config.FACTOR_VALUE_MAX, factor_value))

        return AgentResult(
            success=True,
            data={
                "factor_category": category,
                "factor_value": factor_value,
                "impact_magnitude": parsed.get("impact_magnitude", "medium"),
                "time_horizon": parsed.get("time_horizon", "short"),
                "quantification_logic": parsed.get("quantification_logic", ""),
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建因子量化提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        category = context.get("factor_category", "unrelated")

        return (
            "你是石油市场量化分析师，请将新闻事件量化为因子值。\n"
            "量化范围为 -1.0 到 +1.0，正值表示利好油价，负值表示利空油价。\n\n"
            f"因子分类：{category}\n"
            f"新闻标题：{title}\n"
            "新闻正文：\n"
            f"{content}\n\n"
            "输出JSON：\n"
            "{\n"
            '  "factor_value": 数值,\n'
            '  "impact_magnitude": "low/medium/high",\n'
            '  "time_horizon": "short/medium/long",\n'
            '  "quantification_logic": "量化依据"\n'
            "}\n"
            "仅输出JSON。"
        )
