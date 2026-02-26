from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    be_database_url: str = "postgresql+asyncpg://localhost:5432/ai_brokerage"

    # Simulation
    price_tick_interval_seconds: float = 1.5
    snapshot_interval_minutes: int = 15

    # Default user
    default_user_name: str = "Trader"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
