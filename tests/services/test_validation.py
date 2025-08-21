"""
Unit tests for the validation layer.

This module tests all validation methods and data structures
to ensure consistent behavior across the Discord service.
"""

import pytest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from discord_mcp.services.validation import (
    ValidationResult,
    ValidationErrorType,
    OperationContext,
    ValidationMixin
)


def test_validation_result_success():
    """Test creating successful validation results."""
    # Test without data
    result = ValidationResult.success()
    assert result.is_valid is True
    assert result.data is None
    assert result.error_message is None
    assert result.error_type is None
    
    # Test with data
    data = {"key": "value"}
    result = ValidationResult.success(data)
    assert result.is_valid is True
    assert result.data == data
    assert result.error_message is None
    assert result.error_type is None


def test_validation_result_error():
    """Test creating error validation results."""
    message = "Test error"
    error_type = ValidationErrorType.INVALID_INPUT
    
    # Test without data
    result = ValidationResult.error(message, error_type)
    assert result.is_valid is False
    assert result.error_message == message
    assert result.error_type == error_type
    assert result.data is None
    
    # Test with data
    data = {"context": "test"}
    result = ValidationResult.error(message, error_type, data)
    assert result.is_valid is False
    assert result.error_message == message
    assert result.error_type == error_type
    assert result.data == data


def test_operation_context():
    """Test creating operation context."""
    # Basic creation
    context = OperationContext("test_operation")
    assert context.operation_name == "test_operation"
    assert context.guild_id is None
    assert context.channel_id is None
    assert context.user_id is None
    assert context.additional_params == {}
    
    # Full creation
    additional_params = {"key": "value"}
    context = OperationContext(
        operation_name="test_operation",
        guild_id="123456789",
        channel_id="987654321",
        user_id="555666777",
        additional_params=additional_params
    )
    assert context.operation_name == "test_operation"
    assert context.guild_id == "123456789"
    assert context.channel_id == "987654321"
    assert context.user_id == "555666777"
    assert context.additional_params == additional_params


def test_validation_mixin():
    """Test ValidationMixin methods."""
    validator = ValidationMixin()
    
    # Test string content validation
    result = validator._validate_string_content("Hello World")
    assert result.is_valid is True
    assert result.data == {"content": "Hello World"}
    
    # Test empty content
    result = validator._validate_string_content("")
    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.CONTENT_EMPTY
    
    # Test content too long
    long_content = "x" * 2001
    result = validator._validate_string_content(long_content)
    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.CONTENT_TOO_LONG
    
    # Test numeric range validation
    result = validator._validate_numeric_range(5, "test_field", 1, 10)
    assert result.is_valid is True
    assert result.data == {"value": 5}
    
    # Test numeric range below minimum
    result = validator._validate_numeric_range(0, "test_field", min_value=1)
    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.INVALID_RANGE
    
    # Test Discord ID validation
    valid_id = "123456789012345678"
    result = validator._validate_discord_id(valid_id, "guild")
    assert result.is_valid is True
    assert result.data == {"id": valid_id}
    
    # Test invalid Discord ID
    result = validator._validate_discord_id("abc123", "guild")
    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.INVALID_INPUT
    
    # Test message content validation
    result = validator._validate_message_content("Hello, Discord!")
    assert result.is_valid is True
    assert result.data == {"content": "Hello, Discord!"}
    
    # Test message content validation for editing
    result = validator._validate_message_content_for_editing("Updated message")
    assert result.is_valid is True
    assert result.data == {"content": "Updated message"}
    
    # Test message content validation for DM
    result = validator._validate_message_content_for_dm("Direct message")
    assert result.is_valid is True
    assert result.data == {"content": "Direct message"}
    
    # Test timeout duration validation
    result = validator._validate_timeout_duration(60)
    assert result.is_valid is True
    assert result.data == {"value": 60}
    
    # Test message limit validation
    result = validator._validate_message_limit(50)
    assert result.is_valid is True
    assert result.data == {"value": 50}
    
    # Test ban delete days validation
    result = validator._validate_ban_delete_days(3)
    assert result.is_valid is True
    assert result.data == {"value": 3}
    
    # Test error response creation
    validation_result = ValidationResult.error(
        "Test error message", 
        ValidationErrorType.INVALID_INPUT
    )
    response = validator._create_validation_error_response(validation_result)
    assert response.error_message == "❌ Error: Test error message"
    assert response.error_type == ValidationErrorType.INVALID_INPUT
    
    # Test permission denied response
    response = validator._create_permission_denied_response("guild", "123456789")
    expected = "❌ Error: Access to guild `123456789` is not permitted."
    assert response.error_message == expected
    assert response.error_type == ValidationErrorType.PERMISSION_DENIED
    
    # Test not found response
    response = validator._create_not_found_response("user", "555666777")
    expected = "❌ Error: User `555666777` was not found or bot has no access."
    assert response.error_message == expected
    assert response.error_type == ValidationErrorType.NOT_FOUND


