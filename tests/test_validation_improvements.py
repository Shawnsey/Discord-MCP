"""
Test suite for validation layer improvements.

This module tests the enhanced validation functionality including
the new validator classes, constants, and improved ValidationResult.
"""

import pytest
from src.discord_mcp.services.validation import (
    ValidationResult,
    ValidationErrorType,
    ValidationConstants,
    StringValidator,
    NumericValidator,
    DiscordValidator,
    ValidationMixin,
    OperationContext
)


class TestValidationResult:
    """Test ValidationResult enhancements."""
    
    def test_boolean_conversion_success(self):
        """Test ValidationResult can be used in boolean contexts for success."""
        result = ValidationResult.success({"test": "data"})
        assert bool(result) is True
        assert result.is_valid is True
        assert result.is_error is False
    
    def test_boolean_conversion_error(self):
        """Test ValidationResult can be used in boolean contexts for errors."""
        result = ValidationResult.error("Test error", ValidationErrorType.INVALID_INPUT)
        assert bool(result) is False
        assert result.is_valid is False
        assert result.is_error is True
    
    def test_success_factory_method(self):
        """Test success factory method creates correct result."""
        data = {"key": "value"}
        result = ValidationResult.success(data)
        
        assert result.is_valid is True
        assert result.data == data
        assert result.error_message is None
        assert result.error_type is None
    
    def test_error_factory_method(self):
        """Test error factory method creates correct result."""
        message = "Test error message"
        error_type = ValidationErrorType.CONTENT_TOO_LONG
        data = {"field": "content"}
        
        result = ValidationResult.error(message, error_type, data)
        
        assert result.is_valid is False
        assert result.error_message == message
        assert result.error_type == error_type
        assert result.data == data


class TestValidationConstants:
    """Test validation constants are properly defined."""
    
    def test_message_constants(self):
        """Test message-related constants."""
        assert ValidationConstants.MESSAGE_MAX_LENGTH == 2000
        assert ValidationConstants.MESSAGE_MIN_LENGTH == 1
    
    def test_discord_id_constants(self):
        """Test Discord ID-related constants."""
        assert ValidationConstants.DISCORD_ID_MIN_LENGTH == 15
        assert ValidationConstants.DISCORD_ID_MAX_LENGTH == 20
    
    def test_timeout_constants(self):
        """Test timeout-related constants."""
        assert ValidationConstants.TIMEOUT_MIN_MINUTES == 1
        assert ValidationConstants.TIMEOUT_MAX_MINUTES == 40320  # 28 days
    
    def test_message_limit_constants(self):
        """Test message limit constants."""
        assert ValidationConstants.MESSAGE_LIMIT_MIN == 1
        assert ValidationConstants.MESSAGE_LIMIT_MAX == 100
    
    def test_ban_delete_constants(self):
        """Test ban message deletion constants."""
        assert ValidationConstants.BAN_DELETE_DAYS_MIN == 0
        assert ValidationConstants.BAN_DELETE_DAYS_MAX == 7


class TestStringValidator:
    """Test StringValidator functionality."""
    
    def test_valid_content(self):
        """Test validation of valid string content."""
        result = StringValidator.validate_content("Hello, World!")
        
        assert result.is_valid is True
        assert result.data == {"content": "Hello, World!"}
        assert result.error_message is None
    
    def test_content_with_whitespace_trimming(self):
        """Test content is properly trimmed."""
        result = StringValidator.validate_content("  Hello, World!  ")
        
        assert result.is_valid is True
        assert result.data == {"content": "Hello, World!"}
    
    def test_none_content(self):
        """Test validation fails for None content."""
        result = StringValidator.validate_content(None, "test_field")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "test_field cannot be None" in result.error_message
    
    def test_empty_content_not_allowed(self):
        """Test validation fails for empty content when not allowed."""
        result = StringValidator.validate_content("", "test_field", allow_empty=False)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_EMPTY
        assert "test_field cannot be empty" in result.error_message
    
    def test_empty_content_allowed(self):
        """Test validation passes for empty content when allowed."""
        result = StringValidator.validate_content("", "test_field", allow_empty=True)
        
        assert result.is_valid is True
        assert result.data == {"content": ""}
    
    def test_content_too_short(self):
        """Test validation fails for content below minimum length."""
        result = StringValidator.validate_content("Hi", "test_field", min_length=5)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "must be at least 5 characters long" in result.error_message
    
    def test_content_too_long(self):
        """Test validation fails for content above maximum length."""
        long_content = "x" * 2001
        result = StringValidator.validate_content(long_content, "test_field", max_length=2000)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_TOO_LONG
        assert "is too long (2001 characters)" in result.error_message


