from __future__ import annotations
import time
import os
from typing import Optional, Dict, Any, Generator, Callable
from dataclasses import dataclass
from openai import OpenAI, APIConnectionError, RateLimitError, APIError
import httpx

from src.config import config

@dataclass
class LLMResponse:
    text: str
    tokens: int
    generation_time: float
    cost: float
    model: str
    provider: str

class UnifiedLLMClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or config.system.default_provider
        self.client = self._init_client()

    def _init_client(self) -> OpenAI:
        base_url = config.get_base_url(self.provider)
        api_key = config.get_api_key(self.provider) or "dummy-key-for-local"
        http_client = httpx.Client(timeout=httpx.Timeout(120.0, connect=10.0))
        return OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        temperature: float = 0.4,
        json_mode: bool = False,
        stream: bool = False,
        stream_callback: Optional[Callable[[str], None]] = None,
        max_retries: int = 3
    ) -> LLMResponse:
        target_model = model or config.models.solo_model.get(self.provider, "qwen2.5:14b")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        extra_body: Dict[str, Any] = {}
        if self.provider == "ollama":
            keep_alive = getattr(config.providers.ollama, "keep_alive", "5m")
            extra_body["keep_alive"] = keep_alive
            extra_body["options"] = {"seed": config.system.seed}

        start_time = time.time()
        last_error = None

        for attempt in range(max_retries):
            try:
                if stream:
                    full_text = ""
                    response = self.client.chat.completions.create(
                        model=target_model,
                        messages=messages,
                        temperature=temperature,
                        response_format={"type": "json_object"} if json_mode else None,
                        stream=True,
                        extra_body=extra_body if extra_body else None
                    )
                    prompt_tokens_est = len(prompt.split()) + len(system_prompt.split())
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            delta = chunk.choices[0].delta.content
                            full_text += delta
                            if stream_callback:
                                stream_callback(delta)

                    generation_time = time.time() - start_time
                    completion_tokens_est = len(full_text.split()) * 2
                    total_tokens = prompt_tokens_est + completion_tokens_est
                    cost = config.calculate_cost(target_model, total_tokens)
                    return LLMResponse(
                        text=full_text,
                        tokens=total_tokens,
                        generation_time=generation_time,
                        cost=cost,
                        model=target_model,
                        provider=self.provider
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=target_model,
                        messages=messages,
                        temperature=temperature,
                        response_format={"type": "json_object"} if json_mode else None,
                        stream=False,
                        extra_body=extra_body if extra_body else None
                    )
                    generation_time = time.time() - start_time
                    content = response.choices[0].message.content or ""
                    tokens = 0
                    if response.usage:
                        tokens = response.usage.total_tokens
                    else:
                        tokens = (len(prompt) + len(content)) // 4

                    cost = config.calculate_cost(target_model, tokens)
                    return LLMResponse(
                        text=content,
                        tokens=tokens,
                        generation_time=generation_time,
                        cost=cost,
                        model=target_model,
                        provider=self.provider
                    )
            except (RateLimitError, APIConnectionError, APIError) as e:
                last_error = e
                time.sleep(2 ** attempt)

        return LLMResponse(
            text=f"ERROR: {last_error}",
            tokens=0,
            generation_time=time.time() - start_time,
            cost=0.0,
            model=target_model,
            provider=self.provider
        )
