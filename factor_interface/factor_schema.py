"""
文本因子分类规范
用于与因子组对接时保持统一字段
"""

TEXT_FACTOR_CATEGORIES = {
    "geopolitical_risk": {
        "name": "地缘政治风险",
        "description": "战争、冲突、制裁等导致供应风险上升",
    },
    "supply_signal": {
        "name": "供给信号",
        "description": "产量、出口、管道与供应侧变化",
    },
    "demand_signal": {
        "name": "需求信号",
        "description": "需求强弱、消费、库存变化",
    },
    "opec_policy": {
        "name": "OPEC政策",
        "description": "OPEC/欧佩克配额、减产增产政策",
    },
    "macro_economic": {
        "name": "宏观经济",
        "description": "GDP、通胀、利率、美元等宏观信号",
    },
    "inventory_signal": {
        "name": "库存信号",
        "description": "EIA/API库存与储备相关数据",
    },
    "unrelated": {
        "name": "无关",
        "description": "与油价无关的新闻",
    },
}
