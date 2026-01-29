"""
Agent2: IEA分析Agent - 实体与传导路径提取
负责提取供需金三要素实体、量化指标、传导路径
"""
from typing import Dict, Any

import config
from .base_agent import BaseAgent, AgentResult


class IEAAnalyzer(BaseAgent):
    """Agent2：IEA智能油价分析Agent，提取实体与传导路径。"""

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        title = context.get("title", "")
        content = context.get("content", "")
        event_type = context.get("event_type", "")
        keywords = context.get("keywords", [])

        if not content:
            return AgentResult(success=False, error="缺少新闻正文")

        prompt = self.build_prompt(context)
        result = self.llm.call_with_prompt(prompt, temperature=0.1, timeout=60)
        if result.get("status") != "success":
            return AgentResult(success=False, error=result.get("error", "LLM调用失败"))

        response_text = result.get("content", "")
        parsed = self.parse_json_response(response_text)

        return AgentResult(
            success=True,
            data={
                "reason": parsed.get("reason", ""),
                "key_entities": parsed.get("key_entities", []),
                "quantitative_metrics": parsed.get("quantitative_metrics", {
                    "supply_impact": None,
                    "demand_impact": None,
                    "inventory_change": None,
                    "other_metrics": {}
                }),
                "transmission_path": parsed.get("transmission_path", ""),
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建IEA分析提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        event_type = context.get("event_type", "")
        keywords = context.get("keywords", [])

        # TODO: 后续完善详细的IEA分析提示词
        return f"""你是国际能源署（IEA）高级分析师，请分析事件与油价的因果链。

事件类型：{event_type}
关键词：{keywords}

新闻标题：{title}
新闻正文：
{content}

请提取以下信息并输出JSON：
1. 判断依据（满足供给/需求/金融哪个要素）
2. 关键实体（国家、组织、数据源）
3. 量化指标（供应影响、需求影响、库存变动）
4. 传导路径（原因→中间环节→油价影响）

输出格式：
{{
  "reason": "满足的要素说明",
  "key_entities": ["实体1", "实体2"],
  "quantitative_metrics": {{
    "supply_impact": "减产量/供应变动值（桶/日）或null",
    "demand_impact": "需求变动值（桶/日）或null",
    "inventory_change": "库存变动值（万桶）或null",
    "other_metrics": {{}}
  }},
  "transmission_path": "原因 → 中间环节 → 油价影响"
}}
仅输出JSON，不要添加任何解释。"""
