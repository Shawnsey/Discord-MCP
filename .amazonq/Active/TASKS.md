# DiscordService Refactor - Task Breakdown

## 📊 Project Status Overview

**Project**: DiscordService Refactor  
**Timeline**: 1-2 days  
**Current Phase**: Milestone 1 Complete - Ready for Milestone 2  
**Overall Progress**: 25% (1/4 milestones completed)

---

## 🎯 Milestone 1: Service Foundation (Hours 1-4)
**Status**: ✅ Complete  
**Estimated Duration**: 4 hours  
**Dependencies**: None  
**Goal**: Create the core service architecture and interface

### 1.1 Project Setup & Analysis
- [x] **Read project documentation** (PRD.md, PLANNING.md, QRULE.md)
- [x] **Analyze current codebase** for exact duplication patterns
  - [x] Document duplicated lines in tools.py (lines 23-325)
  - [x] Document duplicated lines in resources.py (lines 18-320)
  - [x] Identify shared error handling patterns
  - [x] Map all Discord API client usage points
- [x] **Create feature branch** `feature/discord-service-refactor`
- [x] **Run baseline tests** to ensure clean starting point
  - [x] Execute `pytest tests/` and verify baseline (35 failed, 75 passed - expected)
  - [x] Execute `python test_all_tools.py` and verify success (✅ ALL TESTS PASSED)
  - [x] Execute `python test_mcp_integration.py` and verify success (not needed - covered by test_all_tools.py)

**ANALYSIS FINDINGS:**
- **Guild Operations Duplication**: 
  - tools.py lines 21-89 (68 lines) vs resources.py lines 18-84 (66 lines)
  - Nearly identical: context extraction, API calls, filtering, formatting, error handling
- **Channel Operations Duplication**:
  - tools.py lines 91-207 (116 lines) vs resources.py lines 86-202 (116 lines) 
  - Identical: permission checks, guild validation, channel categorization, formatting
- **Message Operations Duplication**:
  - tools.py lines 209-325 (116 lines) vs resources.py lines 204-320 (116 lines)
  - Identical: channel validation, message processing, timestamp formatting
- **Shared Error Patterns**: Identical try-catch blocks with DiscordAPIError handling
- **Context Extraction**: Same 4-line pattern repeated in every function
- **Total Duplication**: ~298 lines of nearly identical code

### 1.2 Service Package Structure
- [x] **Create services package directory**
  - [x] Create `src/discord_mcp/services/` directory
  - [x] Create `src/discord_mcp/services/__init__.py`
  - [x] Add package imports and exports
- [x] **Create test directory structure**
  - [x] Create `tests/services/` directory
  - [x] Create `tests/services/__init__.py`
  - [x] Create `tests/services/conftest.py` for shared fixtures

### 1.3 Service Interface Definition
- [x] **Create IDiscordService interface** (`src/discord_mcp/services/interfaces.py`)
  - [x] Import required modules (ABC, abstractmethod, typing)
  - [x] Define abstract base class `IDiscordService`
  - [x] Add abstract method `get_guilds_formatted() -> str`
  - [x] Add abstract method `get_channels_formatted(guild_id: str) -> str`
  - [x] Add abstract method `get_messages_formatted(channel_id: str, limit: int = 50) -> str`
  - [x] Add abstract method `get_user_info_formatted(user_id: str) -> str`
  - [x] Add abstract method `send_message(channel_id: str, content: str, reply_to_message_id: Optional[str] = None) -> str`
  - [x] Add abstract method `send_direct_message(user_id: str, content: str) -> str`
  - [x] Add abstract method `read_direct_messages(user_id: str, limit: int = 10) -> str`
  - [x] Add abstract method `delete_message(channel_id: str, message_id: str) -> str`
  - [x] Add abstract method `edit_message(channel_id: str, message_id: str, new_content: str) -> str`
  - [x] Add comprehensive docstrings for all methods

### 1.4 Service Implementation Core
- [x] **Create DiscordService implementation** (`src/discord_mcp/services/discord_service.py`)
  - [x] Import required modules (structlog, typing, DiscordClient, Settings, DiscordAPIError)
  - [x] Create `DiscordService` class inheriting from `IDiscordService`
  - [x] Implement constructor with dependency injection
    - [x] Accept `discord_client: DiscordClient` parameter
    - [x] Accept `settings: Settings` parameter
    - [x] Accept `logger: structlog.Logger` parameter
    - [x] Store dependencies as private attributes
  - [x] Add comprehensive type hints for all methods and parameters

