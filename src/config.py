from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
RESULTS_DIR = BASE_DIR / "results"

class SystemSettings(BaseModel):
    seed: int = 2026
    default_provider: str = "ollama"
    checkpoint_file: str = "results/checkpoint.jsonl"
    excel_output: str = "results/badanie_groupchat_wyniki.xlsx"
    local_db_file: str = "local_database.txt"

class ExecutionSettings(BaseModel):
    max_group_turns: int = 15
    max_solo_turns: int = 5
    code_timeout_seconds: int = 15
    web_search_max_results: int = 3

class ProviderDetails(BaseModel):
    base_url: str
    api_key_env: Optional[str] = None
    keep_alive: Optional[str] = "5m"

class ProvidersConfig(BaseModel):
    ollama: ProviderDetails = Field(default_factory=lambda: ProviderDetails(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        keep_alive=os.getenv("OLLAMA_KEEP_ALIVE", "5m")
    ))
    groq: ProviderDetails = Field(default_factory=lambda: ProviderDetails(
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY"
    ))
    openai: ProviderDetails = Field(default_factory=lambda: ProviderDetails(
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY"
    ))
    openrouter: ProviderDetails = Field(default_factory=lambda: ProviderDetails(
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY"
    ))

class ModelsConfig(BaseModel):
    solo_model: Dict[str, str] = Field(default_factory=lambda: {
        "ollama": "qwen2.5:14b",
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4o-mini",
        "openrouter": "meta-llama/llama-3.3-70b-instruct"
    })
    jury_models: Dict[str, List[str]] = Field(default_factory=lambda: {
        "ollama": ["phi4:latest", "qwen2.5:14b", "mistral-nemo:12b"],
        "groq": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
        "openai": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        "openrouter": ["meta-llama/llama-3.3-70b-instruct", "mistralai/mixtral-8x7b-instruct", "google/gemma-2-9b-it"]
    })

class AppConfig(BaseModel):
    system: SystemSettings = Field(default_factory=SystemSettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    pricing_per_1m_tokens: Dict[str, float] = Field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "AppConfig":
        path = config_path or (CONFIG_DIR / "benchmark_config.yaml")
        data: Dict[str, Any] = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        env_provider = os.getenv("DEFAULT_PROVIDER")
        if env_provider and "system" in data:
            data["system"]["default_provider"] = env_provider
        elif env_provider:
            data.setdefault("system", {})["default_provider"] = env_provider

        return cls(**data)

    def get_api_key(self, provider: str) -> Optional[str]:
        prov = getattr(self.providers, provider, None)
        if prov and prov.api_key_env:
            return os.getenv(prov.api_key_env, "")
        return None

    def get_base_url(self, provider: str) -> str:
        prov = getattr(self.providers, provider, None)
        if prov:
            return prov.base_url
        return "http://localhost:11434/v1"

    def calculate_cost(self, model: str, total_tokens: int) -> float:
        rate = self.pricing_per_1m_tokens.get(model, self.pricing_per_1m_tokens.get("default", 1.0))
        return (total_tokens / 1_000_000.0) * rate

config = AppConfig.load()
