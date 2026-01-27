## 项目结构

```text
main.py                        # 程序入口，串联整个流程
config.py                      # 配置项：文件路径、并发、LLM 等
crawler.py                     # 简单爬虫，从新闻 URL 抓取正文文本
data_loader.py                 # 读取输入 CSV、保存分析结果
llm_client.py                  # 封装 LLM 调用逻辑
data/                          # 输入数据目录
  input.csv                    # 原始新闻列表（id,title,date,category,url）
output/                        # 输出结果目录
  analysis_result.csv          # 按分类汇总的 LLM 分析结果
README.md                      # 项目说明（当前文件）
```

## 整体流程说明

程序从 `data/input.csv` 中读取一批新闻（包含编号、标题、日期、分类和 URL），然后并发地对每条新闻的 URL 进行网页抓取，只保留正文文本。抓取完成后，脚本会按 `category` 对新闻分组，把每一类下的多篇新闻摘要打包成提示词，调用 LLM 进行整体分析，判断该类别新闻对国际油价的大致影响及主要逻辑。

最后，程序将每个分类的新闻数量、涉及的 ID/标题以及对应的 LLM 分析结果写入 `output/analysis_result.csv`，便于后续在 Excel 或其他工具中查看和进一步处理。

## 接口设计
- 输入
  - 一个包含文本数据的 CSV/Excel 文件
  - 字段: id,title,data,category,url
- 输出
  - 一个 CSV 文件
  - 字段：分类,新闻数量,涉及新闻ID,涉及新闻标题,分类LLM分析结果