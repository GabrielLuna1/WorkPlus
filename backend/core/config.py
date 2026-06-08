import sys
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017/workplus"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000"]

    lm_studio_url: str = "http://127.0.0.1:1234"
    lm_studio_model: str = "qwen-3.6-27b"

    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"

    ai_provider_primary: str = "ollama"
    ai_provider_fallback: str = "ollama"
    ai_retry_max: int = 3
    ai_retry_base_delay: float = 2.0
    ai_circuit_breaker_threshold: int = 5
    ai_circuit_breaker_reset: int = 60

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    email_imap_host: str = ""
    email_imap_port: int = 993
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_user: str = ""
    email_pass: str = ""
    email_from: str = ""
    email_check_interval_minutes: int = 15

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def _warn_default_secret(self) -> None:
        if (
            self.secret_key == "change-me"
            or self.secret_key == "change-me-to-a-random-secret"
        ):
            from core.logger import logger

            logger.warning(
                "SECRET_KEY is still default. Set a random value in .env for security."
            )


settings = Settings()
settings._warn_default_secret()
