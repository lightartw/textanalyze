# main.py
import concurrent.futures
import time
from collections import defaultdict

from data_loader import DataLoader
from crawler import SimpleCrawler
from llm_client import LLMClient
import config


def crawl_single_item(item):
    crawler = SimpleCrawler()
    print(f"--> 抓取: {item.id} | {item.title}")

    content = crawler.fetch_text(item.url)

    return {
        "id": item.id,
        "title": item.title,
        "date": item.date,
        "category": item.category,
        "url": item.url,
        "content": content
    }


def main():
    # ====== 1. 加载 ======
    items = DataLoader.load_data(config.INPUT_FILE)
    if not items:
        return

    # ====== 2. 爬取 ======
    crawl_results = []
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=config.MAX_WORKERS
    ) as executor:
        futures = [executor.submit(crawl_single_item, item) for item in items]

        for future in concurrent.futures.as_completed(futures):
            try:
                crawl_results.append(future.result())
            except Exception as e:
                print(f"[Main] 抓取任务异常: {e}")

    print(f"[System] 抓取完成，用时 {time.time() - start_time:.2f}s")

    # ====== 3. 按 category 聚合 ======
    category_map = defaultdict(list)

    for item in crawl_results:
        if item["content"]:
            category_map[item["category"]].append(item)

    # ====== 4. 按 category 调用 LLM ======
    llm = LLMClient()
    final_results = []

    for category, news_list in category_map.items():
        # 控制每类新闻数量
        selected_news = news_list[:config.MAX_NEWS_PER_CATEGORY]

        print(f"\n[LLM] 分析分类: {category} | 新闻数: {len(selected_news)}")

        result = llm.analyze_category(
            category=category,
            news_list=selected_news
        )

        final_results.append({
            "分类": category,
            "新闻数量": len(selected_news),
            "涉及新闻ID": [n["id"] for n in selected_news],
            "涉及新闻标题": [n["title"] for n in selected_news],
            "分类LLM分析结果": result["analysis"],
        })

    # ====== 5. 保存结果 ======
    DataLoader.save_data(config.OUTPUT_FILE, final_results)

    print(f"\n全部完成！总耗时: {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()
