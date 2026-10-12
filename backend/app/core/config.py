from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-secret-change-me-in-env-file"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GYMPULSE_", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/gympulse"
    jwt_secret: str = _DEV_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    # Fixed-window rate limit for auth and check-in endpoints
    rate_limit_per_minute: int = 20

    cors_origins: list[str] = ["*"]

    @model_validator(mode="after")
    def _require_real_secret_outside_dev(self) -> "Settings":
        if self.environment != "development" and self.jwt_secret == _DEV_SECRET:
            raise ValueError("GYMPULSE_JWT_SECRET must be set outside development.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
