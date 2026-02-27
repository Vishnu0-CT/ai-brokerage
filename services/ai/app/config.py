from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    use_direct_anthropic: bool = False
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://clear-llm-proxy.internal.cleartax.co"
    anthropic_direct_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    # BE service
    be_service_url: str = "http://localhost:8000"
    be_service_timeout: float = 10.0

    # Voice
    whisper_model: str = "mlx-community/whisper-medium-mlx"

    # Chat
    max_conversation_history: int = 50

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = {"env_prefix": "AI_", "env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
