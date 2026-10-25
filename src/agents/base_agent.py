from __future__ import annotations
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from src.llm.client import UnifiedLLMClient, LLMResponse

class AgentConfig(BaseModel):
    id: str
    role: str
    model: str
    system_prompt: str

class Agent:
    def __init__(self, config: AgentConfig, provider: Optional[str] = None):
        self.config = config
        self.provider = provider
        self.client = UnifiedLLMClient(provider=provider)

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def role(self) -> str:
        return self.config.role

    @property
    def model(self) -> str:
        return self.config.model

    def step(self, prompt: str, temperature: float = 0.4) -> LLMResponse:
        return self.client.generate(
            prompt=prompt,
            system_prompt=self.config.system_prompt,
            model=self.config.model,
            temperature=temperature
        )
