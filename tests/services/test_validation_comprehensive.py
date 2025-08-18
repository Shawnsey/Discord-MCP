"""
Comprehensive tests for the validation layer foundation.

This module provides end-to-end testing of all validation layer
components to ensure they work together correctly.
"""

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


def test_comprehensive_validation_workflow():
    """Test a complete validation workflow using all components."""
    validator = ValidationMixin()
    
    # Create operation context
    context = OperationContext(
        operation_name="send_message",
        guild_id="123456789012345678",
        channel_id="987654321098765432",
        user_id="555666777888999000"
    )
    
    # Test successful validation chain
    print("Testing successful validation chain...")
    
    # Validate Discord IDs
    guild_result = validator._validate_discord_id(context.guild_id, "guild")
    assert guild_result.is_valid, f"Guild ID validation failed: {guild_result.error_message}"
    
    channel_result = validator._validate_discord_id(context.channel_id, "channel")
    assert channel_result.is_valid, f"Channel ID validation failed: {channel_result.error_message}"
    
    user_result = validator._validate_discord_id(context.user_id, "user")
    assert user_result.is_valid, f"User ID validation failed: {user_result.error_message}"
    
    # Validate message content
    message_content = "Hello, Discord! This is a test message."
    content_result = validator._validate_message_content(message_content)
    assert content_result.is_valid, f"Message content validation failed: {content_result.error_message}"
    
    print("✅ All successful validations passed")
    
    # Test error validation chain
    print("Testing error validation chain...")
    
    # Test invalid Discord ID
    invalid_id_result = validator._validate_discord_id("invalid_id", "guild")
    assert not invalid_id_result.is_valid
    assert invalid_id_result.error_type == ValidationErrorType.INVALID_INPUT
    
    # Create error response
    error_response = validator._create_validation_error_response(invalid_id_result, context)
    expected_error = "❌ Error in send_message: Invalid guild ID format. Discord IDs must be numeric"
    assert error_response.error_message == expected_error
    assert error_response.error_type == ValidationErrorType.INVALID_INPUT
    
    # Test empty message content
    empty_content_result = validator._validate_message_content("")
    assert not empty_content_result.is_valid
    assert empty_content_result.error_type == ValidationErrorType.CONTENT_EMPTY
    
    # Test message too long
    long_message = "x" * 2001
    long_content_result = validator._validate_message_content(long_message)
    assert not long_content_result.is_valid
    assert long_content_result.error_type == ValidationErrorType.CONTENT_TOO_LONG
    
    print("✅ All error validations passed")
    
    # Test numeric validations
    print("Testing numeric validations...")
    
    # Test timeout duration
    timeout_result = validator._validate_timeout_duration(1440)  # 24 hours
    assert timeout_result.is_valid
    assert timeout_result.data["value"] == 1440
    
    # Test invalid timeout duration
    invalid_timeout = validator._validate_timeout_duration(50000)  # Too long
    assert not invalid_timeout.is_valid
    assert invalid_timeout.error_type == ValidationErrorType.INVALID_RANGE
    
    # Test message limit
    limit_result = validator._validate_message_limit(50)
    assert limit_result.is_valid
    assert limit_result.data["value"] == 50
    
    # Test ban delete days
    ban_days_result = validator._validate_ban_delete_days(7)
    assert ban_days_result.is_valid
    assert ban_days_result.data["value"] == 7
    
    print("✅ All numeric validations passed")
    
    # Test response creation methods
    print("Testing response creation methods...")
    
    # Test permission denied response
    perm_denied = validator._create_permission_denied_response(
        "channel", 
        context.channel_id, 
        "Bot lacks required permissions."
    )
    expected_perm = f"❌ Error: Access to channel `{context.channel_id}` is not permitted. Bot lacks required permissions."
    assert perm_denied.error_message == expected_perm
    assert perm_denied.error_type == ValidationErrorType.PERMISSION_DENIED
    
    # Test not found response
    not_found = validator._create_not_found_response(
        "message",
        "111222333444555666",
        "Message may have been deleted."
    )
    expected_not_found = "❌ Error: Message `111222333444555666` was not found or bot has no access. Message may have been deleted."
    assert not_found.error_message == expected_not_found
    assert not_found.error_type == ValidationErrorType.NOT_FOUND
    
    print("✅ All response creation tests passed")


