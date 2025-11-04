from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from typing import List


class Settings(BaseSettings):
    app_name: str = "PromptStack Auth Service"
    environment: str = "dev"  # dev|prod

    database_url: str = "postgresql://promptstack:promptstack@db:5432/promptstack"

    api_cors_origins: List[AnyHttpUrl] | List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8001",
    ]

    # JWT config
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # OIDC/JWT config (optional for prod)
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None

    # Dev header auth allows overriding identity
    allow_dev_headers: bool = True

    class Config:
        env_prefix = "AUTH_"
        env_file = ".env"

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def split_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()  # type: ignore[call-arg]