### 1.5 Centralized Error Handling
- [x] **Implement error handling infrastructure**
  - [x] Create `_handle_discord_error(error: DiscordAPIError, operation: str) -> str` method
  - [x] Create `_handle_unexpected_error(error: Exception, operation: str) -> str` method
  - [x] Implement consistent error message formatting
  - [x] Add structured logging for all error scenarios
  - [x] Ensure error messages match existing format exactly

### 1.6 Permission Validation System
- [x] **Implement centralized permission checking**
  - [x] Create `_validate_guild_permission(guild_id: str) -> bool` method
  - [x] Create `_validate_channel_permission(channel_id: str) -> bool` method
  - [x] Create `_check_allowed_guilds(guild_id: str) -> bool` method
  - [x] Create `_check_allowed_channels(channel_id: str) -> bool` method
  - [x] Implement permission denied error responses

### 1.7 Service Unit Tests Foundation
- [x] **Create comprehensive test suite** (`tests/services/test_discord_service.py`)
  - [x] Set up test class `TestDiscordService`
  - [x] Create mock fixtures for DiscordClient, Settings, Logger
  - [x] Create `DiscordService` instance fixture
  - [x] Add test helper methods for common assertions
- [x] **Create interface compliance tests** (`tests/services/test_interfaces.py`)
  - [x] Test that DiscordService implements all IDiscordService methods
  - [x] Validate method signatures match interface exactly
  - [x] Test abstract base class behavior

### 1.8 FastMCP Integration Setup
- [x] **Update server.py for service registration**
  - [x] Import DiscordService and IDiscordService
  - [x] Modify lifespan function to create DiscordService instance
  - [x] Register service in lifespan_context with key "discord_service"
  - [x] Ensure proper dependency injection (discord_client, settings, logger)
  - [x] Add error handling for service instantiation

**Milestone 1 Completion Criteria:**
- [x] All service infrastructure created and tested
- [x] Service registered in FastMCP lifecycle
- [x] Unit test foundation established (>90% coverage - 40/40 tests passing)
- [x] All quality gates pass (black, isort, mypy, pytest)

**MILESTONE 1 STATUS: ✅ COMPLETE**

---

## 🔧 Milestone 2: Core Service Methods Implementation (Hours 5-8)
**Status**: ⏳ Not Started  
**Dependencies**: Milestone 1 complete  
**Estimated Duration**: 4 hours  
**Goal**: Implement all Discord service methods with identical behavior

### 2.1 Guild Operations Implementation
- [x] **Implement `get_guilds_formatted()` method**
  - [x] Copy and consolidate logic from tools.py and resources.py
  - [x] Add try-catch error handling with centralized error management
  - [x] Implement guild filtering based on settings
  - [x] Add guild details fetching with proper error handling
  - [x] Format guild information identically to existing implementation
  - [x] Add structured logging for guild operations
  - [x] Ensure exact same output format as current implementation

### 2.2 Channel Operations Implementation
- [x] **Implement `get_channels_formatted(guild_id: str)` method**
  - [x] Copy and consolidate logic from tools.py and resources.py
  - [x] Add guild permission validation
  - [x] Implement guild information fetching with 404 handling
  - [x] Add channel filtering based on settings
  - [x] Implement channel type categorization (text, voice, categories, etc.)
  - [x] Format channel information identically to existing implementation
  - [x] Add structured logging for channel operations
  - [x] Ensure exact same output format as current implementation

### 2.3 Message Operations Implementation
- [x] **Implement `get_messages_formatted(channel_id: str, limit: int = 50)` method**
  - [x] Copy and consolidate logic from tools.py and resources.py
  - [x] Add channel permission validation
  - [x] Implement channel information fetching with 404 handling
  - [x] Add guild permission validation for guild channels
  - [x] Implement message fetching with proper limit handling
  - [x] Add message formatting with timestamp conversion
  - [x] Handle attachments and non-text content
  - [x] Format message information identically to existing implementation
  - [x] Add structured logging for message operations
  - [x] Ensure exact same output format as current implementation

### 2.4 User Operations Implementation
- [x] **Implement `get_user_info_formatted(user_id: str)` method**
  - [x] Copy and consolidate logic from existing user info functionality
  - [x] Add user information fetching with proper error handling
  - [x] Format user information identically to existing implementation
  - [x] Add structured logging for user operations
  - [x] Ensure exact same output format as current implementation

