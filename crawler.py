# crawler.py
import requests
from bs4 import BeautifulSoup
import config

class SimpleCrawler:
    def fetch_text(self, url):
        """ 
        输入 URL -> 输出 纯文本 
        """
        try:
            # 1. 发起请求
            resp = requests.get(url, headers=config.HEADERS, timeout=config.REQUEST_TIMEOUT)
            if resp.status_code != 200:
                print(f"[Crawler] 请求失败 {resp.status_code}: {url}")
                return ""

            # 2. 解析 HTML
            soup = BeautifulSoup(resp.content, "html.parser")

            # 3. 清洗数据 (核心逻辑)
            for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript"]):
                tag.decompose()

            # 提取正文：简单的策略是提取所有 <p> 标签
            paragraphs = soup.find_all("p")
            text_list = [p.get_text(strip=True) for p in paragraphs]
            
            # 过滤掉太短的段落
            clean_text = "\n".join([t for t in text_list if len(t) > 20])
            
            return clean_text

        except Exception as e:
            print(f"[Crawler] 抓取异常 {url}: {e}")
            return ""