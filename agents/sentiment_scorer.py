"""
Agent3: SentimentIntensityScorer - 情绪与强度评分器
负责评估事件的情绪极性、冲击强度、置信度
"""
from typing import Dict, Any
import json

import config
from .base_agent import BaseAgent, AgentResult


class SentimentIntensityScorer(BaseAgent):
    """Agent3：情绪与强度评分器，量化事件影响。"""

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        title = context.get("title", "")
        content = context.get("content", "")
        event_type = context.get("event_type", "")
        key_entities = context.get("key_entities", [])
        quantitative_metrics = context.get("quantitative_metrics", {})
        transmission_path = context.get("transmission_path", "")

        if not content:
            return AgentResult(success=False, error="缺少新闻正文")

        prompt = self.build_prompt(context)
        result = self.llm.call_with_prompt(prompt, temperature=0.2, timeout=60)
        if result.get("status") != "success":
            return AgentResult(success=False, error=result.get("error", "LLM调用失败"))

        response_text = result.get("content", "")
        parsed = self.parse_json_response(response_text)

        # 验证并约束数值范围
        sentiment = float(parsed.get("sentiment", 0))
        sentiment = max(-1.0, min(1.0, sentiment))
        
        intensity = float(parsed.get("intensity", 0))
        intensity = max(0.0, min(1.0, intensity))
        
        confidence = float(parsed.get("confidence", 0))
        confidence = max(0.0, min(1.0, confidence))

        return AgentResult(
            success=True,
            data={
                "sentiment": sentiment,
                "intensity": intensity,
                "confidence": confidence,
                "reasoning": parsed.get("reasoning", {}),
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建情绪评分提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        event_type = context.get("event_type", "")
        key_entities = context.get("key_entities", [])
        quantitative_metrics = context.get("quantitative_metrics", {})
        transmission_path = context.get("transmission_path", "")

        # TODO: 后续完善详细的情绪评分提示词
        return f"""你是石油市场量化分析师，请评估事件对油价的影响。

事件类型：{event_type}
关键实体：{key_entities}
量化指标：{json.dumps(quantitative_metrics, ensure_ascii=False)}
传导路径：{transmission_path}

新闻标题：{title}
新闻正文：
{content}

请评估以下指标：
1. sentiment（情绪极性）：-1.0到+1.0，正值利多，负值利空
2. intensity（冲击强度）：0.0到1.0，越大影响越大
3. confidence（置信度）：0.0到1.0，越大越可信

输出格式：
{{
  "sentiment": 0.8,
  "intensity": 0.85,
  "confidence": 0.85,
  "reasoning": {{
    "event_type": "事件类型描述",
    "sentiment_basis": "情绪判断依据",
    "intensity_basis": "强度判断依据",
    "confidence_breakdown": {{
      "信息完整性": 0.9,
      "历史事件匹配度": 0.9,
      "多维度一致性": 0.85,
      "市场预期偏离度": 0.8,
      "评估者经验权重": 0.8
    }},
    "historical_reference": "历史事件参考",
    "cross_validation": "交叉验证结果"
  }}
}}
仅输出JSON，不要添加任何解释。"""
