"""
Overmanifold Configuration Management
Production-ready configuration with environment variables, secrets management, and validation.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import secrets
import hashlib

from overmanifold.validation.validators import validator, ValidationError


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    name: str = "overmanifold"
    user: str = "overmanifold"
    password: str = ""
    ssl_mode: str = "require"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    
    def validate(self) -> None:
        """Validate database configuration."""
        if not self.host:
            raise ValidationError("database.host", "Database host is required")
        if not self.name:
            raise ValidationError("database.name", "Database name is required")
        if not self.user:
            raise ValidationError("database.user", "Database user is required")
        if not self.password:
            raise ValidationError("database.password", "Database password is required")
        if self.port < 1 or self.port > 65535:
            raise ValidationError("database.port", "Invalid port number")


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    max_connections: int = 50
    
    def validate(self) -> None:
        """Validate Redis configuration."""
        if not self.host:
            raise ValidationError("redis.host", "Redis host is required")
        if self.port < 1 or self.port > 65535:
            raise ValidationError("redis.port", "Invalid port number")


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    password_min_length: int = 12
    session_timeout_minutes: int = 30
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    allowed_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    
    def validate(self) -> None:
        """Validate security configuration."""
        if not self.secret_key:
            raise ValidationError("security.secret_key", "Secret key is required")
        if len(self.secret_key) < 32:
            raise ValidationError("security.secret_key", "Secret key must be at least 32 characters")
        if self.jwt_expiration_hours < 1:
            raise ValidationError("security.jwt_expiration_hours", "JWT expiration must be at least 1 hour")


@dataclass
class APIConfig:
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 4
    max_request_size_mb: int = 10
    timeout_seconds: int = 30
    cors_enabled: bool = True
    
    def validate(self) -> None:
        """Validate API configuration."""
        if self.port < 1 or self.port > 65535:
            raise ValidationError("api.port", "Invalid port number")
        if self.workers < 1:
            raise ValidationError("api.workers", "Workers must be at least 1")


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    prometheus_port: int = 9090
    log_level: str = "INFO"
    metrics_enabled: bool = True
    tracing_enabled: bool = False
    health_check_interval_seconds: int = 30
    
    def validate(self) -> None:
        """Validate monitoring configuration."""
        if self.prometheus_port < 1 or self.prometheus_port > 65535:
            raise ValidationError("monitoring.prometheus_port", "Invalid port number")


@dataclass
class OvermanifoldConfig:
    """Main Overmanifold configuration."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: str = "INFO"
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    api: APIConfig = field(default_factory=APIConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "transaction_workers": True,
        "repo_tokenization": True,
        "browser_validators": True,
        "sms_transport": True,
        "phone_did": True,
        "governance": True
    })
    
    def validate(self) -> None:
        """Validate all configuration."""
        self.database.validate()
        self.redis.validate()
        self.security.validate()
        self.api.validate()
        self.monitoring.validate()
    
    def to_dict(self, sanitize: bool = True) -> Dict:
        """Convert configuration to dictionary."""
        config_dict = {
            "environment": self.environment.value,
            "debug": self.debug,
            "log_level": self.log_level,
            "features": self.features
        }
        
        if not sanitize:
            config_dict.update({
                "database": self.database.__dict__,
                "redis": self.redis.__dict__,
                "security": {k: v for k, v in self.security.__dict__.items() if k != "secret_key"},
                "api": self.api.__dict__,
                "monitoring": self.monitoring.__dict__
            })
        
        return config_dict


