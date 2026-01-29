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

        return f"""你是石油市场量化分析师，请按照以下六步流程评估事件对油价的影响。

## 操作步骤

### 1. 理解事件内容
- 识别事件类型：供给端、需求端、地缘政治、宏观经济、其他
- 提取关键要素：涉及主体、影响方向、规模/数量、时间维度

### 2. 评估情绪极性(sentiment)
- 依据供给-需求框架判断：
  - 供给减少 / 需求增加 → 利多（正极性）
  - 供给增加 / 需求减少 → 利空（负极性）
- 量化规则：
  - ±1.0：极端利多/利空（如全面禁运、大规模战争）
  - ±0.7~0.9：显著影响（如重大减产、经济危机）
  - ±0.4~0.6：中度影响（如常规库存变化、季节性需求）
  - ±0.1~0.3：轻微影响（如短期波动、小规模事件）

### 3. 评估冲击强度(intensity)
- 评估维度：
  - 影响规模：波及全球/区域/局部
  - 持续时间：长期/中期/短期
  - 市场关注度：主导性因素/次要因素
- 量化规则：
  - 0.9~1.0：重大冲击（如2022俄乌冲突）
  - 0.6~0.8：强冲击（如OPEC+大规模减产）
  - 0.3~0.5：中度冲击（如库存超预期变化）
  - 0.0~0.2：轻微冲击（如短期扰动）

### 4. 评估置信度(confidence)
- 评估维度（各0-1分）：
  - **信息完整性**：事件描述的详细程度和关键信息齐全度
  - **历史事件匹配度**：与历史相似事件的匹配程度
  - **多维度一致性**：供给/需求/地缘/宏观多维度评估的一致性
  - **市场预期偏离度**：事件与市场预期的一致程度（一致则置信度高）
  - **评估者经验权重**：评估者对该类型事件的经验程度
- 量化规则：
  - 0.9~1.0：极高置信（信息完整，历史匹配度高，多维度一致）
  - 0.7~0.9：高置信（信息较完整，有历史参照，评估一致）
  - 0.5~0.7：中等置信（信息有限，部分维度不一致）
  - 0.3~0.5：低置信（信息模糊，缺乏历史参照）
  - 0.0~0.3：极低置信（信息严重不足，无法准确评估）

### 5. 多维度交叉验证
- 验证项：
  - 供给/需求/地缘/宏观多维度评估一致性检查
  - 与历史相似事件的评分对比
  - 市场价格预期的合理性校验
  - 评分边界条件检查（sentiment∈[-1,1]，intensity∈[0,1]，confidence∈[0,1]）
- 异常处理：发现不一致或异常时，需重新评估或调整置信度

### 6. 输出标准化结果
- 严格遵循 JSON 格式
- 必须包含字段：sentiment（情绪极性）、intensity（冲击强度）、confidence（置信度）、reasoning（评估推理）
- reasoning 字段包含：
  - 主要评估依据（事件类型、影响方向、规模判断）
  - 置信度各维度评分（信息完整性、历史匹配度、多维度一致性等）
  - 历史事件对比参考
  - 异常情况说明（如存在）

## 输入数据

事件类型：{event_type}
关键实体：{key_entities}
量化指标：{json.dumps(quantitative_metrics, ensure_ascii=False)}
传导路径：{transmission_path}

新闻标题：{title}
新闻正文：
{content}

## 输出格式

请严格输出以下格式的JSON：

{{
  "sentiment": 0.8,
  "intensity": 0.85,
  "confidence": 0.85,
  "reasoning": {{
    "event_type": "供给端冲击",
    "sentiment_basis": "供给减少100万桶/日，利多情绪明确",
    "intensity_basis": "影响规模占全球约1%，持续数月，市场关注度高",
    "confidence_breakdown": {{
      "信息完整性": 0.9,
      "历史事件匹配度": 0.9,
      "多维度一致性": 0.85,
      "市场预期偏离度": 0.8,
      "评估者经验权重": 0.8
    }},
    "historical_reference": "参考2020年OPEC减产事件（sentiment=0.75, intensity=0.7）",
    "cross_validation": "供需维度评估一致，与历史事件匹配度高"
  }}
}}

## 注意事项

- 严格按输出格式返回JSON，不要添加任何解释或额外字段
- 确保所有评分在有效范围内（sentiment∈[-1,1]，intensity∈[0,1]，confidence∈[0,1]）
- 必须执行多维度交叉验证，确保评分的可靠性
- reasoning字段必须详细记录评估依据，支持数据溯源
- 发现评分异常或维度不一致时，必须调整置信度并说明原因

请开始评估并输出JSON结果。"""
