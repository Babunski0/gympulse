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

    # Default geofence radius for new gyms; each gym's admin can change it.
    default_gym_radius_m: int = 50

    # Address search for the admin gym form (OpenStreetMap Nominatim by default).
    # Nominatim's usage policy asks for an identifying User-Agent and at most 1 request/second.
    geocoder_url: str = "https://nominatim.openstreetmap.org/search"
    geocoder_user_agent: str = "GymPulse/0.1 (gym check-in app)"
    geocoder_timeout_s: float = 5.0

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
