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
                    "other_metrics": {
                        "price_impact": None,
                        "time_horizon": "短期"
                    }
                }),
                "transmission_path": parsed.get("transmission_path", ""),
                "confidence": parsed.get("confidence", "中"),
                "uncertainties": parsed.get("uncertainties", []),
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建IEA分析提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        event_type = context.get("event_type", "")
        keywords = context.get("keywords", [])

        return f"""你是国际能源署（IEA）高级分析师，请按照以下步骤分析事件与油价的因果链。

## 分析步骤

### 步骤1: 识别供需金三要素
- **供给要素**：石油生产、出口、库存、供应链等
- **需求要素**：经济增长、消费、工业活动、交通运输等
- **金融要素**：美元汇率、投机资金、市场情绪、地缘政治风险溢价等

### 步骤2: 提取关键实体
- **国家/地区**：涉及的主要国家或地区
- **组织**：OPEC、OPEC+、IEA、国际组织等
- **公司**：石油公司、贸易公司等
- **数据源**：EIA、API、OPEC等官方数据来源

### 步骤3: 分析量化指标
- **供应影响**：产量变化、出口量变化、供应中断规模等（桶/日）
- **需求影响**：需求增长/减少、消费变化等（桶/日）
- **库存变动**：商业库存、战略储备变化等（万桶）
- **其他指标**：价格变动预期、市场份额变化等

### 步骤4: 构建传导路径
- **原因**：事件的直接原因
- **中间环节**：影响供需平衡的具体机制
- **油价影响**：最终对油价的影响方向和程度

### 步骤5: 验证因果关系
- 确保传导路径逻辑清晰，每一步都有合理的因果关系
- 识别潜在的混杂变量或其他影响因素
- 评估事件影响的确定性和不确定性

## 输入数据

事件类型：{event_type}
关键词：{keywords}

新闻标题：{title}
新闻正文：
{content}

## 输出格式

请严格输出以下格式的JSON：

{{
  "reason": "满足的要素说明（供给/需求/金融）",
  "key_entities": ["实体1", "实体2", "实体3"],
  "quantitative_metrics": {{
    "supply_impact": "减产量/供应变动值（桶/日）或null",
    "demand_impact": "需求变动值（桶/日）或null",
    "inventory_change": "库存变动值（万桶）或null",
    "other_metrics": {{
      "price_impact": "价格影响预期（美元/桶）或null",
      "time_horizon": "影响时间范围（短期/中期/长期）"
    }}
  }},
  "transmission_path": "原因 → 中间环节 → 油价影响",
  "confidence": "分析置信度（高/中/低）",
  "uncertainties": ["不确定性因素1", "不确定性因素2"]
}}

## 注意事项

- 严格按输出格式返回JSON，不要添加任何解释或额外字段
- 尽可能提供具体的量化数据，无法确定时使用null
- 传导路径要逻辑清晰，体现完整的因果链条
- 识别并列出主要的不确定性因素
- 基于事实分析，避免主观臆断

请开始分析并输出JSON结果。"""
