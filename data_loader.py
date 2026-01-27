# data_loader.py
import pandas as pd
import os
from dataclasses import dataclass

@dataclass
class NewsItem:
    """ 定义标准的数据输入对象 """
    id: str
    title: str
    date: str
    category: str
    url: str

class DataLoader:
    @staticmethod
    def load_data(filepath):
        """ 
        读取CSV并转换为对象列表 
        """
        if not os.path.exists(filepath):
            print(f"[Error] 输入文件不存在: {filepath}")
            return []

        try:
            # 1. 强制不读表头 (header=None)，且全部作为字符串读取 (dtype=str)
            df = pd.read_csv(filepath, header=None, dtype=str).fillna("")
            
            # 2. 基础验证：列数检查
            if df.shape[1] < 5:
                print(f"[Error] 数据格式错误：列数不足5列。当前列数: {df.shape[1]}")
                return []

            # 3. 识别表头
            # 策略：检查第5列（索引4，即URL列）。
            # 如果第一行的URL列不是以 'http' 开头，且包含 'url'/'链接' 字样，或者前几列包含 '标题'/'编号'，则认为是表头。
            first_row = df.iloc[0].tolist()
            first_row_str = [str(x).lower() for x in first_row]
            
            has_header = False
            
            # 判定依据 A: 第5列显然不是一个链接
            url_col_val = str(first_row[4]).strip()
            if not url_col_val.startswith("http"):
                # 判定依据 B: 包含常见表头关键字
                keywords = ["id", "编号", "title", "标题", "url", "链接", "date", "日期"]
                if any(k in " ".join(first_row_str) for k in keywords):
                    has_header = True

            if has_header:
                print(f"[System] 检测到表头: {first_row}，已自动跳过")
                df = df[1:] # 切片，扔掉第一行
            else:
                print("[System] 未检测到表头，将第一行视为数据")

            items = []
            for index, row in df.iterrows():
                # 4. 数据行级验证
                url_str = str(row[4]).strip()
                if not url_str.startswith("http"):
                    print(f"[Warning] 跳过无效行 (第{index}行): URL格式不正确 -> {url_str[:20]}...")
                    continue

                item = NewsItem(
                    id=str(row[0]).strip(),       # 编号
                    title=str(row[1]).strip(),    # 标题
                    date=str(row[2]).strip(),     # 日期
                    category=str(row[3]).strip(), # 分类
                    url=url_str                   # URL
                )
                items.append(item)
            
            print(f"[System] 成功加载 {len(items)} 条有效数据")
            return items

        except Exception as e:
            print(f"[Error] 数据加载严重失败: {e}")
            return []

    @staticmethod
    def save_data(filepath, results):
        """ 保存结果，自动创建父目录 """
        try:
            # 自动创建 output 目录
            output_dir = os.path.dirname(filepath)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"[System] 创建输出目录: {output_dir}")

            df = pd.DataFrame(results)
            
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"[System] 结果已保存至 {filepath}")
            
        except Exception as e:
            print(f"[Error] 结果保存失败: {e}")