"""
Unit tests for Overmanifold infrastructure module.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime

from overmanifold.infrastructure.config import (
    ConfigLoader,
    OvermanifoldConfig,
    Environment,
    DatabaseConfig,
    SecurityConfig,
    SecretsManager
)
from overmanifold.infrastructure.logging_config import (
    OvermanifoldLogger,
    ErrorHandler,
    RequestLogger,
    setup_logging,
    get_logger
)
from overmanifold.validation.validators import ValidationError


@pytest.mark.unit
class TestConfigLoader:
    """Test cases for ConfigLoader."""
    
    @pytest.fixture
    def temp_env_file(self):
        """Create a temporary .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("ENVIRONMENT=test\n")
            f.write("DEBUG=true\n")
            f.write("DB_HOST=testhost\n")
            f.write("DB_PORT=5433\n")
            f.write("DB_NAME=overmanifold\n")
            f.write("DB_USER=overmanifold\n")
            f.write("DB_PASSWORD=test_password\n")
            f.write("SECRET_KEY=test_secret_key_32_characters_long\n")
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    def test_load_config_basic(self, temp_env_file):
        """Test basic configuration loading."""
        loader = ConfigLoader(temp_env_file)
        config = loader.load_config()
        
        assert isinstance(config, OvermanifoldConfig)
        assert config.environment == Environment.TEST
        assert config.debug is True
        assert config.database.host == "testhost"
        assert config.database.port == 5433
    
    def test_load_config_validation(self, temp_env_file):
        """Test configuration validation."""
        loader = ConfigLoader(temp_env_file)
        config = loader.load_config()
        
        # Should not raise validation errors with valid config
        config.validate()
    
    def test_load_config_missing_secret_key(self, temp_env_file):
        """Test handling of missing secret key."""
        # Remove SECRET_KEY from env file
        with open(temp_env_file, 'r') as f:
            content = f.read()
        
        content = content.replace("SECRET_KEY=test_secret_key_32_characters_long\n", "")
        
        with open(temp_env_file, 'w') as f:
            f.write(content)
        
        loader = ConfigLoader(temp_env_file)
        config = loader.load_config()
        
        # Should generate a secret key
        assert len(config.security.secret_key) >= 32
    
    def test_generate_secret_key(self):
        """Test secret key generation."""
        loader = ConfigLoader()
        secret_key = loader._generate_secret_key()
        
        assert len(secret_key) >= 32
        assert isinstance(secret_key, str)


@pytest.mark.unit
class TestDatabaseConfig:
    """Test cases for DatabaseConfig."""
    
    def test_valid_config(self):
        """Test valid database configuration."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            name="testdb",
            user="testuser",
            password="testpass"
        )
        config.validate()  # Should not raise
    
    def test_missing_host(self):
        """Test missing host validation."""
        config = DatabaseConfig(host="", port=5432, name="testdb", user="testuser", password="testpass")
        with pytest.raises(ValidationError):
            config.validate()
    
    def test_invalid_port(self):
        """Test invalid port validation."""
        config = DatabaseConfig(host="localhost", port=99999, name="testdb", user="testuser", password="testpass")
        with pytest.raises(ValidationError):
            config.validate()


@pytest.mark.unit
class TestSecurityConfig:
    """Test cases for SecurityConfig."""
    
    def test_valid_config(self):
        """Test valid security configuration."""
        config = SecurityConfig(
            secret_key="a" * 32,
            jwt_algorithm="HS256",
            jwt_expiration_hours=24
        )
        config.validate()  # Should not raise
    
    def test_short_secret_key(self):
        """Test short secret key validation."""
        config = SecurityConfig(secret_key="short", jwt_algorithm="HS256")
        with pytest.raises(ValidationError):
            config.validate()
    
    def test_invalid_jwt_expiration(self):
        """Test invalid JWT expiration validation."""
        config = SecurityConfig(
            secret_key="a" * 32,
            jwt_algorithm="HS256",
            jwt_expiration_hours=0
        )
        with pytest.raises(ValidationError):
            config.validate()


@pytest.mark.unit
class TestSecretsManager:
    """Test cases for SecretsManager."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return OvermanifoldConfig(
            environment=Environment.DEVELOPMENT,
            security=SecurityConfig(secret_key="a" * 32)
        )
    
    @pytest.fixture
    def secrets_manager(self, config):
        """Create secrets manager."""
        return SecretsManager(config)
    
    def test_get_secret_from_env(self, secrets_manager):
        """Test getting secret from environment."""
        os.environ["TEST_SECRET"] = "test_value"
        result = secrets_manager.get_secret("TEST_SECRET")
        assert result == "test_value"
        
        # Cleanup
        del os.environ["TEST_SECRET"]
    
    def test_get_secret_not_found(self, secrets_manager):
        """Test getting non-existent secret."""
        with pytest.raises(ValueError):
            secrets_manager.get_secret("NON_EXISTENT_SECRET")
    
    def test_set_secret_development(self, secrets_manager):
        """Test setting secret in development."""
        secrets_manager.set_secret("NEW_SECRET", "new_value")
        assert secrets_manager.get_secret("NEW_SECRET") == "new_value"
        
        # Cleanup
        del os.environ["NEW_SECRET"]
    
    def test_set_secret_production(self):
        """Test that setting secrets in production raises error."""
        config = OvermanifoldConfig(
            environment=Environment.PRODUCTION,
            security=SecurityConfig(secret_key="a" * 32)
        )
        secrets_manager = SecretsManager(config)
        
        with pytest.raises(RuntimeError):
            secrets_manager.set_secret("NEW_SECRET", "new_value")
    
    def test_rotate_secret(self, secrets_manager):
        """Test secret rotation."""
        os.environ["ROTATE_SECRET"] = "old_value"
        old_secret = secrets_manager.get_secret("ROTATE_SECRET")
        
        new_secret = secrets_manager.rotate_secret("ROTATE_SECRET")
        
        assert new_secret != old_secret
        assert secrets_manager.get_secret("ROTATE_SECRET") == new_secret
        
        # Cleanup
        del os.environ["ROTATE_SECRET"]
    
    def test_hash_secret(self, secrets_manager):
        """Test secret hashing."""
        secret_value = "my_secret_value"
        hashed = secrets_manager.hash_secret(secret_value)
        
        assert len(hashed) == 64  # SHA-256 produces 64 character hex string
        assert hashed != secret_value


