"""MEMBRA CompanyOS — Production-grade configuration."""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    APP_NAME: str = "MEMBRA CompanyOS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database (accepts sqlite:///... for local dev, postgresql://... for production)
    DATABASE_URL: str = Field(default="sqlite:///./membra_companyos.db")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis (optional — reserved for future workers)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    # CORS — comma-separated origins, or * for open (dev only)
    CORS_ORIGINS: str = "*"

    # Security
    SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Ethereum / Wallet Auth
    ETHEREUM_RPC_URL: Optional[str] = None
    CHAIN_ID: int = 1

    # LLM
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "groq"
    DEFAULT_LLM_MODEL: str = "llama-3.3-70b-versatile"

    # Settlement
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    SOLANA_RPC_URL: Optional[str] = None
    SOLANA_PRIVATE_KEY: Optional[str] = None

    # IPFS / Proof
    IPFS_GATEWAY: str = "https://gateway.pinata.cloud"
    PINATA_API_KEY: Optional[str] = None
    PINATA_SECRET_KEY: Optional[str] = None

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090

    # CompanyOS
    DEFAULT_COMPANY_NAME: str = "MEMBRA Autonomous Unit"
    DEFAULT_CURRENCY: str = "USD"
    PROOFBOOK_HASH_ALGORITHM: str = "sha3_256"
    GOVERNANCE_ADMIN_WALLET: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    def cors_origin_list(self) -> list[str]:
        raw = (self.CORS_ORIGINS or "*").strip()
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