class ConfigLoader:
    """
    Configuration loader with support for environment variables and .env files.
    """
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self._load_env_file()
    
    def _load_env_file(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path(self.env_file)
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    def load_config(self) -> OvermanifoldConfig:
        """Load complete configuration."""
        config = OvermanifoldConfig()
        
        # Load environment
        config.environment = Environment(os.getenv("ENVIRONMENT", "development"))
        config.debug = os.getenv("DEBUG", "false").lower() == "true"
        config.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Load database configuration
        config.database = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "overmanifold"),
            user=os.getenv("DB_USER", "overmanifold"),
            password=os.getenv("DB_PASSWORD", ""),
            ssl_mode=os.getenv("DB_SSL_MODE", "require"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30"))
        )
        
        # Load Redis configuration
        config.redis = RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        )
        
        # Load security configuration
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            secret_key = self._generate_secret_key()
        
        config.security = SecurityConfig(
            secret_key=secret_key,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "12")),
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "30")),
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
        )
        
        # Load API configuration
        config.api = APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            debug=config.debug,
            workers=int(os.getenv("API_WORKERS", "4")),
            max_request_size_mb=int(os.getenv("MAX_REQUEST_SIZE_MB", "10")),
            timeout_seconds=int(os.getenv("API_TIMEOUT_SECONDS", "30")),
            cors_enabled=os.getenv("CORS_ENABLED", "true").lower() == "true"
        )
        
        # Load monitoring configuration
        config.monitoring = MonitoringConfig(
            enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
            log_level=config.log_level,
            metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            tracing_enabled=os.getenv("TRACING_ENABLED", "false").lower() == "true",
            health_check_interval_seconds=int(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "30"))
        )
        
        # Load feature flags
        features_json = os.getenv("FEATURE_FLAGS")
        if features_json:
            try:
                config.features.update(json.loads(features_json))
            except json.JSONDecodeError:
                pass
        
        # Validate configuration
        config.validate()
        
        return config
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        return secrets.token_urlsafe(32)
    
    def save_secret(self, secret_name: str, secret_value: str) -> None:
        """
        Save a secret to environment (in production, use proper secret manager).
        This is a simplified implementation for development.
        """
        os.environ[secret_name] = secret_value
        
        # Also append to .env file for development
        env_path = Path(self.env_file)
        with open(env_path, 'a') as f:
            f.write(f"\n{secret_name}={secret_value}\n")


class SecretsManager:
    """
    Secrets manager for production environments.
    In production, this would integrate with AWS Secrets Manager, HashiCorp Vault, etc.
    """
    
    def __init__(self, config: OvermanifoldConfig):
        self.config = config
        self._secrets_cache: Dict[str, str] = {}
    
    def get_secret(self, secret_name: str) -> str:
        """Get a secret by name."""
        # Check cache first
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        # In production, this would fetch from proper secret manager
        # For now, use environment variables
        secret_value = os.getenv(secret_name)
        if not secret_value:
            raise ValueError(f"Secret {secret_name} not found")
        
        self._secrets_cache[secret_name] = secret_value
        return secret_value
    
    def set_secret(self, secret_name: str, secret_value: str) -> None:
        """Set a secret (in development only)."""
        if self.config.environment == Environment.PRODUCTION:
            raise RuntimeError("Cannot set secrets directly in production")
        
        self._secrets_cache[secret_name] = secret_value
        os.environ[secret_name] = secret_value
    
    def rotate_secret(self, secret_name: str) -> str:
        """Rotate a secret and return the new value."""
        new_secret = secrets.token_urlsafe(32)
        self.set_secret(secret_name, new_secret)
        return new_secret
    
    def hash_secret(self, secret_value: str) -> str:
        """Hash a secret for storage."""
        return hashlib.sha256(secret_value.encode()).hexdigest()


# Global configuration instance
_config: Optional[OvermanifoldConfig] = None
_config_loader: Optional[ConfigLoader] = None


def get_config(env_file: str = ".env") -> OvermanifoldConfig:
    """Get global configuration instance."""
    global _config, _config_loader
    
    if _config is None:
        _config_loader = ConfigLoader(env_file)
        _config = _config_loader.load_config()
    
    return _config


def reload_config() -> OvermanifoldConfig:
    """Reload configuration from environment."""
    global _config
    
    if _config_loader:
        _config = _config_loader.load_config()
    
    return _config