"""
文本因子分类Agent
负责识别新闻是否与油价相关，并归类因子类型
"""
from typing import Dict, Any, List

import config
from .base_agent import BaseAgent, AgentResult
from factor_interface.factor_schema import TEXT_FACTOR_CATEGORIES


class TextFactorClassifier(BaseAgent):
    """Agent1：文本因子分类与关联性判断。"""

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
        category = parsed.get("factor_category", "unrelated")
        confidence = float(parsed.get("confidence", 0))
        is_related = bool(parsed.get("is_oil_related", False))

        if category not in TEXT_FACTOR_CATEGORIES:
            category = "unrelated"
            is_related = False

        if confidence < config.CLASSIFY_CONFIDENCE_THRESHOLD:
            is_related = False

        return AgentResult(
            success=True,
            data={
                "is_oil_related": is_related,
                "factor_category": category,
                "confidence": confidence,
                "keywords_found": parsed.get("keywords_found", []),
                "brief_reason": parsed.get("brief_reason", ""),
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建分类提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        category_desc = "\n".join(
            [f"- {key}: {meta['name']}" for key, meta in TEXT_FACTOR_CATEGORIES.items()]
        )
        
        res = f"""你是油价市场分析师，请判断新闻是否与油价相关，并归类为因子类型。
            因子分类列表：
            {category_desc}

            新闻标题：{title}
            新闻正文：
            {content}

            请输出JSON，字段如下：
            {{
            "is_oil_related": true/false,
            "factor_category": "分类名",
            "confidence": 0.0-1.0,
            "keywords_found": ["关键词1", "关键词2"],
            "brief_reason": "简要说明"
            }}
            仅输出JSON。"""
        return res
