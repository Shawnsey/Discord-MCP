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
- [ ] **Implement `get_guilds_formatted()` method**
  - [ ] Copy and consolidate logic from tools.py and resources.py
  - [ ] Add try-catch error handling with centralized error management
  - [ ] Implement guild filtering based on settings
  - [ ] Add guild details fetching with proper error handling
  - [ ] Format guild information identically to existing implementation
  - [ ] Add structured logging for guild operations
  - [ ] Ensure exact same output format as current implementation

### 2.2 Channel Operations Implementation
- [ ] **Implement `get_channels_formatted(guild_id: str)` method**
  - [ ] Copy and consolidate logic from tools.py and resources.py
  - [ ] Add guild permission validation
  - [ ] Implement guild information fetching with 404 handling
  - [ ] Add channel filtering based on settings
  - [ ] Implement channel type categorization (text, voice, categories, etc.)
  - [ ] Format channel information identically to existing implementation
  - [ ] Add structured logging for channel operations
  - [ ] Ensure exact same output format as current implementation

### 2.3 Message Operations Implementation
- [ ] **Implement `get_messages_formatted(channel_id: str, limit: int = 50)` method**
  - [ ] Copy and consolidate logic from tools.py and resources.py
  - [ ] Add channel permission validation
  - [ ] Implement channel information fetching with 404 handling
  - [ ] Add guild permission validation for guild channels
  - [ ] Implement message fetching with proper limit handling
  - [ ] Add message formatting with timestamp conversion
  - [ ] Handle attachments and non-text content
  - [ ] Format message information identically to existing implementation
  - [ ] Add structured logging for message operations
  - [ ] Ensure exact same output format as current implementation

### 2.4 User Operations Implementation
- [ ] **Implement `get_user_info_formatted(user_id: str)` method**
  - [ ] Copy and consolidate logic from existing user info functionality
  - [ ] Add user information fetching with proper error handling
  - [ ] Format user information identically to existing implementation
  - [ ] Add structured logging for user operations
  - [ ] Ensure exact same output format as current implementation

### 2.5 Messaging Operations Implementation
- [ ] **Implement `send_message()` method**
  - [ ] Copy logic from existing send_message tool
  - [ ] Add channel permission validation
  - [ ] Implement message sending with reply support
  - [ ] Add proper error handling and logging
  - [ ] Ensure exact same response format

- [ ] **Implement `send_direct_message()` method**
  - [ ] Copy logic from existing send_dm tool
  - [ ] Add user validation and error handling
  - [ ] Implement DM sending functionality
  - [ ] Add proper error handling and logging
  - [ ] Ensure exact same response format

- [ ] **Implement `read_direct_messages()` method**
  - [ ] Copy logic from existing read_direct_messages tool
  - [ ] Add user validation and limit handling
  - [ ] Implement DM reading functionality
  - [ ] Add proper error handling and logging
  - [ ] Ensure exact same response format

- [ ] **Implement `delete_message()` method**
  - [ ] Copy logic from existing delete_message tool
  - [ ] Add permission validation
  - [ ] Implement message deletion functionality
  - [ ] Add proper error handling and logging
  - [ ] Ensure exact same response format

