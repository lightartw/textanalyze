"""
文本因子分类规范
用于与因子组对接时保持统一字段
"""

# 8类事件类型（与组件EventClassifier一致）
EVENT_TYPES = {
    "geopolitical": {
        "name": "地缘政治",
        "description": "战争、冲突、制裁、OPEC决策、管道袭击、产油国政治变动",
    },
    "macro": {
        "name": "宏观经济",
        "description": "GDP、利率、货币政策、PMI、就业、通胀、汇率、经济衰退/复苏",
    },
    "sentiment": {
        "name": "市场情绪",
        "description": "恐慌、担忧、乐观、投机、仓位调整、看涨/看跌预期",
    },
    "weather": {
        "name": "极端天气",
        "description": "飓风、台风、寒潮、热浪、洪水、干旱、炼厂停工",
    },
    "inventory": {
        "name": "库存变化",
        "description": "原油/成品油库存增减、EIA/API数据、战略储备释放",
    },
    "policy": {
        "name": "政策因素",
        "description": "能源政策、税收政策、出口配额、进口关税、环保法规",
    },
    "technology": {
        "name": "技术进步",
        "description": "开采技术突破、炼油技术改进、新能源技术、采收率提升",
    },
    "other": {
        "name": "其他因素",
        "description": "替代能源发展、供需基本面、贸易摩擦、能源转型等",
    },
}

# 保持向后兼容
TEXT_FACTOR_CATEGORIES = EVENT_TYPES
