# llm_client.py
"""
LLM客户端
用于统一封装对话接口调用
"""
from typing import Dict, Any, List, Optional
import requests
import config


class LLMClient:
    """LLM调用客户端，仅保留文本因子分析所需接口。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """初始化连接配置。"""
        self.api_key = api_key or config.LLM_API_KEY
        self.base_url = base_url or config.LLM_BASE_URL
        self.model = model or config.LLM_MODEL
        self.api_url = f"{self.base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def call(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """调用LLM，返回统一结构。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else config.LLM_TEMPERATURE,
        }
        try:
            resp = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=timeout or config.LLM_TIMEOUT,
            )
            data = resp.json()
            if "choices" not in data:
                return {"status": "error", "error": f"API返回异常: {data}", "content": ""}
            return {
                "status": "success",
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
            }
        except requests.Timeout:
            return {"status": "error", "error": "请求超时", "content": ""}
        except Exception as e:
            return {"status": "error", "error": f"LLM调用失败: {e}", "content": ""}

    def call_with_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """简化接口：传入prompt生成对话消息。"""
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.call(messages=messages, temperature=temperature, timeout=timeout)
