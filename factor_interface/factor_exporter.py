"""
因子结果导出
输出CSV与说明文档，供因子组调用
"""
from typing import Dict, Any
import os
import pandas as pd


def export_factor_csv(series: pd.Series, output_dir: str) -> str:
    """导出因子时间序列为CSV。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = f"{series.name}.csv"
    filepath = os.path.join(output_dir, filename)
    df = series.reset_index()
    df.columns = ["date", series.name]
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath


def export_factor_doc(doc: Dict[str, Any], output_dir: str) -> str:
    """导出因子说明文档为文本。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    factor_name = doc.get("factor_name", "factor_doc")
    filepath = os.path.join(output_dir, f"{factor_name}.txt")
    lines = [
        f"因子名称: {doc.get('factor_name', '')}",
        f"数据来源: {doc.get('data_source', '')}",
        f"因子逻辑: {doc.get('logic', '')}",
        f"覆盖范围: {doc.get('coverage', '')}",
        f"频率: {doc.get('frequency', '')}",
        f"核心公式: {doc.get('formula', '')}",
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filepath