def test_validation_result_chaining():
    """Test chaining validation results for complex operations."""
    validator = ValidationMixin()
    
    # Simulate a complex operation that requires multiple validations
    def validate_moderation_action(guild_id: str, user_id: str, duration: int, reason: str):
        """Simulate validating a moderation action with multiple checks."""
        results = []
        
        # Validate guild ID
        guild_result = validator._validate_discord_id(guild_id, "guild")
        results.append(("guild_id", guild_result))
        
        # Validate user ID
        user_result = validator._validate_discord_id(user_id, "user")
        results.append(("user_id", user_result))
        
        # Validate timeout duration
        duration_result = validator._validate_timeout_duration(duration)
        results.append(("duration", duration_result))
        
        # Validate reason (if provided)
        if reason:
            reason_result = validator._validate_string_content(
                reason, "reason", min_length=1, max_length=512
            )
            results.append(("reason", reason_result))
        
        # Check if all validations passed
        failed_validations = [(name, result) for name, result in results if not result.is_valid]
        
        if failed_validations:
            # Return first error
            first_error = failed_validations[0][1]
            return ValidationResult.error(
                f"Validation failed: {first_error.error_message}",
                first_error.error_type
            )
        
        # All validations passed
        return ValidationResult.success({
            "validated_data": {name: result.data for name, result in results}
        })
    
    # Test successful chaining
    result = validate_moderation_action(
        "123456789012345678",
        "987654321098765432", 
        60,
        "Spamming in chat"
    )
    assert result.is_valid
    assert "validated_data" in result.data
    
    # Test failed chaining (invalid guild ID)
    result = validate_moderation_action(
        "invalid_guild",
        "987654321098765432",
        60,
        "Spamming in chat"
    )
    assert not result.is_valid
    assert result.error_type == ValidationErrorType.INVALID_INPUT
    assert "Discord IDs must be numeric" in result.error_message
    
    # Test failed chaining (duration too long)
    result = validate_moderation_action(
        "123456789012345678",
        "987654321098765432",
        50000,  # Too long
        "Spamming in chat"
    )
    assert not result.is_valid
    assert result.error_type == ValidationErrorType.INVALID_RANGE
    
    print("✅ Validation result chaining tests passed")


def test_error_type_coverage():
    """Test that all error types are properly used."""
    validator = ValidationMixin()
    
    # Test each error type
    error_type_tests = [
        (ValidationErrorType.PERMISSION_DENIED, "permission_denied"),
        (ValidationErrorType.NOT_FOUND, "not_found"),
        (ValidationErrorType.INVALID_INPUT, "invalid_input"),
        (ValidationErrorType.CONTENT_TOO_LONG, "content_too_long"),
        (ValidationErrorType.CONTENT_EMPTY, "content_empty"),
        (ValidationErrorType.INVALID_RANGE, "invalid_range"),
        (ValidationErrorType.HIERARCHY_VIOLATION, "hierarchy_violation"),
    ]
    
    for error_type, expected_value in error_type_tests:
        assert error_type.value == expected_value
        
        # Test creating error result with this type
        result = ValidationResult.error(f"Test {expected_value}", error_type)
        assert result.error_type == error_type
        assert not result.is_valid
    
    print("✅ Error type coverage tests passed")


if __name__ == "__main__":
    print("Running comprehensive validation layer tests...\n")
    
    test_comprehensive_validation_workflow()
    print("✅ Comprehensive validation workflow tests passed\n")
    
    test_validation_result_chaining()
    print("✅ Validation result chaining tests passed\n")
    
    test_error_type_coverage()
    print("✅ Error type coverage tests passed\n")
    
    print("🎉 All comprehensive validation tests passed successfully!")