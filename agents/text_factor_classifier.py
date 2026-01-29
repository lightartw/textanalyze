"""
Agent1: EventClassifier - 事件分类器
负责识别新闻是否与油价相关，判断事件类型
"""
from typing import Dict, Any, List

import config
from .base_agent import BaseAgent, AgentResult
from factor_interface.factor_schema import EVENT_TYPES


class EventClassifier(BaseAgent):
    """Agent1：事件分类与油价关联性判断。"""

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
        
        event_type = parsed.get("event_type")
        is_related = bool(parsed.get("is_oil_related", False))
        keywords = parsed.get("keywords", [])

        # 验证event_type有效性
        if event_type not in EVENT_TYPES and event_type is not None:
            event_type = None
            is_related = False

        return AgentResult(
            success=True,
            data={
                "event_type": event_type,
                "keywords": keywords,
                "is_oil_related": is_related,
            },
            reasoning=response_text,
        )

    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建事件分类提示词。"""
        title = context.get("title", "")
        content = context.get("content", "")[: config.MAX_CONTENT_LENGTH]
        
        return f"""你是油价市场事件分类专家。请按照以下操作步骤判断新闻是否与油价相关，并识别事件类型。

## 操作步骤

### 步骤1: 判断是否石油/能源相关
- 识别句子中是否包含石油、原油、能源、油价、WTI、Brent等关键词
- 如果句子与石油/能源/油价无直接关联，直接返回 `{{"event_type": null, "keywords": [], "is_oil_related": false}}`
- 仅在确认石油相关后继续分类

### 步骤2: 识别事件类型
- 逐类检查句子是否包含对应事件的特征词汇和语义
- 如果句子涉及多个事件类型，选择最显著的主导类型
- 如果句子不涉及任何可识别的七类事件，但明显影响油价，归为 `other`（其他因素）
- 如果句子与石油无关或不影响油价，返回 `null`

### 步骤3: 提取关键词
- 从原文中提取与识别到的事件类型直接相关的关键词
- 关键词必须来自原文，不得添加或修改
- 提取2-5个最具代表性的关键词

### 步骤4: 生成JSON输出
- 严格遵循输出格式，不得添加额外字段或说明
- 确保JSON格式正确，逗号和引号规范

## 事件类型定义

### 可识别的八类事件

1. **地缘政治 (geopolitical)**
   - 战争、冲突、军事行动
   - 制裁、贸易限制
   - OPEC决策、产量协议
   - 管道袭击、设施破坏
   - 关键产油国政治变动

2. **宏观经济 (macro)**
   - GDP、经济增长数据
   - 利率、货币政策
   - PMI、就业数据
   - 通胀、汇率波动
   - 经济衰退或复苏信号

3. **市场情绪 (sentiment)**
   - 恐慌、担忧、乐观
   - 投机行为、仓位调整
   - 看涨、看跌预期
   - 抛售、抢购
   - 风险偏好变化

4. **极端天气 (weather)**
   - 飓风、台风
   - 寒潮、热浪
   - 洪水、干旱
   - 炼厂停工、生产中断
   - 需求异常（如取暖/制冷需求）

5. **库存变化 (inventory)**
   - 原油、成品油库存增减
   - 商业库存数据发布
   - 战略储备释放
   - 库存超预期或低于预期

6. **政策因素 (policy)**
   - 能源政策调整
   - 税收政策变化
   - 出口配额、进口关税
   - 环保法规、碳排放限制
   - 石油补贴调整

7. **技术进步 (technology)**
   - 开采技术突破
   - 炼油技术改进
   - 新能源技术发展
   - 提高采收率技术
   - 数字化、自动化应用

8. **其他因素 (other)**
   - 不属于前七类但明显影响油价的因素
   - 包括：替代能源发展、供需基本面、贸易摩擦、地缘紧张局势（非制裁）、能源转型等

## 输入数据

新闻标题：{title}
新闻正文：
{content}

## 输出格式

仅返回严格符合以下格式的JSON：

{{
  "event_type": "geopolitical|macro|sentiment|weather|inventory|policy|technology|other|null",
  "keywords": ["关键词1", "关键词2"],
  "is_oil_related": true|false
}}

## 注意事项

- 严格按输出格式返回JSON，不要添加任何解释或额外字段
- 关键词必须从原文中提取，不得杜撰
- 仅识别输出格式中定义的八类事件，其他不影响油价的情况返回 `null`
- 若句子与石油无直接关联，即使包含可识别事件也返回 `null`
- 优先识别最显著的事件类型，避免模糊分类

## 示例

### 示例1: 地缘政治事件
输入: "OPEC+宣布从5月起自愿减产116万桶/日"
输出: `{{"event_type": "geopolitical", "keywords": ["OPEC+", "减产"], "is_oil_related": true}}`

### 示例2: 宏观经济事件
输入: "美联储加息25个基点，经济放缓担忧加剧"
输出: `{{"event_type": "macro", "keywords": ["美联储", "加息", "经济放缓"], "is_oil_related": true}}`

### 示例3: 非石油相关
输入: "苹果公司发布新款iPhone，股价上涨5%"
输出: `{{"event_type": null, "keywords": [], "is_oil_related": false}}`

请开始分析并输出JSON结果。"""
