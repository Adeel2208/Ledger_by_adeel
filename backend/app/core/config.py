"""Central application configuration.

All runtime config comes from the environment (see `.env.example`) so nothing —
LLM provider, thesis, database — is hardcoded (Requirements FR-1, principle #5).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (OpenAI by default). Model IDs are config-driven — swap freely.
    #   reasoning/memo work -> llm_model (frontier);  extraction/screening -> llm_model_fast (cheap).
    llm_provider: str = "openai"             # openai | anthropic
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_model: str = "gpt-5.6-terra"         # balanced frontier default; use gpt-5.6-sol for hardest reasoning
    llm_model_fast: str = "gpt-5.6-luna"     # cheap/high-volume: extraction, first-pass screening
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-large"  # highest-quality OpenAI embeddings
    embedding_dimensions: int = 1536         # 3-large supports shortening; 1536 balances cost/quality

    # Database
    database_url: str = "sqlite:///./vcbrain.db"

    # Vector store
    vector_backend: str = "chroma"           # chroma | pgvector
    chroma_dir: str = "./.chroma"

    # Ingestion / outbound
    github_token: str | None = None
    tavily_api_key: str | None = None
    outbound_scan_interval_min: int = 60

    # App
    app_env: str = "dev"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so config is parsed once per process."""
    return Settings()
