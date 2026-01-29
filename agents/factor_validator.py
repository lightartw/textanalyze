"""
Agent4: CausalValidator - 因果验证器
负责验证"相关≠因果"，校准强度，输出最终结果
"""
from typing import Dict, Any, List
import json

import config
from .base_agent import BaseAgent, AgentResult


class CausalValidator(BaseAgent):
    """Agent4：因果推断验证器，校验因果关系与强度校准。"""

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        if not context.get("content"):
            return AgentResult(success=False, error="缺少新闻正文")

        prompt = self.build_prompt(context)
        result = self.llm.call_with_prompt(prompt, temperature=0.1, timeout=60)
        if result.get("status") != "success":
            return AgentResult(success=False, error=result.get("error", "LLM调用失败"))

        response_text = result.get("content", "")
        parsed = self.parse_json_response(response_text)
        
        # 约束adjusted_intensity范围
        adjusted_intensity = float(parsed.get("adjusted_intensity", context.get("intensity", 0)))
        adjusted_intensity = max(0.0, min(1.0, adjusted_intensity))
        
        # 约束confidence范围
        confidence = float(parsed.get("confidence", context.get("confidence", 0)))
        confidence = max(0.0, min(1.0, confidence))

        return AgentResult(
            success=True,
            data={
                "is_causal": bool(parsed.get("is_causal", True)),
                "adjusted_intensity": adjusted_intensity,
                "logic_analysis": parsed.get("logic_analysis", {}),
                "final_confidence": confidence,
                "warning": parsed.get("warning"),
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建因果验证提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        event_type = context.get("event_type", "")
        transmission_path = context.get("transmission_path", "")
        sentiment = context.get("sentiment", 0)
        intensity = context.get("intensity", 0)
        confidence = context.get("confidence", 0)
        reasoning = context.get("reasoning", {})
        similar_events = context.get("similar_events", [])

        # 格式化历史事件
        history_lines: List[str] = []
        for event in similar_events[: config.SIMILAR_EVENTS_LIMIT]:
            history_lines.append(
                f"- {event.get('title', '')[:50]} | intensity={event.get('adjusted_factor_value', 0)}"
            )
        history_text = "\n".join(history_lines) if history_lines else "无"

        # TODO: 后续完善详细的因果验证提示词
        return f"""你是因果推断专家，请验证事件与油价的因果关系。

事件类型：{event_type}
传导路径：{transmission_path}
当前评估：sentiment={sentiment}, intensity={intensity}, confidence={confidence}
评估推理：{json.dumps(reasoning, ensure_ascii=False)}

历史同类事件：
{history_text}

新闻标题：{title}
新闻正文：
{content}

请进行三重校验：
1. 传导路径是否完整？（事件→供给/需求/金融→油价）
2. 是否存在混杂变量？
3. 历史同类事件是否支持当前评分？

输出格式：
{{
  "is_causal": true|false,
  "adjusted_intensity": 0.75,
  "logic_analysis": {{
    "transmission_path_valid": true|false,
    "confounding_variables": ["混杂变量1", "混杂变量2"],
    "historical_consistency": "与历史的一致性说明"
  }},
  "confidence": 0.8,
  "warning": "警告信息或null"
}}
仅输出JSON，不要添加任何解释。"""
