"""
Overmanifold Input Validation and Sanitization
Comprehensive validation for all system inputs to prevent injection attacks and ensure data integrity.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
import re
import hashlib
import json
from dataclasses import dataclass


class ValidationError(Exception):
    """Custom validation error with detailed context."""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error for '{field}': {message}")


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Security vulnerability, must reject
    HIGH = "high"  # Major issue, should reject
    MEDIUM = "medium"  # Warning, may accept with sanitization
    LOW = "low"  # Minor issue, can accept
    
    # Define severity order for comparison
    def __lt__(self, other):
        severity_order = {ValidationSeverity.LOW: 0, ValidationSeverity.MEDIUM: 1, ValidationSeverity.HIGH: 2, ValidationSeverity.CRITICAL: 3}
        return severity_order[self] < severity_order[other]
    
    def __gt__(self, other):
        severity_order = {ValidationSeverity.LOW: 0, ValidationSeverity.MEDIUM: 1, ValidationSeverity.HIGH: 2, ValidationSeverity.CRITICAL: 3}
        return severity_order[self] > severity_order[other]


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None
    severity: ValidationSeverity = ValidationSeverity.LOW
    
    def add_error(self, message: str, severity: ValidationSeverity = ValidationSeverity.HIGH) -> None:
        """Add an error to the validation result."""
        self.errors.append(message)
        self.is_valid = False
        if severity > self.severity:
            self.severity = severity
    
    def add_warning(self, message: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(message)


class InputValidator:
    """
    Comprehensive input validator for Overmanifold system.
    Validates and sanitizes all user inputs and external data.
    """
    
    # Security patterns
    SQL_INJECTION_PATTERN = re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER)\b)', re.IGNORECASE)
    XSS_PATTERN = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE)
    COMMAND_INJECTION_PATTERN = re.compile(r'[;&|`$()]', re.MULTILINE)
    PATH_TRAVERSAL_PATTERN = re.compile(r'\.\.[\\/]')
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    HEX_PATTERN = re.compile(r'^0x[a-fA-F0-9]+$')
    HASH_PATTERN = re.compile(r'^[a-fA-F0-9]{64}$')  # SHA-256
    DID_PATTERN = re.compile(r'^did:[a-z0-9]+:[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$')
    ENDPOINT_ID_PATTERN = re.compile(r'^[a-fA-F0-9]{32}$')
    
    def __init__(self):
        self.max_string_length = 10000
        self.max_array_length = 1000
        self.max_nested_depth = 10
    
    def validate_string(self, value: Any, field_name: str = "field",
                      min_length: int = 0, max_length: Optional[int] = None,
                      pattern: Optional[re.Pattern] = None,
                      allow_empty: bool = False) -> ValidationResult:
        """Validate string input."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Type check
        if not isinstance(value, str):
            try:
                value = str(value)
                result.add_warning(f"Converted {field_name} to string")
            except Exception:
                result.add_error(f"{field_name} must be a string", ValidationSeverity.CRITICAL)
                return result
        
        # Empty check
        if not value.strip():
            if not allow_empty:
                result.add_error(f"{field_name} cannot be empty", ValidationSeverity.HIGH)
            return result
        
        # Length check
        actual_max = max_length or self.max_string_length
        if len(value) > actual_max:
            result.add_error(f"{field_name} exceeds maximum length of {actual_max}", ValidationSeverity.HIGH)
            result.sanitized_value = value[:actual_max]
        
        if len(value) < min_length:
            result.add_error(f"{field_name} must be at least {min_length} characters", ValidationSeverity.MEDIUM)
        
        # Pattern check
        if pattern and not pattern.match(value):
            result.add_error(f"{field_name} does not match required pattern", ValidationSeverity.HIGH)
        
        # Security checks
        self._check_security_issues(value, field_name, result)
        
        if result.is_valid:
            result.sanitized_value = value.strip()
        
        return result
    
    def validate_integer(self, value: Any, field_name: str = "field",
                        min_value: Optional[int] = None, max_value: Optional[int] = None) -> ValidationResult:
        """Validate integer input."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            result.add_error(f"{field_name} must be a valid integer", ValidationSeverity.CRITICAL)
            return result
        
        if min_value is not None and int_value < min_value:
            result.add_error(f"{field_name} must be at least {min_value}", ValidationSeverity.MEDIUM)
        
        if max_value is not None and int_value > max_value:
            result.add_error(f"{field_name} must be at most {max_value}", ValidationSeverity.MEDIUM)
        
        if result.is_valid:
            result.sanitized_value = int_value
        
        return result
    
    def validate_float(self, value: Any, field_name: str = "field",
                      min_value: Optional[float] = None, max_value: Optional[float] = None) -> ValidationResult:
        """Validate float input."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            result.add_error(f"{field_name} must be a valid number", ValidationSeverity.CRITICAL)
            return result
        
        if min_value is not None and float_value < min_value:
            result.add_error(f"{field_name} must be at least {min_value}", ValidationSeverity.MEDIUM)
        
        if max_value is not None and float_value > max_value:
            result.add_error(f"{field_name} must be at most {max_value}", ValidationSeverity.MEDIUM)
        
        if result.is_valid:
            result.sanitized_value = float_value
        
        return result
    
    def validate_boolean(self, value: Any, field_name: str = "field") -> ValidationResult:
        """Validate boolean input."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if isinstance(value, bool):
            result.sanitized_value = value
            return result
        
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                result.sanitized_value = True
                return result
            elif value.lower() in ('false', '0', 'no', 'off'):
                result.sanitized_value = False
                return result
        
        if isinstance(value, (int, float)):
            result.sanitized_value = bool(value)
            return result
        
        result.add_error(f"{field_name} must be a boolean value", ValidationSeverity.HIGH)
        return result
    
    def validate_dict(self, value: Any, field_name: str = "field",
                     required_keys: Optional[List[str]] = None,
                     optional_keys: Optional[List[str]] = None,
                     max_size: Optional[int] = None) -> ValidationResult:
        """Validate dictionary input."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not isinstance(value, dict):
            result.add_error(f"{field_name} must be a dictionary", ValidationSeverity.CRITICAL)
            return result
        
        # Size check
        actual_max = max_size or 100
        if len(value) > actual_max:
            result.add_error(f"{field_name} exceeds maximum size of {actual_max}", ValidationSeverity.HIGH)
        
        # Required keys check
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                result.add_error(f"{field_name} missing required keys: {missing_keys}", ValidationSeverity.HIGH)
        
        # Check for unexpected keys
        allowed_keys = set((required_keys or []) + (optional_keys or []))
        if allowed_keys:
            unexpected_keys = [key for key in value.keys() if key not in allowed_keys]
            if unexpected_keys:
                result.add_warning(f"{field_name} contains unexpected keys: {unexpected_keys}")
        
        # Recursively validate dictionary values
        sanitized_dict = {}
        for key, val in value.items():
            val_result = self.validate_any(val, f"{field_name}.{key}")
            if not val_result.is_valid:
                result.add_error(f"Invalid value for {field_name}.{key}: {val_result.errors}")
            else:
                sanitized_dict[key] = val_result.sanitized_value
        
        if result.is_valid:
            result.sanitized_value = sanitized_dict
        
        return result
    
    def validate_list(self, value: Any, field_name: str = "field",
                     min_length: int = 0, max_length: Optional[int] = None,
                     item_type: Optional[type] = None) -> ValidationResult:
        """Validate list input."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not isinstance(value, (list, tuple)):
            result.add_error(f"{field_name} must be a list or tuple", ValidationSeverity.CRITICAL)
            return result
        
        # Length check
        actual_max = max_length or self.max_array_length
        if len(value) > actual_max:
            result.add_error(f"{field_name} exceeds maximum length of {actual_max}", ValidationSeverity.HIGH)
            value = value[:actual_max]
        
        if len(value) < min_length:
            result.add_error(f"{field_name} must have at least {min_length} items", ValidationSeverity.MEDIUM)
        
        # Type check for items
        if item_type:
            for i, item in enumerate(value):
                if not isinstance(item, item_type):
                    result.add_error(f"{field_name}[{i}] must be of type {item_type.__name__}", ValidationSeverity.MEDIUM)
        
        if result.is_valid:
            result.sanitized_value = list(value)
        
        return result
    
    def validate_hash(self, value: Any, field_name: str = "field",
                     algorithm: str = "sha256") -> ValidationResult:
        """Validate cryptographic hash."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        string_result = self.validate_string(value, field_name, min_length=64, max_length=64)
        if not string_result.is_valid:
            result.add_error(f"{field_name} must be a valid {algorithm} hash", ValidationSeverity.HIGH)
            return result
        
        if not self.HASH_PATTERN.match(str(value)):
            result.add_error(f"{field_name} must be a valid {algorithm} hash", ValidationSeverity.HIGH)
            return result
        
        result.sanitized_value = str(value).lower()
        return result
    
    def validate_did(self, value: Any, field_name: str = "field") -> ValidationResult:
        """Validate Decentralized Identifier."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        string_result = self.validate_string(value, field_name, min_length=10)
        if not string_result.is_valid:
            return string_result
        
        if not self.DID_PATTERN.match(str(value)):
            result.add_error(f"{field_name} must be a valid DID", ValidationSeverity.HIGH)
            return result
        
        result.sanitized_value = str(value)
        return result
    
    def validate_endpoint_id(self, value: Any, field_name: str = "field") -> ValidationResult:
        """Validate endpoint ID."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        string_result = self.validate_string(value, field_name, min_length=32, max_length=32)
        if not string_result.is_valid:
            return result
        
        if not self.ENDPOINT_ID_PATTERN.match(str(value)):
            result.add_error(f"{field_name} must be a valid endpoint ID", ValidationSeverity.HIGH)
            return result
        
        result.sanitized_value = str(value).lower()
        return result
    
    def validate_url(self, value: Any, field_name: str = "field",
                    allowed_schemes: Optional[List[str]] = None) -> ValidationResult:
        """Validate URL."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        string_result = self.validate_string(value, field_name, min_length=5)
        if not string_result.is_valid:
            return result
        
        url_str = str(value).strip()
        
        # Basic URL validation
        if not re.match(r'^https?://', url_str):
            result.add_error(f"{field_name} must use HTTP or HTTPS scheme", ValidationSeverity.HIGH)
            return result
        
        # Scheme validation
        if allowed_schemes:
            scheme = url_str.split('://')[0]
            if scheme not in allowed_schemes:
                result.add_error(f"{field_name} must use one of these schemes: {allowed_schemes}", ValidationSeverity.HIGH)
        
        result.sanitized_value = url_str
        return result
    
    def validate_timestamp(self, value: Any, field_name: str = "field") -> ValidationResult:
        """Validate timestamp."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if isinstance(value, datetime):
            result.sanitized_value = value
            return result
        
        if isinstance(value, (int, float)):
            # Assume Unix timestamp
            try:
                result.sanitized_value = datetime.fromtimestamp(value)
                return result
            except (ValueError, OSError):
                result.add_error(f"{field_name} must be a valid timestamp", ValidationSeverity.HIGH)
                return result
        
        if isinstance(value, str):
            # Try ISO format
            try:
                result.sanitized_value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return result
            except ValueError:
                result.add_error(f"{field_name} must be a valid ISO 8601 timestamp", ValidationSeverity.HIGH)
                return result
        
        result.add_error(f"{field_name} must be a valid timestamp", ValidationSeverity.HIGH)
        return result
    
    def validate_any(self, value: Any, field_name: str = "field") -> ValidationResult:
        """Validate any input type by attempting to determine the best validator."""
        if value is None:
            return ValidationResult(is_valid=True, errors=[], warnings=[], sanitized_value=None)
        
        if isinstance(value, bool):
            return self.validate_boolean(value, field_name)
        elif isinstance(value, int):
            return self.validate_integer(value, field_name)
        elif isinstance(value, float):
            return self.validate_float(value, field_name)
        elif isinstance(value, str):
            # Try to determine if it's a specific type
            if self.HASH_PATTERN.match(value):
                return self.validate_hash(value, field_name)
            elif self.DID_PATTERN.match(value):
                return self.validate_did(value, field_name)
            elif self.ENDPOINT_ID_PATTERN.match(value):
                return self.validate_endpoint_id(value, field_name)
            elif value.startswith(('http://', 'https://')):
                return self.validate_url(value, field_name)
            else:
                return self.validate_string(value, field_name)
        elif isinstance(value, (list, tuple)):
            return self.validate_list(value, field_name)
        elif isinstance(value, dict):
            return self.validate_dict(value, field_name)
        else:
            # Unknown type, convert to string
            return self.validate_string(value, field_name)
    
    def _check_security_issues(self, value: str, field_name: str, result: ValidationResult) -> None:
        """Check for common security issues in string input."""
        # SQL injection
        if self.SQL_INJECTION_PATTERN.search(value):
            result.add_error(f"{field_name} contains potential SQL injection pattern", ValidationSeverity.CRITICAL)
        
        # XSS
        if self.XSS_PATTERN.search(value):
            result.add_error(f"{field_name} contains potential XSS pattern", ValidationSeverity.CRITICAL)
        
        # Command injection
        if self.COMMAND_INJECTION_PATTERN.search(value):
            result.add_error(f"{field_name} contains potential command injection pattern", ValidationSeverity.CRITICAL)
        
        # Path traversal
        if self.PATH_TRAVERSAL_PATTERN.search(value):
            result.add_error(f"{field_name} contains potential path traversal pattern", ValidationSeverity.HIGH)