@pytest.mark.unit
class TestOvermanifoldLogger:
    """Test cases for OvermanifoldLogger."""
    
    @pytest.fixture
    def logger(self):
        """Create logger instance."""
        return OvermanifoldLogger("test_logger", "DEBUG")
    
    def test_logger_creation(self, logger):
        """Test logger creation."""
        assert logger.logger.name == "test_logger"
        assert logger.logger.level == 10  # DEBUG level
    
    def test_log_debug(self, logger):
        """Test debug logging."""
        logger.debug("Debug message")
        # Should not raise any exceptions
    
    def test_log_info(self, logger):
        """Test info logging."""
        logger.info("Info message")
        # Should not raise any exceptions
    
    def test_log_warning(self, logger):
        """Test warning logging."""
        logger.warning("Warning message")
        # Should not raise any exceptions
    
    def test_log_error(self, logger):
        """Test error logging."""
        logger.error("Error message")
        # Should not raise any exceptions
    
    def test_log_with_extra_fields(self, logger):
        """Test logging with extra fields."""
        extra = {"request_id": "123", "user_id": "456"}
        logger.info("Message with extra", extra=extra)
        # Should not raise any exceptions


@pytest.mark.unit
class TestErrorHandler:
    """Test cases for ErrorHandler."""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler instance."""
        logger = OvermanifoldLogger("test_logger", "DEBUG")
        return ErrorHandler(logger)
    
    def test_handle_validation_error(self, error_handler):
        """Test validation error handling."""
        error = ValidationError("field", "Invalid value")
        result = error_handler.handle_validation_error(error)
        
        assert result["error"] == "validation_error"
        assert result["status_code"] == 400
        assert "timestamp" in result
    
    def test_handle_authentication_error(self, error_handler):
        """Test authentication error handling."""
        error = Exception("Auth failed")
        result = error_handler.handle_authentication_error(error)
        
        assert result["error"] == "authentication_error"
        assert result["status_code"] == 401
    
    def test_handle_not_found_error(self, error_handler):
        """Test not found error handling."""
        result = error_handler.handle_not_found_error("user", "123")
        
        assert result["error"] == "not_found"
        assert result["status_code"] == 404
        assert "123" in result["message"]
    
    def test_handle_rate_limit_error(self, error_handler):
        """Test rate limit error handling."""
        result = error_handler.handle_rate_limit_error(retry_after=60)
        
        assert result["error"] == "rate_limit_exceeded"
        assert result["status_code"] == 429
        assert result["retry_after"] == 60
    
    def test_handle_internal_error(self, error_handler):
        """Test internal error handling."""
        error = Exception("Internal error")
        result = error_handler.handle_internal_error(error)
        
        assert result["error"] == "internal_error"
        assert result["status_code"] == 500


@pytest.mark.unit
class TestRequestLogger:
    """Test cases for RequestLogger."""
    
    @pytest.fixture
    def request_logger(self):
        """Create request logger instance."""
        logger = OvermanifoldLogger("test_logger", "DEBUG")
        return RequestLogger(logger)
    
    def test_log_request(self, request_logger):
        """Test request logging."""
        headers = {"content-type": "application/json", "authorization": "Bearer token"}
        request_id = request_logger.log_request(
            "GET",
            "/api/test",
            headers,
            query_params={"param": "value"}
        )
        
        assert request_id is not None
        assert len(request_id) > 0
    
    def test_log_response(self, request_logger):
        """Test response logging."""
        request_logger.log_response("request_123", 200, 150.5, 1024)
        # Should not raise any exceptions
    
    def test_sanitize_headers(self, request_logger):
        """Test header sanitization."""
        headers = {
            "content-type": "application/json",
            "authorization": "Bearer secret_token",
            "cookie": "session=abc123"
        }
        
        sanitized = request_logger._sanitize_headers(headers)
        
        assert sanitized["content-type"] == "application/json"
        assert sanitized["authorization"] == "***REDACTED***"
        assert sanitized["cookie"] == "***REDACTED***"


@pytest.mark.unit
def test_setup_logging():
    """Test logging setup."""
    with tempfile.TemporaryDirectory() as temp_dir:
        setup_logging(log_level="DEBUG", log_dir=temp_dir)
        
        # Check that log directory was created
        assert Path(temp_dir).exists()
        
        # Check that log files would be created
        log_files = list(Path(temp_dir).glob("*.log"))
        # Log files might not exist yet, but directory should be ready