def test_message_content_validation_utilities():
    """Test new message content validation utilities."""
    validator = ValidationMixin()
    
    # Test _validate_message_content_for_editing
    result = validator._validate_message_content_for_editing("Valid edit content")
    assert result.is_valid is True
    assert result.data == {"content": "Valid edit content"}
    
    # Test empty content for editing
    result = validator._validate_message_content_for_editing("")
    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.CONTENT_EMPTY
    assert "New message content" in result.error_message
    
    # Test _validate_message_content_for_dm
    result = validator._validate_message_content_for_dm("Valid DM content")
    assert result.is_valid is True
    assert result.data == {"content": "Valid DM content"}
    
    # Test empty content for DM
    result = validator._validate_message_content_for_dm("   ")
    assert result.is_valid is False
    assert result.error_type == ValidationErrorType.CONTENT_EMPTY
    
    # Test _create_message_validation_error_response
    validation_result = ValidationResult.error(
        "Message content cannot be empty",
        ValidationErrorType.CONTENT_EMPTY
    )
    error_response = validator._create_message_validation_error_response(
        validation_result, "message"
    )
    assert "❌ Error: Message content cannot be empty" in error_response
    assert "Please provide a non-empty message content" in error_response
    
    # Test error response for editing
    error_response = validator._create_message_validation_error_response(
        validation_result, "edit"
    )
    assert "New message content cannot be empty" in error_response
    
    # Test error response for DM
    error_response = validator._create_message_validation_error_response(
        validation_result, "dm"
    )
    assert "Direct message content cannot be empty" in error_response
    
    # Test _create_message_content_empty_response
    empty_response = validator._create_message_content_empty_response("message")
    assert empty_response == "❌ Error: Message content cannot be empty."
    
    empty_response = validator._create_message_content_empty_response("edit")
    assert empty_response == "❌ Error: New message content cannot be empty."
    
    empty_response = validator._create_message_content_empty_response("dm")
    assert empty_response == "❌ Error: Direct message content cannot be empty."
    
    # Test _create_message_content_too_long_response
    too_long_response = validator._create_message_content_too_long_response(2500, "message")
    expected = "❌ Error: Message content too long (2500 characters). Discord limit is 2000 characters."
    assert too_long_response == expected
    
    # Test _validate_and_format_message_content_error
    # Valid content should return None
    error = validator._validate_and_format_message_content_error("Valid content", "message")
    assert error is None
    
    # Empty content should return error
    error = validator._validate_and_format_message_content_error("", "message")
    assert error is not None
    assert "❌ Error: Message content cannot be empty" in error
    
    # Too long content should return error
    long_content = "x" * 2001
    error = validator._validate_and_format_message_content_error(long_content, "message")
    assert error is not None
    assert "too long" in error
    assert "2000 characters" in error
    
    # Test different operation types
    error = validator._validate_and_format_message_content_error("", "edit")
    assert error is not None
    assert "New message content cannot be empty" in error
    
    error = validator._validate_and_format_message_content_error("", "dm")
    assert error is not None
    assert "Direct message content cannot be empty" in error


def test_validation_error_types():
    """Test ValidationErrorType enum values."""
    assert ValidationErrorType.PERMISSION_DENIED.value == "permission_denied"
    assert ValidationErrorType.NOT_FOUND.value == "not_found"
    assert ValidationErrorType.INVALID_INPUT.value == "invalid_input"
    assert ValidationErrorType.CONTENT_TOO_LONG.value == "content_too_long"
    assert ValidationErrorType.CONTENT_EMPTY.value == "content_empty"
    assert ValidationErrorType.INVALID_RANGE.value == "invalid_range"
    assert ValidationErrorType.HIERARCHY_VIOLATION.value == "hierarchy_violation"


if __name__ == "__main__":
    # Run all tests
    test_validation_result_success()
    print("✅ ValidationResult success tests passed")
    
    test_validation_result_error()
    print("✅ ValidationResult error tests passed")
    
    test_operation_context()
    print("✅ OperationContext tests passed")
    
    test_validation_mixin()
    print("✅ ValidationMixin tests passed")
    
    test_message_content_validation_utilities()
    print("✅ Message content validation utilities tests passed")
    
    test_validation_error_types()
    print("✅ ValidationErrorType tests passed")
    
    print("\n🎉 All validation layer tests passed successfully!")