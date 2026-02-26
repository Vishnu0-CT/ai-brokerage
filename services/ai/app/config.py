from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://clear-llm-proxy.internal.cleartax.co"
    anthropic_model: str = "claude-sonnet-4-5"
    be_service_url: str = "http://localhost:8000"
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = {"env_prefix": "AI_"}


settings = Settings()
