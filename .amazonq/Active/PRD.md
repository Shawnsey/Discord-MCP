# Product Requirements Document (PRD)
## DiscordService Refactor: Service Layer Architecture Implementation

```yaml
# AI_METADATA_START
issue_type: "refactor"
priority: "medium"
complexity: "moderate"
estimated_effort: "1-2days"
affected_components: ["backend", "api", "tools", "resources"]
programming_languages: ["python"]
frameworks: ["fastmcp", "discord_api"]
requires_database_changes: false
requires_api_changes: false
requires_ui_changes: false
breaking_changes: false
# AI_METADATA_END
```

---

## Executive Summary

**Business Problem**: The Discord MCP server currently suffers from significant code duplication between `tools.py` and `resources.py`, with nearly identical implementations for core Discord API operations. This technical debt reduces maintainability, increases the risk of bugs, and violates DRY (Don't Repeat Yourself) principles.

**Proposed Solution**: Create a centralized `DiscordService` class that consolidates all Discord API interactions into a single, well-designed service layer. This refactor will eliminate code duplication, improve testability, and establish a clean separation of concerns following established service layer architecture patterns.

**Expected Outcomes**: 
- Reduce codebase size by ~60% through elimination of duplicated functionality
- Improve maintainability and reduce bug risk
- Establish foundation for future Discord feature enhancements
- Enhance test coverage and code quality

---

## Issue Classification

- [x] **Refactoring** (Code structure improvement)
- [ ] Bug Report
- [ ] Feature Request  
- [ ] Enhancement
- [ ] Documentation
- [ ] Configuration

---

## Priority & Impact Assessment

- [ ] Critical
- [x] **Medium** - Significant technical debt that impacts development velocity
- [ ] Low

**Impact Areas:**
- **Developer Experience**: High positive impact on maintainability
- **Code Quality**: Significant improvement in architecture and testability
- **Performance**: Neutral (no performance impact expected)
- **User Experience**: No direct impact (internal refactor)

---

## Current State Analysis

### Existing Implementation Issues

Based on analysis of the Discord MCP codebase, the following critical issues have been identified:

#### Code Duplication Patterns

**1. Guild Operations Duplication**
- `tools.py` lines 23-89: `list_guilds()` implementation
- `resources.py` lines 18-84: Nearly identical `list_guilds()` implementation
- **Duplication**: ~66 lines of identical logic for guild fetching, filtering, and formatting

**2. Channel Operations Duplication**  
- `tools.py` lines 91-207: `list_channels()` implementation
- `resources.py` lines 86-202: Nearly identical `list_channels()` implementation
- **Duplication**: ~116 lines of identical logic for channel retrieval and categorization

**3. Message Operations Duplication**
- `tools.py` lines 209-325: `get_messages()` implementation  
- `resources.py` lines 204-320: Nearly identical message retrieval logic
- **Duplication**: ~116 lines of identical message processing and formatting

**4. Shared Infrastructure Patterns**
```python
# Repeated in both files:
ctx = server.get_context()
lifespan_ctx = ctx.request_context.lifespan_context
discord_client: DiscordClient = lifespan_ctx["discord_client"]
settings: Settings = lifespan_ctx["settings"]
```

**5. Identical Error Handling**
```python
# Duplicated error patterns:
except DiscordAPIError as e:
    error_msg = f"Discord API error while fetching: {str(e)}"
    logger.error("Discord API error", error=str(e))
    return f"# Error\n\n{error_msg}"
```

#### Technical Debt Metrics
- **Total Duplicated Lines**: ~298 lines of code
- **Maintenance Burden**: Changes require updates in 2 locations
- **Bug Risk**: High (inconsistencies between implementations)
- **Test Coverage Gap**: Duplicated logic requires duplicate test coverage

---

## Proposed Solution: DiscordService Architecture

### Service Layer Design Principles

Following established service layer architecture patterns, the `DiscordService` will implement:

1. **Single Responsibility**: Centralized Discord API interaction logic
2. **Dependency Injection**: Clean integration with FastMCP lifecycle
3. **Interface Segregation**: Clear contract definition for Discord operations
4. **Error Handling**: Consistent error management and logging
5. **Testability**: Mockable interface for comprehensive testing

### Technical Architecture

```yaml
# TECHNICAL_SPECS_START
service_architecture:
  interface: "IDiscordService (abstract base class)"
  implementation: "DiscordService (concrete implementation)"
  dependencies: ["DiscordClient", "Settings", "structlog.Logger"]
  
integration_points:
  tools_py: "Refactor all Discord operations to use DiscordService"
  resources_py: "Refactor all Discord operations to use DiscordService"
  server_py: "Register DiscordService in lifespan context"
  
new_files:
  - "src/discord_mcp/services/__init__.py"
  - "src/discord_mcp/services/discord_service.py"
  - "src/discord_mcp/services/interfaces.py"

modified_files:
  - "src/discord_mcp/tools.py"
  - "src/discord_mcp/resources.py" 
  - "src/discord_mcp/server.py"
  - "tests/test_tools.py"
  - "tests/test_resources.py"
# TECHNICAL_SPECS_END
```

### Service Interface Definition

```python
# src/discord_mcp/services/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IDiscordService(ABC):
    """Interface for Discord API service operations."""
    
    @abstractmethod
    async def get_guilds_formatted(self) -> str:
        """Get formatted list of accessible Discord guilds."""
        pass
    
    @abstractmethod
    async def get_channels_formatted(self, guild_id: str) -> str:
        """Get formatted list of channels in a guild."""
        pass
    
    @abstractmethod
    async def get_messages_formatted(self, channel_id: str, limit: int = 50) -> str:
        """Get formatted list of messages from a channel."""
        pass
    
    @abstractmethod
    async def get_user_info_formatted(self, user_id: str) -> str:
        """Get formatted user information."""
        pass
    
    @abstractmethod
    async def send_message(self, channel_id: str, content: str, 
                          reply_to_message_id: Optional[str] = None) -> str:
        """Send a message to a Discord channel."""
        pass
    
    @abstractmethod
    async def send_direct_message(self, user_id: str, content: str) -> str:
        """Send a direct message to a user."""
        pass
```

### Service Implementation Structure

```python
# src/discord_mcp/services/discord_service.py
class DiscordService(IDiscordService):
    """Centralized service for Discord API operations."""
    
    def __init__(self, discord_client: DiscordClient, settings: Settings, logger):
        self._discord_client = discord_client
        self._settings = settings
        self._logger = logger
    
    async def get_guilds_formatted(self) -> str:
        """Consolidated guild fetching logic."""
        # Single implementation replacing duplicated code
        pass
    
    # Additional methods following same pattern...
    
    def _handle_discord_error(self, error: DiscordAPIError, operation: str) -> str:
        """Centralized error handling for Discord operations."""
        pass
    
    def _check_permissions(self, guild_id: str = None, channel_id: str = None) -> bool:
        """Centralized permission checking logic."""
        pass
```

---

## Detailed Requirements

### Functional Requirements

#### Core Service Operations
- [ ] **Guild Operations**: Centralized guild listing with filtering and formatting
- [ ] **Channel Operations**: Centralized channel listing with categorization
- [ ] **Message Operations**: Centralized message retrieval and formatting
- [ ] **User Operations**: Centralized user information retrieval
- [ ] **Messaging Operations**: Centralized message sending (channels and DMs)

#### Service Integration
- [ ] **Tools Integration**: All tools use DiscordService instead of direct client calls
- [ ] **Resources Integration**: All resources use DiscordService instead of direct client calls
- [ ] **Lifecycle Management**: DiscordService properly registered in FastMCP context
- [ ] **Dependency Injection**: Clean injection of DiscordClient and Settings

#### Error Handling & Logging
- [ ] **Consistent Error Handling**: Single error handling strategy across all operations
- [ ] **Structured Logging**: Consistent logging patterns with proper context
- [ ] **Permission Validation**: Centralized permission checking logic
- [ ] **API Error Translation**: Consistent translation of Discord API errors to user messages

### Technical Requirements

```yaml
# IMPLEMENTATION_REQUIREMENTS_START
code_organization:
  - "Create services package with proper __init__.py"
  - "Implement IDiscordService interface with all required methods"
  - "Create DiscordService implementation with comprehensive error handling"
  - "Update server.py to register DiscordService in lifespan context"

refactoring_requirements:
  - "Replace direct discord_client calls in tools.py with service calls"
  - "Replace direct discord_client calls in resources.py with service calls"
  - "Maintain exact same public API for tools and resources"
  - "Preserve all existing functionality and behavior"

testing_requirements:
  - "Create comprehensive unit tests for DiscordService"
  - "Update existing tool tests to mock DiscordService"
  - "Update existing resource tests to mock DiscordService"
  - "Maintain 100% test coverage for all modified code"

performance_requirements:
  - "No performance degradation from current implementation"
  - "Service instantiation overhead < 1ms"
  - "Memory usage increase < 5MB"
# IMPLEMENTATION_REQUIREMENTS_END
```

### Quality Requirements

#### Code Quality Metrics
- [ ] **Code Reduction**: Achieve 60%+ reduction in duplicated code lines
- [ ] **Cyclomatic Complexity**: Maintain complexity score < 10 per method
- [ ] **Test Coverage**: Maintain 90%+ test coverage across all modified files
- [ ] **Type Safety**: Full type hints for all service methods and parameters

#### Maintainability Requirements
- [ ] **Documentation**: Comprehensive docstrings for all service methods
- [ ] **Code Style**: Consistent with existing codebase (Black, isort formatting)
- [ ] **Error Messages**: Clear, actionable error messages for all failure scenarios
- [ ] **Logging**: Structured logging with appropriate log levels

---

## Acceptance Criteria

### Phase 1: Service Foundation (Day 1)
- [ ] **Service Interface Created**: `IDiscordService` interface with all required methods
- [ ] **Service Implementation**: `DiscordService` class with core Discord operations
- [ ] **Error Handling**: Centralized error handling and logging mechanisms
- [ ] **Unit Tests**: Comprehensive test suite for DiscordService (90%+ coverage)
- [ ] **Integration Setup**: DiscordService registered in FastMCP lifespan context

### Phase 2: Tools Refactor (Day 1-2)
- [ ] **Tools Migration**: All tools.py functions use DiscordService instead of direct client
- [ ] **API Compatibility**: All existing tool APIs remain unchanged
- [ ] **Functionality Preservation**: All existing tool behaviors preserved exactly
- [ ] **Test Updates**: All tool tests updated to mock DiscordService
- [ ] **Integration Tests**: All tool integration tests pass

### Phase 3: Resources Refactor (Day 2)
- [ ] **Resources Migration**: All resources.py functions use DiscordService
- [ ] **API Compatibility**: All existing resource APIs remain unchanged  
- [ ] **Functionality Preservation**: All existing resource behaviors preserved exactly
- [ ] **Test Updates**: All resource tests updated to mock DiscordService
- [ ] **Integration Tests**: All resource integration tests pass

### Phase 4: Validation & Cleanup (Day 2)
- [ ] **Code Cleanup**: Remove all duplicated code from tools.py and resources.py
- [ ] **Documentation Updates**: Update README.md and code documentation
- [ ] **Performance Validation**: Confirm no performance regression
- [ ] **End-to-End Testing**: Full integration test suite passes
- [ ] **Code Review**: Peer review completed and approved

### Success Metrics

#### Quantitative Metrics
- [ ] **Code Reduction**: Reduce total lines of code by 250+ lines
- [ ] **Duplication Elimination**: 0% code duplication between tools and resources
- [ ] **Test Coverage**: Maintain 90%+ coverage across all modified files
- [ ] **Performance**: No degradation in response times (< 5% variance)

#### Qualitative Metrics
- [ ] **Maintainability**: Single location for Discord API logic changes
- [ ] **Testability**: Improved ability to mock Discord operations in tests
- [ ] **Code Quality**: Improved separation of concerns and architecture
- [ ] **Developer Experience**: Easier to add new Discord features

---

## Implementation Strategy

### Development Approach

#### Phase 1: Foundation (Hours 1-4)
```yaml
tasks:
  - "Create services package structure"
  - "Implement IDiscordService interface"
  - "Create DiscordService implementation with core methods"
  - "Add comprehensive error handling and logging"
  - "Write unit tests for DiscordService"
  - "Update server.py to register service in context"

deliverables:
  - "src/discord_mcp/services/ package with interface and implementation"
  - "Comprehensive unit test suite"
  - "Updated server.py with service registration"

validation:
  - "All new tests pass"
  - "Service can be instantiated and basic operations work"
  - "Integration with FastMCP lifecycle successful"
```

#### Phase 2: Tools Refactor (Hours 5-8)
```yaml
tasks:
  - "Refactor list_guilds tool to use DiscordService"
  - "Refactor list_channels tool to use DiscordService"
  - "Refactor get_messages tool to use DiscordService"
  - "Refactor get_user_info tool to use DiscordService"
  - "Refactor messaging tools to use DiscordService"
  - "Update all tool tests to mock DiscordService"

deliverables:
  - "Refactored tools.py with service integration"
  - "Updated test suite with service mocking"

validation:
  - "All existing tool tests pass"
  - "Integration tests demonstrate identical behavior"
  - "No breaking changes to tool APIs"
```

#### Phase 3: Resources Refactor (Hours 9-12)
```yaml
tasks:
  - "Refactor guild resource to use DiscordService"
  - "Refactor channel resource to use DiscordService"
  - "Refactor message resource to use DiscordService"
  - "Refactor user resource to use DiscordService"
  - "Update all resource tests to mock DiscordService"

deliverables:
  - "Refactored resources.py with service integration"
  - "Updated test suite with service mocking"

validation:
  - "All existing resource tests pass"
  - "Integration tests demonstrate identical behavior"
  - "No breaking changes to resource APIs"
```

#### Phase 4: Validation & Documentation (Hours 13-16)
```yaml
tasks:
  - "Remove all duplicated code"
  - "Update documentation and README"
  - "Run comprehensive test suite"
  - "Performance testing and validation"
  - "Code review and final cleanup"

deliverables:
  - "Clean, deduplicated codebase"
  - "Updated documentation"
  - "Performance validation report"

validation:
  - "All tests pass (unit, integration, end-to-end)"
  - "No performance regression"
  - "Code review approved"
```

### Risk Assessment & Mitigation

#### Technical Risks

**Risk: Breaking Changes to Existing APIs**
- *Probability*: Low
- *Impact*: High
- *Mitigation*: Maintain exact same method signatures and return types; comprehensive integration testing

**Risk: Performance Degradation**
- *Probability*: Low  
- *Impact*: Medium
- *Mitigation*: Performance testing at each phase; service instantiation optimization

**Risk: Test Coverage Reduction**
- *Probability*: Medium
- *Impact*: Medium
- *Mitigation*: Update tests incrementally; maintain coverage metrics throughout

#### Implementation Risks

**Risk: Complex Integration with FastMCP Lifecycle**
- *Probability*: Medium
- *Impact*: Medium
- *Mitigation*: Study existing patterns; implement service registration carefully

**Risk: Inconsistent Error Handling**
- *Probability*: Low
- *Impact*: Medium
- *Mitigation*: Centralized error handling design; comprehensive error scenario testing

### Rollback Strategy

**Rollback Triggers:**
- Any integration test failures
- Performance regression > 10%
- Breaking changes to existing APIs

**Rollback Process:**
1. Revert all changes to tools.py and resources.py
2. Remove services package
3. Restore original server.py configuration
4. Validate all tests pass with original implementation

---

## Dependencies & Constraints

### Technical Dependencies

#### Internal Dependencies
- **DiscordClient**: Core Discord API client (no changes required)
- **Settings**: Configuration management (no changes required)
- **FastMCP**: Server framework (service registration integration needed)
- **structlog**: Logging framework (no changes required)

#### External Dependencies
- **No new external dependencies required**
- **All existing dependencies remain unchanged**

### Development Constraints

#### Compatibility Requirements
- **Python Version**: Must work with existing Python 3.8+ requirement
- **FastMCP Version**: Must be compatible with current FastMCP version
- **Discord API**: Must maintain compatibility with existing Discord API usage

#### Performance Constraints
- **Response Time**: No degradation in API response times
- **Memory Usage**: Service overhead must be minimal (< 5MB)
- **Startup Time**: No significant impact on server startup time

#### Testing Constraints
- **Test Coverage**: Must maintain current 90%+ test coverage
- **Test Performance**: Test suite execution time must not increase significantly
- **Mock Compatibility**: New service must be easily mockable for testing

---

## Testing Requirements

```yaml
# TESTING_REQUIREMENTS_START
test_types_needed:
  unit_tests: "Test DiscordService methods in isolation with mocked dependencies"
  integration_tests: "Test service integration with tools and resources"
  contract_tests: "Verify service interface compliance"
  performance_tests: "Validate no performance regression"

test_scenarios:
  happy_path: "All Discord operations succeed with valid inputs"
  error_cases: "Discord API errors, network failures, invalid permissions"
  boundary_conditions: "Empty results, large datasets, rate limiting"
  integration_scenarios: "Service integration with FastMCP lifecycle"

test_data_requirements:
  mock_discord_responses: "Comprehensive mock data for all Discord API calls"
  test_configurations: "Various settings configurations for permission testing"
  error_scenarios: "Mock error responses for all failure cases"

coverage_requirements:
  service_coverage: "95%+ coverage for DiscordService implementation"
  integration_coverage: "90%+ coverage for refactored tools and resources"
  error_handling_coverage: "100% coverage for error handling paths"
# TESTING_REQUIREMENTS_END
```

### Test Implementation Strategy

#### Unit Tests for DiscordService
```python
# Example test structure
class TestDiscordService:
    async def test_get_guilds_formatted_success(self):
        # Test successful guild retrieval and formatting
        pass
    
    async def test_get_guilds_formatted_api_error(self):
        # Test Discord API error handling
        pass
    
    async def test_get_guilds_formatted_permission_denied(self):
        # Test permission filtering
        pass
```

#### Integration Tests
```python
# Example integration test
class TestToolsServiceIntegration:
    async def test_list_guilds_tool_uses_service(self):
        # Verify tools use service instead of direct client
        pass
```

---

## Documentation Requirements

### Code Documentation
- **Service Interface**: Comprehensive docstrings for all interface methods
- **Service Implementation**: Detailed implementation documentation with examples
- **Error Handling**: Documentation of all error scenarios and responses
- **Integration Guide**: How to use the service in tools and resources

### User Documentation
- **README Updates**: Update architecture section to reflect service layer
- **API Documentation**: No changes required (public APIs unchanged)
- **Developer Guide**: Add section on service layer architecture
- **Migration Notes**: Document the refactoring changes for future developers

### Technical Documentation
- **Architecture Diagrams**: Update to show service layer
- **Sequence Diagrams**: Show interaction flow through service
- **Error Handling Guide**: Centralized error handling documentation
- **Testing Guide**: How to test with the new service architecture

---

## Success Criteria & Validation

### Definition of Done

#### Technical Completion
- [ ] All acceptance criteria met across all phases
- [ ] Zero code duplication between tools.py and resources.py
- [ ] All existing tests pass without modification to test expectations
- [ ] New service has comprehensive test coverage (95%+)
- [ ] Performance benchmarks show no regression

#### Quality Validation
- [ ] Code review completed and approved
- [ ] All linting and formatting checks pass
- [ ] Documentation updated and reviewed
- [ ] Integration tests demonstrate identical behavior to original implementation

#### Operational Readiness
- [ ] Service integrates cleanly with FastMCP lifecycle
- [ ] Error handling provides clear, actionable messages
- [ ] Logging provides appropriate debugging information
- [ ] Service can be easily extended for future Discord features

### Post-Implementation Benefits

#### Immediate Benefits
- **Reduced Maintenance Burden**: Single location for Discord API logic changes
- **Improved Code Quality**: Better separation of concerns and architecture
- **Enhanced Testability**: Easier to mock Discord operations in tests
- **Eliminated Technical Debt**: No more duplicated code maintenance

#### Long-term Benefits
- **Faster Feature Development**: New Discord features only need service implementation
- **Improved Reliability**: Centralized error handling reduces inconsistencies
- **Better Developer Experience**: Clear service interface for Discord operations
- **Foundation for Growth**: Service layer enables future architectural improvements

---

## Appendix

### Code Examples

#### Current Duplication Example
```python
# tools.py - lines 23-45
async def list_guilds() -> str:
    try:
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_client: DiscordClient = lifespan_ctx["discord_client"]
        settings: Settings = lifespan_ctx["settings"]
        
        guilds = await discord_client.get_user_guilds()
        # ... formatting logic ...
        
    except DiscordAPIError as e:
        error_msg = f"Discord API error: {str(e)}"
        return f"# Error\n\n{error_msg}"

# resources.py - lines 18-40 (nearly identical)
async def list_guilds() -> str:
    try:
        ctx = server.get_context()
        lifespan_ctx = ctx.request_context.lifespan_context
        discord_client: DiscordClient = lifespan_ctx["discord_client"]
        settings: Settings = lifespan_ctx["settings"]
        
        guilds = await discord_client.get_user_guilds()
        # ... identical formatting logic ...
        
    except DiscordAPIError as e:
        error_msg = f"Discord API error: {str(e)}"
        return f"# Error\n\n{error_msg}"
```

#### Proposed Service Solution
```python
# After refactor - tools.py
async def list_guilds() -> str:
    ctx = server.get_context()
    discord_service = ctx.request_context.lifespan_context["discord_service"]
    return await discord_service.get_guilds_formatted()

# After refactor - resources.py  
async def list_guilds() -> str:
    ctx = server.get_context()
    discord_service = ctx.request_context.lifespan_context["discord_service"]
    return await discord_service.get_guilds_formatted()

# Single implementation in DiscordService
async def get_guilds_formatted(self) -> str:
    try:
        guilds = await self._discord_client.get_user_guilds()
        # ... single formatting implementation ...
    except DiscordAPIError as e:
        return self._handle_discord_error(e, "fetching guilds")
```

### File Structure After Implementation

```
src/discord_mcp/
├── services/
│   ├── __init__.py
│   ├── interfaces.py          # IDiscordService interface
│   └── discord_service.py     # DiscordService implementation
├── tools.py                   # Refactored to use DiscordService
├── resources.py               # Refactored to use DiscordService
├── server.py                  # Updated with service registration
└── ...

tests/
├── services/
│   ├── __init__.py
│   └── test_discord_service.py  # Comprehensive service tests
├── test_tools.py              # Updated with service mocking
├── test_resources.py          # Updated with service mocking
└── ...
```

---

**Document Version**: 1.0  
**Created**: 2025-08-07  
**Author**: AI Assistant  
**Review Status**: Pending Review  
**Implementation Target**: 1-2 days

---

*This PRD follows software architecture best practices and is designed to provide comprehensive guidance for implementing a clean service layer architecture while eliminating technical debt through code deduplication.*
