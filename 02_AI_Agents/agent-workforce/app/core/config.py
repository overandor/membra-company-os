import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AgentWorkforce"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "change-me"
    cors_origins: str = "*"

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    sendgrid_api_key: Optional[str] = None
    email_from: str = "noreply@agentworkforce.dev"

    github_token: Optional[str] = None
    github_org: Optional[str] = None

    vercel_token: Optional[str] = None
    vercel_team_id: Optional[str] = None

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentworkforce"
    sentry_dsn: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
