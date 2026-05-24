"""
Unit tests for Overmanifold validation module.
"""

import pytest
from overmanifold.validation.validators import (
    InputValidator,
    Sanitizer,
    ValidationError,
    ValidationSeverity,
    ValidationResult
)


@pytest.mark.unit
@pytest.mark.validation
class TestInputValidator:
    """Test cases for InputValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return InputValidator()
    
    def test_validate_string_valid(self, validator):
        """Test valid string validation."""
        result = validator.validate_string("hello world", "test_field")
        assert result.is_valid
        assert result.sanitized_value == "hello world"
        assert len(result.errors) == 0
    
    def test_validate_string_empty(self, validator):
        """Test empty string validation."""
        result = validator.validate_string("", "test_field", allow_empty=False)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_string_too_long(self, validator):
        """Test string that exceeds maximum length."""
        long_string = "a" * 20000
        result = validator.validate_string(long_string, "test_field", max_length=100)
        assert not result.is_valid
        assert len(result.sanitized_value) == 100
    
    def test_validate_string_sql_injection(self, validator):
        """Test SQL injection detection."""
        malicious_string = "test'; DROP TABLE users; --"
        result = validator.validate_string(malicious_string, "test_field")
        assert not result.is_valid
        assert any("SQL injection" in error for error in result.errors)
    
    def test_validate_string_xss(self, validator):
        """Test XSS detection."""
        malicious_string = "<script>alert('xss')</script>"
        result = validator.validate_string(malicious_string, "test_field")
        assert not result.is_valid
        assert any("XSS" in error for error in result.errors)
    
    def test_validate_integer_valid(self, validator):
        """Test valid integer validation."""
        result = validator.validate_integer(42, "test_field")
        assert result.is_valid
        assert result.sanitized_value == 42
    
    def test_validate_integer_invalid(self, validator):
        """Test invalid integer validation."""
        result = validator.validate_integer("not_a_number", "test_field")
        assert not result.is_valid
    
    def test_validate_integer_range(self, validator):
        """Test integer range validation."""
        result = validator.validate_integer(150, "test_field", min_value=0, max_value=100)
        assert not result.is_valid
    
    def test_validate_float_valid(self, validator):
        """Test valid float validation."""
        result = validator.validate_float(3.14, "test_field")
        assert result.is_valid
        assert result.sanitized_value == 3.14
    
    def test_validate_boolean_true(self, validator):
        """Test boolean validation for true values."""
        assert validator.validate_boolean(True, "test_field").sanitized_value is True
        assert validator.validate_boolean("true", "test_field").sanitized_value is True
        assert validator.validate_boolean("1", "test_field").sanitized_value is True
        assert validator.validate_boolean(1, "test_field").sanitized_value is True
    
    def test_validate_boolean_false(self, validator):
        """Test boolean validation for false values."""
        assert validator.validate_boolean(False, "test_field").sanitized_value is False
        assert validator.validate_boolean("false", "test_field").sanitized_value is False
        assert validator.validate_boolean("0", "test_field").sanitized_value is False
        assert validator.validate_boolean(0, "test_field").sanitized_value is False
    
    def test_validate_dict_valid(self, validator):
        """Test valid dictionary validation."""
        test_dict = {"key1": "value1", "key2": 42}
        result = validator.validate_dict(test_dict, "test_field")
        assert result.is_valid
    
    def test_validate_dict_missing_required_keys(self, validator):
        """Test dictionary missing required keys."""
        test_dict = {"key1": "value1"}
        result = validator.validate_dict(
            test_dict, "test_field", 
            required_keys=["key1", "key2", "key3"]
        )
        assert not result.is_valid
    
    def test_validate_list_valid(self, validator):
        """Test valid list validation."""
        test_list = [1, 2, 3, 4, 5]
        result = validator.validate_list(test_list, "test_field")
        assert result.is_valid
        assert result.sanitized_value == test_list
    
    def test_validate_list_too_long(self, validator):
        """Test list that exceeds maximum length."""
        test_list = list(range(2000))
        result = validator.validate_list(test_list, "test_field", max_length=100)
        assert not result.is_valid
    
    def test_validate_hash_valid(self, validator):
        """Test valid hash validation."""
        valid_hash = "a" * 64  # SHA-256 hash
        result = validator.validate_hash(valid_hash, "test_field")
        assert result.is_valid
    
    def test_validate_hash_invalid(self, validator):
        """Test invalid hash validation."""
        invalid_hash = "not_a_hash"
        result = validator.validate_hash(invalid_hash, "test_field")
        assert not result.is_valid
    
    def test_validate_did_valid(self, validator):
        """Test valid DID validation."""
        valid_did = "did:om:123:abc"
        result = validator.validate_did(valid_did, "test_field")
        assert result.is_valid
    
    def test_validate_did_invalid(self, validator):
        """Test invalid DID validation."""
        invalid_did = "not_a_did"
        result = validator.validate_did(invalid_did, "test_field")
        assert not result.is_valid
    
    def test_validate_url_valid(self, validator):
        """Test valid URL validation."""
        valid_url = "https://example.com/path"
        result = validator.validate_url(valid_url, "test_field")
        assert result.is_valid
    
    def test_validate_url_invalid_scheme(self, validator):
        """Test URL with invalid scheme."""
        invalid_url = "ftp://example.com"
        result = validator.validate_url(invalid_url, "test_field")
        assert not result.is_valid
    
    def test_validate_timestamp_valid(self, validator):
        """Test valid timestamp validation."""
        from datetime import datetime
        valid_timestamp = datetime.utcnow()
        result = validator.validate_timestamp(valid_timestamp, "test_field")
        assert result.is_valid
    
    def test_validate_timestamp_invalid(self, validator):
        """Test invalid timestamp validation."""
        invalid_timestamp = "not_a_timestamp"
        result = validator.validate_timestamp(invalid_timestamp, "test_field")
        assert not result.is_valid


@pytest.mark.unit
@pytest.mark.validation
class TestSanitizer:
    """Test cases for Sanitizer."""
    
    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer instance."""
        return Sanitizer()
    
    def test_sanitize_string_basic(self, sanitizer):
        """Test basic string sanitization."""
        input_string = "  hello world  "
        result = sanitizer.sanitize_string(input_string)
        assert result == "hello world"
    
    def test_sanitize_string_dangerous_chars(self, sanitizer):
        """Test removal of dangerous characters."""
        input_string = "test<script>alert('xss')</script>string"
        result = sanitizer.sanitize_string(input_string)
        assert "<script>" not in result
        assert "</script>" not in result
        assert "(" not in result
        assert ")" not in result
    
    def test_sanitize_html(self, sanitizer):
        """Test HTML sanitization."""
        input_html = "<p>safe</p><script>alert('xss')</script>"
        result = sanitizer.sanitize_html(input_html)
        assert "<script>" not in result
        assert "<p>" in result  # Safe HTML should remain
    
    def test_sanitize_filename(self, sanitizer):
        """Test filename sanitization."""
        input_filename = "../../../etc/passwd"
        result = sanitizer.sanitize_filename(input_filename)
        assert "../" not in result
        assert result == "_________etc_passwd"
    
    def test_sanitize_json_valid(self, sanitizer):
        """Test JSON sanitization."""
        input_json = '{"key": "value", "number": 42}'
        result = sanitizer.sanitize_json(input_json)
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_sanitize_json_invalid(self, sanitizer):
        """Test invalid JSON handling."""
        invalid_json = "not json"
        with pytest.raises(ValidationError):
            sanitizer.sanitize_json(invalid_json)


@pytest.mark.unit
@pytest.mark.validation
class TestValidationResult:
    """Test cases for ValidationResult."""
    
    def test_validation_result_initially_valid(self):
        """Test that ValidationResult is initially valid."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_add_error_makes_invalid(self):
        """Test that adding errors makes result invalid."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.add_error("Test error")
        assert not result.is_valid
        assert len(result.errors) == 1
    
    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.add_warning("Test warning")
        assert result.is_valid  # Warnings don't make it invalid
        assert len(result.warnings) == 1
    
    def test_severity_upgrade(self):
        """Test that severity upgrades correctly."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.add_error("Low severity error", ValidationSeverity.LOW)
        assert result.severity == ValidationSeverity.LOW
        
        result.add_error("Critical error", ValidationSeverity.CRITICAL)
        assert result.severity == ValidationSeverity.CRITICAL