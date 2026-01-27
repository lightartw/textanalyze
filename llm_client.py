# llm_client.py
import requests
import config


class LLMClient:
    def __init__(self):
        self.api_url = f"{config.LLM_BASE_URL}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json"
        }

    def _call_llm(self, messages, temperature=0.3, timeout=60):
        payload = {
            "model": config.LLM_MODEL,
            "messages": messages,
            "temperature": temperature
        }

        try:
            resp = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            data = resp.json()

            if "choices" not in data:
                return {
                    "status": "error",
                    "analysis": f"API返回异常: {data}",
                }

            return {
                "status": "success",
                "analysis": data["choices"][0]["message"]["content"],
            }

        except Exception as e:
            return {
                "status": "error",
                "analysis": f"LLM调用失败: {e}",
            }

    def _build_news_prompt(self, title, content, max_chars):
        system_prompt = "你是一个石油与能源市场分析专家。"

        user_prompt = f"""
                新闻标题：{title}
                新闻正文：
                {content[:max_chars]}

                请判断该新闻对国际油价的影响（利好 / 利空 / 中性），并简要说明原因。
                """

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()}
        ]

    def _build_category_prompt(self, category, news_list, max_chars_per_news):
        system_prompt = "你是一个严谨、克制的能源与金融分析专家。"

        user_prompt = f"""
            以下是【{category}】类别下的多条新闻，请综合分析其对国际油价的整体影响。
            """

        for idx, news in enumerate(news_list, 1):
            user_prompt += f"""
            【新闻 {idx}】
            标题：{news['title']}
            正文摘要：
            {news['content'][:max_chars_per_news]}
            """

        user_prompt += """
            请给出：
            1. 总体判断（利好 / 利空 / 中性）
            2. 主要逻辑（不超过 5 条）
            """

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()}
        ]


    def analyze_news(self, title, content, max_chars=10000000):
        if not content:
            return {
                "status": "error",
                "analysis": "无有效正文内容",
            }

        messages = self._build_news_prompt(
            title=title,
            content=content,
            max_chars=max_chars
        )

        return self._call_llm(
            messages=messages,
            temperature=0.3,
            timeout=30
        )


    def analyze_category(self, category, news_list, max_chars_per_news=10000000):
        if not news_list:
            return {
                "status": "error",
                "analysis": "该分类下无可用新闻",
            }

        messages = self._build_category_prompt(
            category=category,
            news_list=news_list,
            max_chars_per_news=max_chars_per_news
        )

        return self._call_llm(
            messages=messages,
            temperature=0.2,
            timeout=60
        )
