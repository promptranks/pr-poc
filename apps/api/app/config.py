from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://promptranks:promptranks-dev@localhost:5432/promptranks"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # LLM
    anthropic_api_key: str = ""
    llm_base_url: str | None = None  # Proxy URL (e.g., https://terminal.pub)
    llm_executor_model: str = "claude-sonnet-4-6"
    llm_judge_model: str = "claude-opus-4-6"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1

    # Assessment timers (seconds)
    quick_assessment_time_limit: int = 900
    full_kba_time_limit: int = 900
    full_ppa_time_limit: int = 1800

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