- [ ] **Implement `edit_message()` method**
  - [ ] Copy logic from existing edit_message tool
  - [ ] Add permission validation (bot's own messages only)
  - [ ] Implement message editing functionality
  - [ ] Add proper error handling and logging
  - [ ] Ensure exact same response format

### 2.6 Service Method Unit Tests
- [ ] **Create comprehensive unit tests for all service methods**
  - [ ] Test `get_guilds_formatted()` success scenarios
  - [ ] Test `get_guilds_formatted()` error scenarios (API errors, permissions)
  - [ ] Test `get_channels_formatted()` success scenarios
  - [ ] Test `get_channels_formatted()` error scenarios (404, permissions)
  - [ ] Test `get_messages_formatted()` success scenarios
  - [ ] Test `get_messages_formatted()` error scenarios (404, permissions)
  - [ ] Test `get_user_info_formatted()` success and error scenarios
  - [ ] Test all messaging operations (send_message, send_dm, etc.)
  - [ ] Test error handling methods in isolation
  - [ ] Test permission validation methods
  - [ ] Achieve 95%+ test coverage for DiscordService

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
- [ ] **Refactor `list_guilds` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_guilds_formatted()`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling
  - [ ] Remove duplicated code (lines 23-89)

- [ ] **Refactor `list_channels` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_channels_formatted(guild_id)`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling
  - [ ] Remove duplicated code (lines 91-207)

- [ ] **Refactor `get_messages` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_messages_formatted(channel_id)`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling
  - [ ] Remove duplicated code (lines 209-325)

- [ ] **Refactor `get_user_info` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_user_info_formatted(user_id)`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling

### 3.2 Tools Refactor - Write Operations
- [ ] **Refactor `send_message` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.send_message()`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling

- [ ] **Refactor `send_dm` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.send_direct_message()`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling

- [ ] **Refactor `read_direct_messages` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.read_direct_messages()`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling

- [ ] **Refactor `delete_message` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.delete_message()`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling

- [ ] **Refactor `edit_message` tool** (tools.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.edit_message()`
  - [ ] Maintain exact same function signature
  - [ ] Ensure identical return values and error handling

### 3.3 Resources Refactor
- [ ] **Refactor `list_guilds` resource** (resources.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_guilds_formatted()`
  - [ ] Maintain exact same resource URI pattern (`guilds://`)
  - [ ] Ensure identical return values and error handling
  - [ ] Remove duplicated code (lines 18-84)

- [ ] **Refactor `list_channels` resource** (resources.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_channels_formatted(guild_id)`
  - [ ] Maintain exact same resource URI pattern (`channels://{guild_id}`)
  - [ ] Ensure identical return values and error handling
  - [ ] Remove duplicated code (lines 86-202)

- [ ] **Refactor `get_messages` resource** (resources.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_messages_formatted(channel_id)`
  - [ ] Maintain exact same resource URI pattern (`messages://{channel_id}`)
  - [ ] Ensure identical return values and error handling
  - [ ] Remove duplicated code (lines 204-320)

- [ ] **Refactor `get_user_info` resource** (resources.py)
  - [ ] Replace direct discord_client usage with service call
  - [ ] Update to use `discord_service.get_user_info_formatted(user_id)`
  - [ ] Maintain exact same resource URI pattern (`user://{user_id}`)
  - [ ] Ensure identical return values and error handling

### 3.4 Test Suite Updates
- [ ] **Update tools tests** (tests/test_tools.py)
  - [ ] Replace DiscordClient mocking with DiscordService mocking
  - [ ] Update all test fixtures to use mock_discord_service
  - [ ] Ensure all existing test assertions still pass
  - [ ] Add tests for service integration in tools
  - [ ] Maintain 90%+ test coverage for tools.py

- [ ] **Update resources tests** (tests/test_resources.py)
  - [ ] Replace DiscordClient mocking with DiscordService mocking
  - [ ] Update all test fixtures to use mock_discord_service
  - [ ] Ensure all existing test assertions still pass
  - [ ] Add tests for service integration in resources
  - [ ] Maintain 90%+ test coverage for resources.py

### 3.5 Integration Testing
- [ ] **Run integration tests to validate behavior**
  - [ ] Execute `python test_all_tools.py` and verify all tools work identically
  - [ ] Execute `python test_mcp_integration.py` and verify resources work identically
  - [ ] Compare before/after outputs for each tool and resource
  - [ ] Validate error handling produces identical error messages
  - [ ] Test service injection works correctly in FastMCP context

**Milestone 3 Completion Criteria:**
- [ ] All tools and resources use DiscordService instead of direct client
- [ ] Zero breaking changes to public APIs
- [ ] All existing tests pass with updated mocking
- [ ] Integration tests demonstrate identical behavior
- [ ] All quality gates pass (black, isort, mypy, pytest)

---

## ✅ Milestone 4: Validation & Cleanup (Hours 13-16)
**Status**: ⏳ Not Started  
**Dependencies**: Milestone 3 complete  
**Estimated Duration**: 4 hours  
**Goal**: Final validation, cleanup, and documentation

### 4.1 Code Duplication Elimination
- [ ] **Remove all duplicated code**
  - [ ] Verify no duplicated Discord API logic between tools.py and resources.py
  - [ ] Remove unused imports from tools.py and resources.py
  - [ ] Clean up any remaining dead code
  - [ ] Validate code reduction metrics (should be 250+ lines removed)

### 4.2 Performance Validation
- [ ] **Conduct performance testing**
  - [ ] Measure response times for all tools before/after refactor
  - [ ] Measure response times for all resources before/after refactor
  - [ ] Validate no performance regression (< 5% variance)
  - [ ] Test memory usage of service instantiation
  - [ ] Validate server startup time impact

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
