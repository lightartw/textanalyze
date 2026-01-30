"""
Agent: DailySummaryAgent - 每日综合分析报告智能体
负责生成包含长短期风险评估的每日综合分析报告
"""
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

import config
from .base_agent import BaseAgent, AgentResult
from database import EventRepository


class DailySummaryAgent(BaseAgent):
    """每日综合分析报告智能体，生成长短期风险评估和重点事件分析。"""

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行每日综合分析
        
        Args:
            context: 包含分析参数的上下文字典
                - date: 分析日期（可选，默认当天）
                - days_back: 分析的历史天数（可选，默认7天）
                - max_events: 最大分析事件数（可选，默认50）
                - oil_related_only: 是否只分析油价相关事件（可选，默认True）
                
        Returns:
            AgentResult: 包含综合分析结果的标准化对象
        """
        # 解析参数
        analysis_date = context.get("date", datetime.now().strftime("%Y-%m-%d"))
        days_back = context.get("days_back", config.DAILY_REPORT_DAYS_BACK)
        max_events = context.get("max_events", config.DAILY_REPORT_MAX_EVENTS)
        oil_related_only = context.get("oil_related_only", True)
        
        try:
            # 从数据库读取事件数据
            repository = EventRepository(config.DATABASE_PATH)
            events = repository.get_all(
                oil_related_only=oil_related_only,
                limit=max_events
            )
            
            if not events:
                return AgentResult(
                    success=False,
                    error="数据库中没有符合条件的事件数据"
                )
            
            # 数据预处理和质量检查
            processed_events = self._process_events(events)
            
            # 计算事件统计指标
            event_metrics = self._calculate_event_metrics(processed_events)
            
            # 构建提示词
            prompt = self.build_prompt({
                "analysis_date": analysis_date,
                "days_back": days_back,
                "events": processed_events,
                "total_events": len(processed_events),
                "event_metrics": event_metrics
            })
            
            # 调用LLM
            result = self.llm.call_with_prompt(prompt, temperature=0.3, timeout=120)
            if result.get("status") != "success":
                return AgentResult(
                    success=False,
                    error=result.get("error", "LLM调用失败")
                )
            
            # 解析响应
            response_text = result.get("content", "")
            parsed = self.parse_json_response(response_text)
            
            # 验证结果
            if not parsed:
                return AgentResult(
                    success=False,
                    error="LLM响应解析失败"
                )
            
            # 结果后处理和验证
            validated_result = self._validate_and_enhance_result(parsed, processed_events)
            
            return AgentResult(
                success=True,
                data={
                    "analysis_date": analysis_date,
                    "short_term_risk": validated_result.get("short_term_risk", {}),
                    "long_term_risk": validated_result.get("long_term_risk", {}),
                    "key_events": validated_result.get("key_events", []),
                    "market_overview": validated_result.get("market_overview", ""),
                    "event_correlation": validated_result.get("event_correlation", ""),
                    "risk_mitigation": validated_result.get("risk_mitigation", ""),
                    "oil_price_strategies": validated_result.get("oil_price_strategies", {}),
                    "total_events_analyzed": len(processed_events),
                    "event_metrics": event_metrics
                },
                reasoning=response_text,
            )
        except Exception as e:
            self.log(f"分析过程中发生错误: {str(e)}")
            return AgentResult(
                success=False,
                error=f"分析过程中发生错误: {str(e)}"
            )
    
    def _process_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理事件数据，确保数据质量和一致性
        
        Args:
            events: 原始事件列表
            
        Returns:
            List[Dict[str, Any]]: 处理后的事件列表
        """
        processed_events = []
        
        for event in events:
            # 确保事件数据的完整性
            processed_event = {
                "id": event.get("id", ""),
                "title": event.get("title", ""),
                "date": event.get("date", ""),
                "event_type": event.get("event_type", ""),
                "is_oil_related": event.get("is_oil_related", False),
                "sentiment": event.get("sentiment", 0),
                "intensity": event.get("intensity", 0),
                "confidence": event.get("confidence", 0),
                "keywords": event.get("keywords", []),
                "transmission_path": event.get("transmission_path", ""),
                "content": event.get("content", ""),
                "category": event.get("category", "")
            }
            
            # 数据类型验证和转换
            if isinstance(processed_event["sentiment"], str):
                try:
                    processed_event["sentiment"] = float(processed_event["sentiment"])
                except:
                    processed_event["sentiment"] = 0
            
            if isinstance(processed_event["intensity"], str):
                try:
                    processed_event["intensity"] = float(processed_event["intensity"])
                except:
                    processed_event["intensity"] = 0
            
            if isinstance(processed_event["confidence"], str):
                try:
                    processed_event["confidence"] = float(processed_event["confidence"])
                except:
                    processed_event["confidence"] = 0
            
            # 确保数值在合理范围内
            processed_event["sentiment"] = max(-1.0, min(1.0, processed_event["sentiment"]))
            processed_event["intensity"] = max(0.0, min(1.0, processed_event["intensity"]))
            processed_event["confidence"] = max(0.0, min(1.0, processed_event["confidence"]))
            
            processed_events.append(processed_event)
        
        # 按日期排序，确保最新的事件在前面
        processed_events.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return processed_events
    
    def _calculate_event_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算事件的统计指标
        
        Args:
            events: 处理后的事件列表
            
        Returns:
            Dict[str, Any]: 事件统计指标
        """
        if not events:
            return {}
        
        # 计算情绪平均值
        sentiments = [e.get("sentiment", 0) for e in events]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # 计算强度平均值
        intensities = [e.get("intensity", 0) for e in events]
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0
        
        # 计算置信度平均值
        confidences = [e.get("confidence", 0) for e in events]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # 统计事件类型分布
        event_types = {}
        for event in events:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # 统计情绪分布
        sentiment_distribution = {
            "positive": len([s for s in sentiments if s > 0]),
            "negative": len([s for s in sentiments if s < 0]),
            "neutral": len([s for s in sentiments if s == 0])
        }
        
        return {
            "average_sentiment": avg_sentiment,
            "average_intensity": avg_intensity,
            "average_confidence": avg_confidence,
            "total_events": len(events),
            "event_type_distribution": event_types,
            "sentiment_distribution": sentiment_distribution,
            "most_common_event_type": max(event_types, key=event_types.get) if event_types else "unknown",
            "dominant_sentiment": self._get_dominant_sentiment(sentiment_distribution)
        }
    
    def _get_dominant_sentiment(self, sentiment_distribution: Dict[str, int]) -> str:
        """
        获取主导情绪
        
        Args:
            sentiment_distribution: 情绪分布
            
        Returns:
            str: 主导情绪
        """
        if not sentiment_distribution:
            return "neutral"
        
        max_count = max(sentiment_distribution.values())
        dominant_sentiments = [k for k, v in sentiment_distribution.items() if v == max_count]
        
        if len(dominant_sentiments) > 1:
            return "mixed"
        return dominant_sentiments[0]
    
    def _validate_and_enhance_result(self, result: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证和增强LLM返回的结果
        
        Args:
            result: LLM返回的原始结果
            events: 处理后的事件列表
            
        Returns:
            Dict[str, Any]: 验证和增强后的结果
        """
        # 确保必要的字段存在
        required_fields = ["market_overview", "short_term_risk", "long_term_risk", "key_events", "event_correlation"]
        for field in required_fields:
            if field not in result:
                if field in ["short_term_risk", "long_term_risk"]:
                    result[field] = {
                        "assessment": "",
                        "forecast": "",
                        "risk_factors": [],
                        "risk_level": "低",
                        "confidence": 0.5,
                        "key_metrics": {}
                    }
                elif field == "key_events":
                    result[field] = []
                else:
                    result[field] = ""
        
        # 确保油价风险应对策略字段存在
        if "oil_price_strategies" not in result:
            result["oil_price_strategies"] = {
                "short_term": "",
                "long_term": "",
                "by_stakeholder": {
                    "producers": "",
                    "consumers": "",
                    "investors": "",
                    "policymakers": ""
                },
                "monitoring_system": ""
            }
        
        # 验证风险等级
        for risk_type in ["short_term_risk", "long_term_risk"]:
            if risk_type in result:
                risk_level = result[risk_type].get("risk_level", "")
                if risk_level not in ["低", "中", "高"]:
                    result[risk_type]["risk_level"] = "低"
                
                # 确保置信度在合理范围内
                confidence = result[risk_type].get("confidence", 0.5)
                result[risk_type]["confidence"] = max(0.0, min(1.0, confidence))
        
        return result

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """
        构建每日综合分析提示词
        
        Args:
            context: 包含分析参数和事件数据的上下文字典
                - analysis_date: 分析日期
                - days_back: 分析的历史天数
                - events: 事件列表
                - total_events: 事件总数
                
        Returns:
            str: 格式化后的提示词
        """
        analysis_date = context.get("analysis_date")
        days_back = context.get("days_back")
        events = context.get("events", [])
        total_events = context.get("total_events", 0)
        
        # 准备事件数据
        events_data = []
        for i, event in enumerate(events[:20], 1):  # 最多使用20个事件进行分析
            event_info = {
                "id": i,
                "title": event.get("title", ""),
                "date": event.get("date", ""),
                "event_type": event.get("event_type", ""),
                "is_oil_related": event.get("is_oil_related", False),
                "sentiment": event.get("sentiment", 0),
                "intensity": event.get("intensity", 0),
                "confidence": event.get("confidence", 0),
                "keywords": event.get("keywords", []),
                "transmission_path": event.get("transmission_path", "")
            }
            events_data.append(event_info)
        
        events_json = json.dumps(events_data, ensure_ascii=False, indent=2)
        
        # 准备事件统计指标
        event_metrics = context.get("event_metrics", {})
        event_metrics_json = json.dumps(event_metrics, ensure_ascii=False, indent=2)
        
        return f"""你是资深的石油市场分析师，负责生成每日石油市场综合分析报告。请根据以下事件数据和统计指标，使用科学严谨的分析方法，生成一份详细的每日综合分析报告。

## 分析方法论

请按照以下科学分析框架进行分析：

1. **数据驱动分析**：基于提供的事件数据，避免无根据的猜测
2. **多维度评估**：从供给、需求、地缘政治、宏观经济等多个维度进行分析
3. **风险量化**：对风险进行系统化评估，提供具体的风险等级和置信度
4. **逻辑严谨性**：确保分析逻辑连贯，论据充分，结论合理
5. **科学预测**：基于历史数据和当前事件，进行合理的趋势预测

## 分析任务

1. **市场总体概况**：
   - 基于过去{days_back}天的事件，分析当前石油市场的整体状况
   - 识别市场的主要趋势和特征
   - 分析市场情绪和预期
   - 提供市场概况的综合评估

2. **短期风险评估**（1-7天）：
   - 评估当前事件对油价的短期影响
   - 基于事件的情绪极性和冲击强度，预测短期油价走势
   - 识别关键的短期风险因素，分析其影响机制
   - 运用风险矩阵方法，给出短期风险等级（低、中、高）
   - 计算风险评估的置信度（0-1）

3. **长期风险评估**（7-30天）：
   - 评估当前事件对油价的长期影响
   - 分析事件的传导路径和滞后效应
   - 预测长期油价走势和可能的波动范围
   - 识别关键的长期风险因素，分析其可持续性
   - 运用风险矩阵方法，给出长期风险等级（低、中、高）
   - 计算风险评估的置信度（0-1）

4. **重点事件识别**：
   - 基于影响强度、持续时间和市场关注度，识别最需关注的5个事件
   - 对每个重点事件进行详细分析，包括其性质、影响范围和潜在后果
   - 解释为什么这些事件值得特别关注
   - 分析每个重点事件的发展趋势和可能的演变
   - 针对每个重点事件，提供具体的监控建议

5. **事件关联性分析**：
   - 运用系统分析方法，分析不同事件之间的关联性
   - 识别可能的连锁反应和级联效应
   - 评估事件组合的综合影响，分析协同效应
   - 构建事件关联网络，识别关键节点事件
   - 分析事件之间的因果关系，避免虚假关联

6. **油价风险应对策略**：
   - 针对识别出的短期风险，提供具体的应急应对措施
   - 针对识别出的长期风险，提供战略性的风险管理建议
   - 按风险类型（供给风险、需求风险、地缘政治风险、金融风险等）提供分类建议
   - 为不同类型的市场参与者（生产者、消费者、投资者、政策制定者）提供定制化建议
   - 建议应具有可操作性，包括具体的行动步骤和实施时机

7. **监控指标与预警系统**：
   - 建议关键的监控指标，用于跟踪风险的发展
   - 设计简单的预警系统，用于及时识别新的风险
   - 提供监控频率和阈值建议

## 输入数据

分析日期：{analysis_date}
分析范围：过去{days_back}天
事件总数：{total_events}

事件统计指标：
{event_metrics_json}

事件数据：
{events_json}

## 输出格式

请严格输出以下格式的JSON：

{{
  "market_overview": "市场总体概况...",
  "short_term_risk": {{
    "assessment": "短期风险评估...",
    "forecast": "短期油价走势预测...",
    "risk_factors": ["风险因素1", "风险因素2", ...],
    "risk_level": "低/中/高",
    "confidence": 0.85,
    "key_metrics": {{
      "sentiment_average": 0.5,
      "intensity_average": 0.6,
      "market_volatility": "低/中/高"
    }}
  }},
  "long_term_risk": {{
    "assessment": "长期风险评估...",
    "forecast": "长期油价走势预测...",
    "risk_factors": ["风险因素1", "风险因素2", ...],
    "risk_level": "低/中/高",
    "confidence": 0.75,
    "key_metrics": {{
      "trend_strength": "弱/中/强",
      "fundamental_balance": "供过于求/平衡/供不应求",
      "geopolitical_stability": "稳定/不稳定/非常不稳定"
    }}
  }},
  "key_events": [
    {{
      "id": 1,
      "title": "事件标题",
      "reason": "值得关注的原因",
      "potential_impact": "潜在影响",
      "suggested_action": "建议采取的行动",
      "monitoring_metrics": ["监控指标1", "监控指标2"]
    }},
    ...
  ],
  "event_correlation": "事件关联性分析...",
  "risk_mitigation": "风险缓解建议...",
  "oil_price_strategies": {{
    "short_term": "短期应对策略...",
    "long_term": "长期战略建议...",
    "by_stakeholder": {{
      "producers": "生产者建议...",
      "consumers": "消费者建议...",
      "investors": "投资者建议...",
      "policymakers": "政策制定者建议..."
    }},
    "monitoring_system": "监控指标与预警系统建议..."
  }}
}}

## 分析要求

1. **科学性**：采用科学的分析方法和框架，确保分析的客观性和可靠性。
2. **严谨性**：逻辑推理严谨，论据充分，结论合理，避免主观臆断。
3. **全面性**：从多个维度进行分析，考虑所有相关因素的影响。
4. **深度**：分析具有深度，不仅描述现象，还要解释原因、机制和可能的后果。
5. **准确性**：基于提供的数据进行分析，引用具体的事件和数据支持结论。
6. **实用性**：提供的建议具有可操作性，能够实际应用于风险管理。
7. **清晰性**：分析结构清晰，逻辑连贯，表达准确，易于理解。

请开始分析并输出JSON格式的结果。"""
