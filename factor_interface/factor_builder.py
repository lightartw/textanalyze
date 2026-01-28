"""
因子构建接口
输出符合因子组规范的时间序列
"""
from typing import Dict, Any, List
import pandas as pd


def build_factor_series(
    events: List[Dict[str, Any]],
    factor_name: str,
    frequency: str = "D",
) -> pd.Series:
    """
    将事件列表聚合为因子时间序列。

    Args:
        events: 事件列表，包含 event_date 与 factor_value
        factor_name: 因子名称，如 geopolitical_risk_factor_v1
        frequency: 时间频率，D(日) / M(月)

    Returns:
        pd.Series: DatetimeIndex 的因子序列
    """
    if not events:
        return pd.Series(name=factor_name, dtype="float64")

    df = pd.DataFrame(events)
    df["event_date"] = pd.to_datetime(df["event_date"])
    df = df.set_index("event_date")
    series = df["factor_value"].resample(frequency).mean()
    series.name = factor_name
    return series
