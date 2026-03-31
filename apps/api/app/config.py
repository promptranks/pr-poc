from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Deployment
    deployment_mode: Literal["self_hosted", "saas"] = "self_hosted"
    deployment_domain: str = ""  # e.g. "prk.mycompany.com" or "promptranks.org"

    # Database
    database_url: str = "postgresql+asyncpg://promptranks:promptranks-dev@localhost:5432/promptranks"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    oauth_redirect_url: str = "http://localhost:3000/auth/callback"

    # Content Registry (self-hosted only)
    promptranks_license_key: str = ""
    content_registry_url: str = "https://content.promptranks.org"
    content_sync_interval: int = 86400  # seconds, default: daily

    # CORS (deployment domain auto-added via effective_cors_origins)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                import json
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def effective_cors_origins(self) -> list[str]:
        """CORS origins including deployment domain if set."""
        origins = list(self.cors_origins)
        if self.deployment_domain:
            domain_origin = f"https://{self.deployment_domain}"
            if domain_origin not in origins:
                origins.append(domain_origin)
        return origins

    # LLM (provider set via model prefix: openai/gpt-4o, anthropic/claude-sonnet-4-6, etc.)
    llm_executor_model: str = "openai/gpt-4o"
    llm_judge_model: str = "openai/gpt-4o"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1

    # Assessment timers (seconds)
    quick_assessment_time_limit: int = 900
    full_kba_time_limit: int = 900
    full_ppa_time_limit: int = 1800

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
