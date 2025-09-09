"""
Unit tests for message content validation utilities.

This module provides comprehensive tests for the new message content
validation methods added to the validation layer.
"""

import pytest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from discord_mcp.services.validation import (
    ValidationResult,
    ValidationErrorType,
    ValidationMixin,
    ValidationConstants,
)


class TestMessageContentValidation:
    """Test class for message content validation utilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ValidationMixin()

    def test_validate_message_content_success(self):
        """Test successful message content validation."""
        # Valid message content
        result = self.validator._validate_message_content("Hello, Discord!")
        assert result.is_valid is True
        assert result.data == {"content": "Hello, Discord!"}
        assert result.error_message is None
        assert result.error_type is None

    def test_validate_message_content_empty(self):
        """Test message content validation with empty content."""
        # Empty string
        result = self.validator._validate_message_content("")
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_EMPTY
        assert "Message content cannot be empty" in result.error_message

        # Whitespace only
        result = self.validator._validate_message_content("   ")
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_EMPTY

    def test_validate_message_content_too_long(self):
        """Test message content validation with content too long."""
        # Content exceeding Discord limit
        long_content = "x" * (ValidationConstants.MESSAGE_MAX_LENGTH + 1)
        result = self.validator._validate_message_content(long_content)
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_TOO_LONG
        assert "too long" in result.error_message
        assert str(ValidationConstants.MESSAGE_MAX_LENGTH) in result.error_message

    def test_validate_message_content_for_editing(self):
        """Test message content validation for editing operations."""
        # Valid edit content
        result = self.validator._validate_message_content_for_editing("Updated message")
        assert result.is_valid is True
        assert result.data == {"content": "Updated message"}

        # Empty edit content
        result = self.validator._validate_message_content_for_editing("")
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_EMPTY
        assert "New message content" in result.error_message

    def test_validate_message_content_for_dm(self):
        """Test message content validation for direct messages."""
        # Valid DM content
        result = self.validator._validate_message_content_for_dm("Direct message")
        assert result.is_valid is True
        assert result.data == {"content": "Direct message"}

        # Empty DM content
        result = self.validator._validate_message_content_for_dm("")
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.CONTENT_EMPTY

    def test_create_message_validation_error_response(self):
        """Test creating message validation error responses."""
        # Test with empty content error
        validation_result = ValidationResult.error(
            "Message content cannot be empty", ValidationErrorType.CONTENT_EMPTY
        )

        # Default message operation
        response = self.validator._create_message_validation_error_response(
            validation_result, "message"
        )
        assert "❌ Error: Message content cannot be empty" in response
        assert "Please provide a non-empty message content" in response

        # Edit operation
        response = self.validator._create_message_validation_error_response(
            validation_result, "edit"
        )
        assert "New message content cannot be empty" in response

        # DM operation
        response = self.validator._create_message_validation_error_response(
            validation_result, "dm"
        )
        assert "Direct message content cannot be empty" in response

    def test_create_message_validation_error_response_too_long(self):
        """Test creating error responses for content too long."""
        validation_result = ValidationResult.error(
            f"Message content is too long (2500 characters). Maximum allowed is {ValidationConstants.MESSAGE_MAX_LENGTH} characters",
            ValidationErrorType.CONTENT_TOO_LONG,
        )

        response = self.validator._create_message_validation_error_response(
            validation_result, "message"
        )
        assert "❌ Error:" in response
        assert "too long" in response
        assert "Please shorten your message" in response

    def test_create_message_validation_error_response_valid_result(self):
        """Test creating error response with valid validation result."""
        validation_result = ValidationResult.success({"content": "Valid content"})

        response = self.validator._create_message_validation_error_response(
            validation_result, "message"
        )
        assert response == ""

    def test_create_message_content_empty_response(self):
        """Test creating empty content error responses."""
        # Message operation
        response = self.validator._create_message_content_empty_response("message")
        assert response == "❌ Error: Message content cannot be empty."

        # Edit operation
        response = self.validator._create_message_content_empty_response("edit")
        assert response == "❌ Error: New message content cannot be empty."

        # DM operation
        response = self.validator._create_message_content_empty_response("dm")
        assert response == "❌ Error: Direct message content cannot be empty."

        # Unknown operation (should default to "Message")
        response = self.validator._create_message_content_empty_response("unknown")
        assert response == "❌ Error: Message content cannot be empty."

    def test_create_message_content_too_long_response(self):
        """Test creating content too long error responses."""
        content_length = 2500

        # Message operation
        response = self.validator._create_message_content_too_long_response(
            content_length, "message"
        )
        expected = f"❌ Error: Message content too long ({content_length} characters). Discord limit is {ValidationConstants.MESSAGE_MAX_LENGTH} characters."
        assert response == expected

        # Edit operation
        response = self.validator._create_message_content_too_long_response(
            content_length, "edit"
        )
        assert "Message content too long" in response
        assert str(content_length) in response

        # DM operation
        response = self.validator._create_message_content_too_long_response(
            content_length, "dm"
        )
        assert "Message content too long" in response
        assert str(ValidationConstants.MESSAGE_MAX_LENGTH) in response

    def test_validate_and_format_message_content_error(self):
        """Test the convenience method for validation and error formatting."""
        # Valid content should return None
        error = self.validator._validate_and_format_message_content_error(
            "Valid content", "message"
        )
        assert error is None

        # Empty content should return formatted error
        error = self.validator._validate_and_format_message_content_error("", "message")
        assert error is not None
        assert "❌ Error: Message content cannot be empty" in error
        assert "Please provide a non-empty message content" in error

        # Too long content should return formatted error
        long_content = "x" * (ValidationConstants.MESSAGE_MAX_LENGTH + 1)
        error = self.validator._validate_and_format_message_content_error(
            long_content, "message"
        )
        assert error is not None
        assert "too long" in error
        assert str(ValidationConstants.MESSAGE_MAX_LENGTH) in error

    def test_validate_and_format_message_content_error_operation_types(self):
        """Test the convenience method with different operation types."""
        # Edit operation
        error = self.validator._validate_and_format_message_content_error("", "edit")
        assert error is not None
        assert "New message content cannot be empty" in error

        # DM operation
        error = self.validator._validate_and_format_message_content_error("", "dm")
        assert error is not None
        assert "Direct message content cannot be empty" in error

        # Unknown operation (should default to message)
        error = self.validator._validate_and_format_message_content_error("", "unknown")
        assert error is not None
        assert "Message content cannot be empty" in error

    def test_edge_cases(self):
        """Test edge cases for message content validation."""
        # Content at exact limit should be valid
        max_content = "x" * ValidationConstants.MESSAGE_MAX_LENGTH
        result = self.validator._validate_message_content(max_content)
        assert result.is_valid is True

        # Content with newlines and special characters
        special_content = "Hello\nWorld! 🎉 @everyone #general"
        result = self.validator._validate_message_content(special_content)
        assert result.is_valid is True

        # Content with only whitespace at the beginning and end (should be trimmed)
        padded_content = "  Hello World  "
        result = self.validator._validate_message_content(padded_content)
        assert result.is_valid is True
        assert result.data == {"content": "Hello World"}

    def test_none_content(self):
        """Test validation with None content."""
        # This should be handled by the StringValidator
        result = self.validator._validate_message_content(None)
        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_INPUT
        assert "cannot be None" in result.error_message


if __name__ == "__main__":
    # Run all tests
    test_instance = TestMessageContentValidation()
    test_instance.setup_method()

    # Run each test method
    test_methods = [
        test_instance.test_validate_message_content_success,
        test_instance.test_validate_message_content_empty,
        test_instance.test_validate_message_content_too_long,
        test_instance.test_validate_message_content_for_editing,
        test_instance.test_validate_message_content_for_dm,
        test_instance.test_create_message_validation_error_response,
        test_instance.test_create_message_validation_error_response_too_long,
        test_instance.test_create_message_validation_error_response_valid_result,
        test_instance.test_create_message_content_empty_response,
        test_instance.test_create_message_content_too_long_response,
        test_instance.test_validate_and_format_message_content_error,
        test_instance.test_validate_and_format_message_content_error_operation_types,
        test_instance.test_edge_cases,
        test_instance.test_none_content,
    ]

    for i, test_method in enumerate(test_methods, 1):
        try:
            test_method()
            print(f"✅ Test {i}/{len(test_methods)}: {test_method.__name__} passed")
        except Exception as e:
            print(
                f"❌ Test {i}/{len(test_methods)}: {test_method.__name__} failed: {e}"
            )
            raise

    print(
        f"\n🎉 All {len(test_methods)} message content validation tests passed successfully!"
    )