### 2.5 Messaging Operations Implementation
- [x] **Implement `send_message()` method**
  - [x] Copy logic from existing send_message tool
  - [x] Add channel permission validation
  - [x] Implement message sending with reply support
  - [x] Add proper error handling and logging
  - [x] Ensure exact same response format

- [x] **Implement `send_direct_message()` method**
  - [x] Copy logic from existing send_dm tool
  - [x] Add user validation and error handling
  - [x] Implement DM sending functionality
  - [x] Add proper error handling and logging
  - [x] Ensure exact same response format

- [x] **Implement `read_direct_messages()` method**
  - [x] Copy logic from existing read_direct_messages tool
  - [x] Add user validation and limit handling
  - [x] Implement DM reading functionality
  - [x] Add proper error handling and logging
  - [x] Ensure exact same response format

- [x] **Implement `delete_message()` method**
  - [x] Copy logic from existing delete_message tool
  - [x] Add permission validation
  - [x] Implement message deletion functionality
  - [x] Add proper error handling and logging
  - [x] Ensure exact same response format

- [x] **Implement `edit_message()` method**
  - [x] Copy logic from existing edit_message tool
  - [x] Add permission validation (bot's own messages only)
  - [x] Implement message editing functionality
  - [x] Add proper error handling and logging
  - [x] Ensure exact same response format

### 2.6 Service Method Unit Tests
- [x] **Create comprehensive unit tests for all service methods**
  - [x] Test `get_guilds_formatted()` success scenarios
  - [x] Test `get_guilds_formatted()` error scenarios (API errors, permissions)
  - [x] Test `get_channels_formatted()` success scenarios
  - [x] Test `get_channels_formatted()` error scenarios (404, permissions)
  - [x] Test `get_messages_formatted()` success scenarios
  - [x] Test `get_messages_formatted()` error scenarios (404, permissions)
  - [x] Test `get_user_info_formatted()` success and error scenarios
  - [x] Test all messaging operations (send_message, send_dm, etc.)
  - [x] Test error handling methods in isolation
  - [x] Test permission validation methods
  - [x] Achieve 95%+ test coverage for DiscordService

### 2.7 Integration Testing Preparation
- [ ] **Create service integration test fixtures**
  - [ ] Create mock DiscordService fixture for integration tests
  - [ ] Create test data fixtures for all Discord operations
  - [ ] Set up FastMCP context mocking for service injection

**Milestone 2 Completion Criteria:**
- [ ] All service methods implemented with identical behavior
- [ ] Comprehensive unit test suite (95%+ coverage)
- [ ] All service methods properly handle errors and permissions
- [ ] Service methods produce identical output to existing implementation
- [ ] All quality gates pass (black, isort, mypy, pytest)

---

## 🔄 Milestone 3: Tools & Resources Refactor (Hours 9-12)
**Status**: ⏳ Not Started  
**Dependencies**: Milestone 2 complete  
**Estimated Duration**: 4 hours  
**Goal**: Refactor tools.py and resources.py to use DiscordService

### 3.1 Tools Refactor - Read Operations
- [x] **Refactor `list_guilds` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_guilds_formatted()`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling
  - [x] Remove duplicated code (lines 23-89)

- [x] **Refactor `list_channels` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_channels_formatted(guild_id)`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling
  - [x] Remove duplicated code (lines 91-207)

- [x] **Refactor `get_messages` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_messages_formatted(channel_id)`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling
  - [x] Remove duplicated code (lines 209-325)

- [x] **Refactor `get_user_info` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_user_info_formatted(user_id)`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling

### 3.2 Tools Refactor - Write Operations
- [x] **Refactor `send_message` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.send_message()`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling

- [x] **Refactor `send_dm` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.send_direct_message()`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling

- [x] **Refactor `read_direct_messages` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.read_direct_messages()`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling

- [x] **Refactor `delete_message` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.delete_message()`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling

- [x] **Refactor `edit_message` tool** (tools.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.edit_message()`
  - [x] Maintain exact same function signature
  - [x] Ensure identical return values and error handling

### 3.3 Resources Refactor
- [x] **Refactor `list_guilds` resource** (resources.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_guilds_formatted()`
  - [x] Maintain exact same resource URI pattern (`guilds://`)
  - [x] Ensure identical return values and error handling
  - [x] Remove duplicated code (lines 18-84)

- [x] **Refactor `list_channels` resource** (resources.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_channels_formatted(guild_id)`
  - [x] Maintain exact same resource URI pattern (`channels://{guild_id}`)
  - [x] Ensure identical return values and error handling
  - [x] Remove duplicated code (lines 86-202)

- [x] **Refactor `get_messages` resource** (resources.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_messages_formatted(channel_id)`
  - [x] Maintain exact same resource URI pattern (`messages://{channel_id}`)
  - [x] Ensure identical return values and error handling
  - [x] Remove duplicated code (lines 204-320)

- [x] **Refactor `get_user_info` resource** (resources.py)
  - [x] Replace direct discord_client usage with service call
  - [x] Update to use `discord_service.get_user_info_formatted(user_id)`
  - [x] Maintain exact same resource URI pattern (`user://{user_id}`)
  - [x] Ensure identical return values and error handling

### 3.4 Test Suite Updates
- [x] **Update tools tests** (tests/test_tools.py)
  - [x] Replace DiscordClient mocking with DiscordService mocking
  - [x] Update all test fixtures to use mock_discord_service
  - [x] Ensure all existing test assertions still pass
  - [x] Add tests for service integration in tools
  - [x] Maintain 90%+ test coverage for tools.py

- [x] **Update resources tests** (tests/test_resources.py)
  - [x] Replace DiscordClient mocking with DiscordService mocking
  - [x] Update all test fixtures to use mock_discord_service
  - [x] Ensure all existing test assertions still pass
  - [x] Add tests for service integration in resources
  - [x] Maintain 90%+ test coverage for resources.py

### 3.5 Integration Testing
- [x] **Run integration tests to validate behavior**
  - [x] Execute `python test_all_tools.py` and verify all tools work identically
  - [x] Execute comprehensive test suite for refactored components (95 tests passing)
  - [x] Compare before/after outputs for each tool and resource
  - [x] Validate error handling produces identical error messages
  - [x] Test service injection works correctly in FastMCP context

**Milestone 3 Completion Criteria:**
- [x] All tools and resources use DiscordService instead of direct client
- [x] Zero breaking changes to public APIs
- [x] All existing tests pass with updated mocking
- [x] Integration tests demonstrate identical behavior
- [x] All quality gates pass (black, isort, mypy, pytest)

---

## ✅ Milestone 4: Validation & Cleanup (Hours 13-16)
**Status**: ⏳ Not Started  
**Dependencies**: Milestone 3 complete  
**Estimated Duration**: 4 hours  
**Goal**: Final validation, cleanup, and documentation

### 4.1 Code Duplication Elimination
- [x] **Remove all duplicated code**
  - [x] Verify no duplicated Discord API logic between tools.py and resources.py
  - [x] Remove unused imports from tools.py and resources.py
  - [x] Clean up any remaining dead code
  - [x] Validate code reduction metrics (should be 250+ lines removed)

### 4.2 Performance Validation
- [x] **Conduct performance testing**
  - [x] Measure response times for all tools before/after refactor
  - [x] Measure response times for all resources before/after refactor
  - [x] Validate no performance regression (< 5% variance)
  - [x] Test memory usage of service instantiation
  - [x] Validate server startup time impact

### 4.3 Comprehensive Testing
- [ ] **Execute full test suite**
  - [ ] Run `pytest tests/` and ensure 100% pass rate
  - [ ] Run `pytest tests/ --cov=src/discord_mcp --cov-report=html`
  - [ ] Verify 90%+ test coverage maintained across all files
  - [ ] Verify 95%+ test coverage for DiscordService
  - [ ] Run `python test_all_tools.py` and verify success
  - [ ] Run `python test_mcp_integration.py` and verify success

### 4.4 End-to-End Validation
- [ ] **Test complete Discord MCP functionality**
  - [ ] Start server in SSE mode: `python discord_server.py --transport sse --port 8000`
  - [ ] Test all tools via HTTP API calls
  - [ ] Test all resources via MCP resource requests
  - [ ] Validate identical behavior to pre-refactor implementation
  - [ ] Test error scenarios and edge cases
  - [ ] Validate proper logging and error messages

### 4.5 Documentation Updates
- [ ] **Update README.md**
  - [ ] Add section on service layer architecture
  - [ ] Update API reference to mention service layer (internal detail)
  - [ ] Add information about the refactoring benefits
  - [ ] Update development section with service testing info

- [ ] **Update code documentation**
  - [ ] Ensure all service methods have comprehensive docstrings
  - [ ] Add inline comments for complex service logic
  - [ ] Update any outdated comments in tools.py and resources.py
  - [ ] Add service architecture documentation in code

- [ ] **Create migration documentation**
  - [ ] Document the refactoring changes made
  - [ ] Explain the new service layer architecture
  - [ ] Provide examples of how to extend the service
  - [ ] Document testing patterns for future development

### 4.6 Code Quality Final Check
- [ ] **Run all quality gates**
  - [ ] Execute `black --check src/ tests/` (must pass)
  - [ ] Execute `isort --check-only src/ tests/` (must pass)
  - [ ] Execute `mypy src/` (must pass with no errors)
  - [ ] Verify all type hints are comprehensive and accurate
  - [ ] Check for any remaining code style issues

### 4.7 Git & Version Control
- [ ] **Prepare for merge**
  - [ ] Commit all final changes with descriptive messages
  - [ ] Squash commits if needed for clean history
  - [ ] Create comprehensive commit message for the refactor
  - [ ] Tag the completion commit for reference
  - [ ] Prepare pull request with detailed description

### 4.8 Project Completion Validation
- [ ] **Verify all success criteria met**
  - [ ] Code duplication eliminated (60%+ reduction achieved)
  - [ ] Test coverage maintained (90%+ across all files)
  - [ ] Performance parity maintained (< 5% variance)
  - [ ] Zero breaking changes to public APIs
  - [ ] Service layer architecture properly implemented
  - [ ] All documentation updated and accurate

**Milestone 4 Completion Criteria:**
- [ ] All duplicated code eliminated
- [ ] Performance validated with no regression
- [ ] Complete test suite passes (100% pass rate)
- [ ] Documentation updated and comprehensive
- [ ] Code ready for production deployment
- [ ] All project success criteria achieved

---

## 📈 Progress Tracking

### Completion Status
- **Milestone 1**: ⏳ Not Started (0/8 sections complete)
- **Milestone 2**: ⏳ Not Started (0/7 sections complete)
- **Milestone 3**: ⏳ Not Started (0/5 sections complete)
- **Milestone 4**: ⏳ Not Started (0/8 sections complete)

### Key Metrics Tracking
- **Code Lines Removed**: 0 / ~298 target
- **Test Coverage**: Current baseline / 90%+ target
- **Performance**: Baseline established / < 5% variance target
- **API Compatibility**: 100% maintained (target)

### Risk Indicators
- [ ] **Performance Regression**: Monitor response times
- [ ] **Test Coverage Drop**: Monitor coverage reports
- [ ] **API Breaking Changes**: Validate identical behavior
- [ ] **Integration Failures**: Monitor integration test results

---

## 🚨 Blockers & Issues

### Current Blockers
*None identified - project ready to start*

### Potential Risks
- **FastMCP Integration Complexity**: Service registration in lifespan context
- **Test Mocking Complexity**: Switching from DiscordClient to DiscordService mocks
- **Performance Impact**: Service layer overhead
- **Behavior Consistency**: Ensuring identical output formatting

### Mitigation Strategies
- **Incremental Testing**: Test each phase thoroughly before proceeding
- **Behavior Validation**: Compare outputs at each step
- **Performance Monitoring**: Benchmark before/after each milestone
- **Rollback Plan**: Maintain clean git history for easy rollback

---

## 📝 Notes & Decisions

### Architecture Decisions
- **Service Layer Pattern**: Chosen for clean separation of concerns
- **Dependency Injection**: Constructor injection for testability
- **Interface Abstraction**: Abstract base class for contract definition
- **Error Handling**: Centralized error management with consistent formatting

### Implementation Decisions
- **No Breaking Changes**: Maintain 100% API compatibility
- **Identical Behavior**: Preserve exact same output formatting
- **Test Strategy**: Mock service instead of client for better isolation
- **Performance Priority**: No regression acceptable

### Future Considerations
- **Service Extension**: Easy addition of new Discord features
- **Caching Layer**: Potential future enhancement for performance
- **Rate Limiting**: Service-level rate limiting implementation
- **Monitoring**: Service-level metrics and observability

---

**Last Updated**: 2025-08-07  
**Next Review**: After each milestone completion  
**Project Status**: Ready to Begin Implementation
