"""
Overmanifold Logging Infrastructure
Production-ready logging with structured output, multiple handlers, and monitoring integration.
"""

import logging
import logging.handlers
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from contextvars import ContextVar
import os


# Context variables for request tracking
REQUEST_ID: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
USER_ID: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
ENDPOINT_ID: ContextVar[Optional[str]] = ContextVar('endpoint_id', default=None)


class OvermanifoldFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def __init__(self, format_type: str = "json"):
        self.format_type = format_type
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context variables if available
        request_id = REQUEST_ID.get()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = USER_ID.get()
        if user_id:
            log_data["user_id"] = user_id
        
        endpoint_id = ENDPOINT_ID.get()
        if endpoint_id:
            log_data["endpoint_id"] = endpoint_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        if self.format_type == "json":
            return json.dumps(log_data)
        else:
            # Text format
            return f"{log_data['timestamp']} | {log_data['level']:8} | {log_data['logger']} | {log_data['message']}"


class OvermanifoldLogger:
    """
    Centralized logger for Overmanifold system.
    Provides structured logging with context tracking.
    """
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup logging handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(OvermanifoldFormatter("text"))
        self.logger.addHandler(console_handler)
        
        # File handler for errors
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/overmanifold_error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(OvermanifoldFormatter("json"))
        self.logger.addHandler(error_handler)
        
        # File handler for all logs
        all_handler = logging.handlers.RotatingFileHandler(
            'logs/overmanifold_all.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(OvermanifoldFormatter("json"))
        self.logger.addHandler(all_handler)
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None, 
             exc_info: bool = False) -> None:
        """Internal logging method with context."""
        if extra:
            record = self.logger.makeRecord(
                self.logger.name, level, '', 0, message, (), None, exc_info
            )
            record.extra_fields = extra
            self.logger.handle(record)
        else:
            self.logger.log(level, message, exc_info=exc_info)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, extra, exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, extra, exc_info)
    
    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log exception with traceback."""
        self._log(logging.ERROR, message, extra, exc_info=True)


class ErrorHandler:
    """
    Centralized error handling for Overmanifold system.
    Provides consistent error responses and logging.
    """
    
    def __init__(self, logger: OvermanifoldLogger):
        self.logger = logger
    
    def handle_validation_error(self, error: Exception, context: Optional[Dict] = None) -> Dict:
        """Handle validation errors."""
        self.logger.warning(f"Validation error: {str(error)}", extra=context or {})
        
        return {
            "error": "validation_error",
            "message": str(error),
            "status_code": 400,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def handle_authentication_error(self, error: Exception, context: Optional[Dict] = None) -> Dict:
        """Handle authentication errors."""
        self.logger.warning(f"Authentication error: {str(error)}", extra=context or {})
        
        return {
            "error": "authentication_error",
            "message": "Authentication failed",
            "status_code": 401,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def handle_authorization_error(self, error: Exception, context: Optional[Dict] = None) -> Dict:
        """Handle authorization errors."""
        self.logger.warning(f"Authorization error: {str(error)}", extra=context or {})
        
        return {
            "error": "authorization_error",
            "message": "Insufficient permissions",
            "status_code": 403,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def handle_not_found_error(self, resource: str, resource_id: str, context: Optional[Dict] = None) -> Dict:
        """Handle not found errors."""
        self.logger.info(f"Resource not found: {resource} {resource_id}", extra=context or {})
        
        return {
            "error": "not_found",
            "message": f"{resource} with ID {resource_id} not found",
            "status_code": 404,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def handle_rate_limit_error(self, retry_after: int = 60, context: Optional[Dict] = None) -> Dict:
        """Handle rate limit errors."""
        self.logger.warning(f"Rate limit exceeded", extra=context or {})
        
        return {
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded. Retry after {retry_after} seconds",
            "retry_after": retry_after,
            "status_code": 429,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def handle_internal_error(self, error: Exception, context: Optional[Dict] = None) -> Dict:
        """Handle internal server errors."""
        self.logger.error(f"Internal error: {str(error)}", extra=context or {}, exc_info=True)
        
        return {
            "error": "internal_error",
            "message": "An internal server error occurred",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def handle_database_error(self, error: Exception, context: Optional[Dict] = None) -> Dict:
        """Handle database errors."""
        self.logger.error(f"Database error: {str(error)}", extra=context or {}, exc_info=True)
        
        return {
            "error": "database_error",
            "message": "A database error occurred",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }


class RequestLogger:
    """
    Request/response logging middleware for API monitoring.
    """
    
    def __init__(self, logger: OvermanifoldLogger):
        self.logger = logger
    
    def log_request(self, method: str, path: str, headers: Dict, 
                   body: Optional[str] = None, query_params: Optional[Dict] = None) -> str:
        """Log incoming request."""
        request_id = self._generate_request_id()
        REQUEST_ID.set(request_id)
        
        log_data = {
            "type": "request",
            "method": method,
            "path": path,
            "headers": self._sanitize_headers(headers),
            "query_params": query_params
        }
        
        if body:
            log_data["body_length"] = len(body)
        
        self.logger.info(f"Request: {method} {path}", extra=log_data)
        return request_id
    
    def log_response(self, request_id: str, status_code: int, 
                    response_time_ms: float, response_length: Optional[int] = None) -> None:
        """Log outgoing response."""
        log_data = {
            "type": "response",
            "request_id": request_id,
            "status_code": status_code,
            "response_time_ms": response_time_ms
        }
        
        if response_length:
            log_data["response_length"] = response_length
        
        level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
        self._log(level, f"Response: {status_code}", log_data)
    
    def log_error(self, request_id: str, error: Exception, context: Optional[Dict] = None) -> None:
        """Log request error."""
        log_data = {
            "type": "error",
            "request_id": request_id,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        if context:
            log_data.update(context)
        
        self.logger.error(f"Request error: {str(error)}", extra=log_data, exc_info=True)
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _sanitize_headers(self, headers: Dict) -> Dict:
        """Sanitize headers to remove sensitive information."""
        sensitive_headers = {'authorization', 'cookie', 'x-api-key', 'x-auth-token'}
        return {k: v if k.lower() not in sensitive_headers else '***REDACTED***' 
                for k, v in headers.items()}
    
    def _log(self, level: int, message: str, extra: Dict) -> None:
        """Internal logging method."""
        if extra:
            record = self.logger.logger.makeRecord(
                self.logger.logger.name, level, '', 0, message, (), None, False
            )
            record.extra_fields = extra
            self.logger.logger.handle(record)
        else:
            self.logger.logger.log(level, message)


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """Setup logging infrastructure."""
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(exist_ok=True)
    
    # Set root logger level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # Configure third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def get_logger(name: str) -> OvermanifoldLogger:
    """Get a logger instance."""
    return OvermanifoldLogger(name)


def get_error_handler(logger: OvermanifoldLogger) -> ErrorHandler:
    """Get an error handler instance."""
    return ErrorHandler(logger)


def get_request_logger(logger: OvermanifoldLogger) -> RequestLogger:
    """Get a request logger instance."""
    return RequestLogger(logger)