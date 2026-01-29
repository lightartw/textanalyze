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
                "calibration_reasoning": parsed.get("calibration_reasoning"),
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

        return f"""你是诺贝尔经济学奖得主级别的因果推断专家，请严格按照以下流程验证事件与油价的因果关系。

## 因果推断流程

### 步骤1: 传导路径完整性验证
- **检查起点**：事件是否有明确的起始原因
- **检查中间环节**：是否有清晰的机制连接事件与油价
- **检查终点**：是否有明确的油价影响结果
- **验证标准**：传导路径必须包含至少两个中间环节，逻辑清晰

### 步骤2: 混杂变量识别
- **经济因素**：GDP、利率、通胀等宏观经济变量
- **地缘政治因素**：其他地区冲突、国际制裁等
- **市场因素**：投机资金、库存水平、OPEC决策等
- **时间因素**：季节性需求变化、周期性因素等

### 步骤3: 历史一致性分析
- **相似事件对比**：与历史同类事件的影响程度对比
- **模式识别**：识别历史上类似传导路径的结果
- **异常检测**：当前事件与历史模式的差异分析

### 步骤4: 强度校准
- **基于证据强度**：根据可用证据的质量和数量调整强度
- **基于不确定性**：考虑未知因素和潜在风险调整强度
- **基于历史参照**：参考历史事件的实际影响程度调整强度

### 步骤5: 因果关系判定
- **必要条件**：事件是否是油价变化的必要条件
- **充分条件**：事件是否是油价变化的充分条件
- **相关性 vs 因果性**：严格区分统计相关与因果关系
- **反事实分析**：如果没有该事件，油价是否会有相同变化

## 输入数据

事件类型：{event_type}
传导路径：{transmission_path}
当前评估：sentiment={sentiment}, intensity={intensity}, confidence={confidence}
评估推理：{json.dumps(reasoning, ensure_ascii=False)}

历史同类事件：
{history_text}

新闻标题：{title}
新闻正文：
{content}

## 输出格式

请严格输出以下格式的JSON：

{{
  "is_causal": true|false,
  "adjusted_intensity": 0.75,
  "logic_analysis": {{
    "transmission_path_valid": true|false,
    "path_issues": ["路径问题1", "路径问题2"],
    "confounding_variables": ["混杂变量1", "混杂变量2"],
    "historical_consistency": "与历史的一致性说明",
    "counterfactual_analysis": "反事实分析结果"
  }},
  "confidence": 0.8,
  "warning": "警告信息或null",
  "calibration_reasoning": "强度校准的详细理由"
}}

## 评估标准

- **因果关系判定**：
  - 强因果：有完整传导路径，无明显混杂变量，历史一致性高
  - 中等因果：传导路径基本完整，存在一些混杂变量，历史一致性中等
  - 弱因果：传导路径不完整，存在多个混杂变量，历史一致性低
  - 无因果：缺乏合理传导路径，或完全由其他因素驱动

- **强度校准标准**：
  - 高证据强度：多个独立数据源支持，逻辑清晰
  - 中等证据强度：部分数据源支持，逻辑基本清晰
  - 低证据强度：证据不足，逻辑存在漏洞

- **置信度评估**：
  - 高置信度：传导路径完整，混杂变量少，历史一致性高
  - 中等置信度：传导路径基本完整，存在一些混杂变量，历史一致性中等
  - 低置信度：传导路径不完整，混杂变量多，历史一致性低

## 注意事项

- 严格区分相关性与因果性，避免将时间上的关联误认为因果关系
- 充分考虑所有可能的混杂变量，不要只关注事件本身
- 参考历史事件但不盲目依赖，考虑当前市场环境的特殊性
- 强度校准要基于客观证据，避免主观臆断
- 保持科学严谨的态度，对不确定性保持诚实

请开始分析并输出JSON结果。"""
