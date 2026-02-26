from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/ai_brokerage"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "BE_"}


settings = Settings()