class Sanitizer:
    """
    Input sanitizer for cleaning potentially dangerous input.
    Used when validation fails but the input can be salvaged.
    """
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Normalize Unicode
        value = value.encode('utf-8', 'ignore').decode('utf-8')
        
        # Strip dangerous characters (conservative approach)
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Sanitize HTML input (basic implementation)."""
        # Remove script tags and common dangerous patterns
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE)
        value = re.sub(r'<iframe[^>]*>.*?</iframe>', '', value, flags=re.IGNORECASE)
        value = re.sub(r'<object[^>]*>.*?</object>', '', value, flags=re.IGNORECASE)
        value = re.sub(r'on\w+="[^"]*"', '', value, flags=re.IGNORECASE)
        return value
    
    @staticmethod
    def sanitize_filename(value: str) -> str:
        """Sanitize filename."""
        # Remove dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00', '.']
        for char in dangerous_chars:
            value = value.replace(char, '_')
        
        # Remove leading spaces
        value = value.lstrip(' ')
        
        # Limit length
        if len(value) > 255:
            value = value[:255]
        
        return value or 'unnamed'
    
    @staticmethod
    def sanitize_json(value: str) -> Dict:
        """Safely parse and sanitize JSON."""
        try:
            data = json.loads(value)
            # Recursively sanitize strings in the JSON
            return Sanitizer._sanitize_dict(data)
        except json.JSONDecodeError:
            raise ValidationError("json", "Invalid JSON format", value)
    
    @staticmethod
    def _sanitize_dict(data: Any, depth: int = 0) -> Any:
        """Recursively sanitize dictionary values."""
        if depth > 10:  # Prevent infinite recursion
            return data
        
        if isinstance(data, dict):
            return {key: Sanitizer._sanitize_dict(value, depth + 1) for key, value in data.items()}
        elif isinstance(data, list):
            return [Sanitizer._sanitize_dict(item, depth + 1) for item in data]
        elif isinstance(data, str):
            return Sanitizer.sanitize_string(data)
        else:
            return data


# Global validator instance
validator = InputValidator()
sanitizer = Sanitizer()