class TestNumericValidator:
    """Test NumericValidator functionality."""
    
    def test_valid_integer(self):
        """Test validation of valid integer."""
        result = NumericValidator.validate_range(42, "test_field")
        
        assert result.is_valid is True
        assert result.data == {"value": 42}
    
    def test_valid_float(self):
        """Test validation of valid float."""
        result = NumericValidator.validate_range(3.14, "test_field")
        
        assert result.is_valid is True
        assert result.data == {"value": 3.14}
    
    def test_none_value(self):
        """Test validation fails for None value."""
        result = NumericValidator.validate_range(None, "test_field")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "test_field cannot be None" in result.error_message
    
    def test_non_numeric_value(self):
        """Test validation fails for non-numeric value."""
        result = NumericValidator.validate_range("not_a_number", "test_field")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "test_field must be a number" in result.error_message
    
    def test_value_below_minimum(self):
        """Test validation fails for value below minimum."""
        result = NumericValidator.validate_range(5, "test_field", min_value=10)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_RANGE
        assert "must be at least 10" in result.error_message
    
    def test_value_above_maximum(self):
        """Test validation fails for value above maximum."""
        result = NumericValidator.validate_range(15, "test_field", max_value=10)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_RANGE
        assert "must be at most 10" in result.error_message
    
    def test_value_within_range(self):
        """Test validation passes for value within range."""
        result = NumericValidator.validate_range(7, "test_field", min_value=5, max_value=10)
        
        assert result.is_valid is True
        assert result.data == {"value": 7}


class TestDiscordValidator:
    """Test DiscordValidator functionality."""
    
    def test_valid_discord_id(self):
        """Test validation of valid Discord ID."""
        valid_id = "123456789012345678"  # 18 digits
        result = DiscordValidator.validate_id(valid_id, "guild")
        
        assert result.is_valid is True
        assert result.data == {"id": valid_id}
    
    def test_empty_discord_id(self):
        """Test validation fails for empty Discord ID."""
        result = DiscordValidator.validate_id("", "guild")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "guild ID cannot be empty" in result.error_message
    
    def test_non_string_discord_id(self):
        """Test validation fails for non-string Discord ID."""
        result = DiscordValidator.validate_id(123456789012345678, "guild")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "guild ID must be a string" in result.error_message
    
    def test_non_numeric_discord_id(self):
        """Test validation fails for non-numeric Discord ID."""
        result = DiscordValidator.validate_id("not_numeric_id", "guild")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "Discord IDs must be numeric" in result.error_message
    
    def test_discord_id_too_short(self):
        """Test validation fails for Discord ID that's too short."""
        short_id = "12345"  # 5 digits
        result = DiscordValidator.validate_id(short_id, "guild")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "Discord IDs should be 15-20 digits" in result.error_message
    
    def test_discord_id_too_long(self):
        """Test validation fails for Discord ID that's too long."""
        long_id = "123456789012345678901"  # 21 digits
        result = DiscordValidator.validate_id(long_id, "guild")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "Discord IDs should be 15-20 digits" in result.error_message


class TestValidationMixin:
    """Test ValidationMixin functionality."""
    
    def setup_method(self):
        """Set up test instance."""
        self.mixin = ValidationMixin()
    
    def test_validate_message_content_valid(self):
        """Test message content validation with valid content."""
        result = self.mixin._validate_message_content("Hello, World!")
        
        assert result.is_valid is True
        assert result.data == {"content": "Hello, World!"}
    
    def test_validate_message_content_too_long(self):
        """Test message content validation with content too long."""
        long_message = "x" * 2001
        result = self.mixin._validate_message_content(long_message)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_TOO_LONG
    
    def test_validate_timeout_duration_valid(self):
        """Test timeout duration validation with valid duration."""
        result = self.mixin._validate_timeout_duration(30)
        
        assert result.is_valid is True
        assert result.data == {"value": 30}
    
    def test_validate_timeout_duration_too_long(self):
        """Test timeout duration validation with duration too long."""
        result = self.mixin._validate_timeout_duration(50000)  # More than 28 days
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_RANGE
    
    def test_validate_message_limit_valid(self):
        """Test message limit validation with valid limit."""
        result = self.mixin._validate_message_limit(50)
        
        assert result.is_valid is True
        assert result.data == {"value": 50}
    
    def test_validate_message_limit_too_high(self):
        """Test message limit validation with limit too high."""
        result = self.mixin._validate_message_limit(150)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_RANGE
    
    def test_validate_ban_delete_days_valid(self):
        """Test ban delete days validation with valid days."""
        result = self.mixin._validate_ban_delete_days(3)
        
        assert result.is_valid is True
        assert result.data == {"value": 3}
    
    def test_validate_ban_delete_days_too_high(self):
        """Test ban delete days validation with days too high."""
        result = self.mixin._validate_ban_delete_days(10)
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_RANGE
    
    def test_create_validation_error_response(self):
        """Test creation of validation error response."""
        validation_result = ValidationResult.error(
            "Test error", 
            ValidationErrorType.INVALID_INPUT
        )
        context = OperationContext("test_operation")
        
        result = self.mixin._create_validation_error_response(validation_result, context)
        
        assert result.is_valid is False
        assert "❌ Error in test_operation: Test error" in result.error_message
    
    def test_create_permission_denied_response(self):
        """Test creation of permission denied response."""
        result = self.mixin._create_permission_denied_response("guild", "123456", "Additional info")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.PERMISSION_DENIED
        assert "Access to guild `123456` is not permitted" in result.error_message
        assert "Additional info" in result.error_message
        assert result.data == {"resource_type": "guild", "resource_id": "123456"}
    
    def test_create_not_found_response(self):
        """Test creation of not found response."""
        result = self.mixin._create_not_found_response("user", "789012", "Additional info")
        
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.NOT_FOUND
        assert "User `789012` was not found" in result.error_message
        assert "Additional info" in result.error_message
        assert result.data == {"resource_type": "user", "resource_id": "789012"}


if __name__ == "__main__":
    pytest.main([__file__])