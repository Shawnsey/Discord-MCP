# Amazon Q Rules: DiscordService Refactor Project

## 📋 Project Context & Session Management

**Always read .amazonq/Active/PLANNING.md at the start of every new conversation, check .amazonq/Active/TASKS.md before starting your work, mark completed tasks to .amazonq/Active/TASKS.md immediately, and add newly discovered tasks to .amazonq/Active/TASKS.md when found.**

### Project Overview
You are working on the **DiscordService Refactor** project for the Discord MCP server. This is a critical architecture improvement initiative to eliminate code duplication and implement proper service layer patterns.

**Key Project Facts:**
- **Objective**: Eliminate ~298 lines of duplicated code between tools.py and resources.py
- **Approach**: Implement centralized DiscordService following service layer architecture
- **Timeline**: 1-2 days, 4-phase implementation
- **Complexity**: Moderate refactoring with zero breaking changes required

---

## 🎯 Core Project Rules

### 1. Architecture Compliance
- **MUST** follow service layer architecture patterns as defined in PLANNING.md
- **MUST** implement IDiscordService interface with proper abstraction
- **MUST** use dependency injection for DiscordClient, Settings, and Logger
- **MUST** maintain single responsibility principle for all service methods

### 2. Code Quality Standards
- **MUST** achieve 60%+ reduction in duplicated code
- **MUST** maintain 90%+ test coverage across all modified files
- **MUST** ensure all methods have comprehensive type hints
- **MUST** follow existing code style (black, isort formatting)

### 3. Backward Compatibility
- **MUST** maintain 100% API compatibility for all tools and resources
- **MUST** preserve exact same method signatures and return types
- **MUST** ensure identical output formatting and error messages
- **MUST** maintain all existing functionality without behavioral changes

### 4. Testing Requirements
- **MUST** create comprehensive unit tests for DiscordService (95%+ coverage)
- **MUST** update existing tests to mock DiscordService instead of DiscordClient
- **MUST** ensure all integration tests pass without modification
- **MUST** validate performance parity with existing implementation

---

## 🏗️ Implementation Guidelines

### Phase-Based Development
Follow the 4-phase approach defined in PRD.md:

#### Phase 1: Service Foundation
- Create `src/discord_mcp/services/` package structure
- Implement `IDiscordService` interface in `interfaces.py`
- Create `DiscordService` implementation in `discord_service.py`
- Add comprehensive error handling and logging
- Write unit tests achieving 95%+ coverage
- Update `server.py` to register service in lifespan context

#### Phase 2: Tools Refactor
- Replace direct DiscordClient calls with DiscordService calls in tools.py
- Maintain exact same tool method signatures
- Update tool tests to mock DiscordService
- Validate identical behavior through integration tests

#### Phase 3: Resources Refactor
- Replace direct DiscordClient calls with DiscordService calls in resources.py
- Maintain exact same resource URI patterns and responses
- Update resource tests to mock DiscordService
- Validate identical behavior through integration tests

#### Phase 4: Validation & Cleanup
- Remove all duplicated code from tools.py and resources.py
- Update documentation and README.md
- Run comprehensive test suite validation
- Perform performance testing and validation

### Code Organization Rules

#### Service Structure
```python
# Required service interface pattern
class IDiscordService(ABC):
    @abstractmethod
    async def get_guilds_formatted(self) -> str: pass
    
    @abstractmethod
    async def get_channels_formatted(self, guild_id: str) -> str: pass
    
    @abstractmethod
    async def get_messages_formatted(self, channel_id: str, limit: int = 50) -> str: pass
```

#### Error Handling Pattern
```python
# Required centralized error handling
def _handle_discord_error(self, error: DiscordAPIError, operation: str) -> str:
    error_msg = f"Discord API error during {operation}: {str(error)}"
    self._logger.error("Discord operation failed", 
                      operation=operation, 
                      error=str(error))
    return f"# Error\n\n{error_msg}"
```

#### Integration Pattern
```python
# Required service integration in tools/resources
async def list_guilds() -> str:
    ctx = server.get_context()
    discord_service = ctx.request_context.lifespan_context["discord_service"]
    return await discord_service.get_guilds_formatted()
```

---

## 🧪 Testing Standards

### Unit Testing Rules
- **MUST** test DiscordService methods in isolation with mocked dependencies
- **MUST** test all error scenarios and edge cases
- **MUST** validate proper logging and error message formatting
- **MUST** ensure service methods handle permission validation correctly

### Integration Testing Rules
- **MUST** verify tools and resources use DiscordService correctly
- **MUST** validate identical behavior to original implementation
- **MUST** test service integration with FastMCP lifecycle
- **MUST** ensure proper context injection and service availability

### Test Organization
```python
# Required test structure
tests/
├── services/
│   ├── test_discord_service.py      # Service unit tests
│   └── test_interfaces.py           # Interface compliance tests
├── test_tools.py                    # Updated tool tests with service mocking
└── test_resources.py                # Updated resource tests with service mocking
```

---

## 📝 Documentation Requirements

### Code Documentation
- **MUST** provide comprehensive docstrings for all service methods
- **MUST** document error scenarios and return value formats
- **MUST** include type hints for all parameters and return values
- **MUST** document integration patterns for future developers

### Project Documentation
- **MUST** update README.md with service layer architecture information
- **MUST** document the refactoring changes and benefits
- **MUST** provide examples of how to extend the service for new features
- **MUST** maintain API documentation accuracy (no public API changes)

---

## 🚨 Critical Constraints

### Performance Constraints
- **MUST NOT** introduce performance regression (< 5% variance acceptable)
- **MUST NOT** increase memory usage by more than 5MB
- **MUST NOT** impact server startup time significantly

### Compatibility Constraints
- **MUST NOT** change any public API signatures
- **MUST NOT** modify existing environment variable requirements
- **MUST NOT** break existing MCP client integrations
- **MUST NOT** change existing error message formats

### Development Constraints
- **MUST** work with existing Python 3.8+ requirement
- **MUST** maintain compatibility with current FastMCP version
- **MUST** use only existing project dependencies (no new external deps)
- **MUST** follow existing project structure and conventions

---

## 🔍 Quality Gates

### Pre-Commit Checks
Before any commit, ensure:
```bash
# Code formatting
black --check src/ tests/
isort --check-only src/ tests/

# Type checking
mypy src/

# Test execution
pytest tests/ --cov=src/discord_mcp --cov-report=term-missing

# Coverage validation
# Must maintain 90%+ coverage
```

### Integration Validation
Before phase completion:
```bash
# Integration tests
python test_all_tools.py
python test_mcp_integration.py

# Behavior validation
# Compare before/after outputs for identical results
```

### Performance Validation
```python
# Required performance testing
async def validate_performance():
    # Measure response times before/after refactor
    # Ensure < 5% variance in API response times
    # Validate memory usage remains stable
```

---

## 🎯 Success Criteria

### Technical Success Metrics
- [ ] **Code Duplication**: Eliminated 60%+ of duplicated lines
- [ ] **Test Coverage**: Maintained 90%+ coverage across all files
- [ ] **Type Safety**: 100% type hints on all service methods
- [ ] **Performance**: No regression in API response times

### Quality Success Metrics
- [ ] **Architecture**: Clean service layer implementation following SOLID principles
- [ ] **Maintainability**: Single source of truth for Discord operations
- [ ] **Testability**: Easy mocking and unit testing of Discord operations
- [ ] **Documentation**: Comprehensive documentation for service usage

### Functional Success Metrics
- [ ] **API Compatibility**: All existing tools and resources work identically
- [ ] **Error Handling**: Consistent error management across all operations
- [ ] **Integration**: Seamless integration with FastMCP lifecycle
- [ ] **Extensibility**: Easy addition of new Discord features

---

## 🛠️ Development Workflow

### Session Startup Checklist
1. **Read PLANNING.md** to understand current project context
2. **Check TASKS.md** for pending work items and priorities
3. **Review recent commits** to understand current implementation state
4. **Run existing tests** to ensure clean starting point
5. **Identify current phase** and focus area for the session

### Work Session Rules
- **Focus on one phase at a time** - don't jump between phases
- **Complete tasks incrementally** - make small, testable changes
- **Update TASKS.md immediately** when completing or discovering tasks
- **Run tests frequently** to catch issues early
- **Commit often** with clear, descriptive commit messages

### Session Completion Checklist
1. **Update TASKS.md** with completed work and any new discoveries
2. **Run quality gates** (formatting, type checking, tests)
3. **Commit changes** with proper commit message format
4. **Document any blockers** or issues for next session
5. **Update progress** in relevant documentation

---

## 📋 Common Patterns & Examples

### Service Method Implementation Pattern
```python
async def get_guilds_formatted(self) -> str:
    """Get formatted list of accessible Discord guilds."""
    try:
        self._logger.info("Fetching guild list")
        
        # Get guilds from Discord API
        guilds = await self._discord_client.get_user_guilds()
        
        # Apply permission filtering
        if self._settings.get_allowed_guilds_set():
            allowed_guilds = self._settings.get_allowed_guilds_set()
            guilds = [g for g in guilds if g["id"] in allowed_guilds]
        
        # Format and return results
        return self._format_guilds(guilds)
        
    except DiscordAPIError as e:
        return self._handle_discord_error(e, "fetching guilds")
    except Exception as e:
        return self._handle_unexpected_error(e, "fetching guilds")
```

### Test Implementation Pattern
```python
async def test_get_guilds_formatted_success(self, mock_discord_client, mock_settings):
    # Setup
    service = DiscordService(mock_discord_client, mock_settings, mock_logger)
    mock_discord_client.get_user_guilds.return_value = [{"id": "123", "name": "Test"}]
    
    # Execute
    result = await service.get_guilds_formatted()
    
    # Verify
    assert "Test" in result
    mock_discord_client.get_user_guilds.assert_called_once()
```

### Integration Pattern
```python
# In tools.py or resources.py
async def list_guilds() -> str:
    ctx = server.get_context()
    discord_service: IDiscordService = ctx.request_context.lifespan_context["discord_service"]
    return await discord_service.get_guilds_formatted()
```

---

## 🚨 Error Handling & Troubleshooting

### Common Issues & Solutions

#### Service Not Found in Context
```python
# Problem: KeyError when accessing discord_service
# Solution: Ensure service is registered in server.py lifespan
async def lifespan(server: FastMCP):
    discord_service = DiscordService(discord_client, settings, logger)
    server.request_context.lifespan_context["discord_service"] = discord_service
```

#### Type Checking Failures
```python
# Problem: mypy errors on service methods
# Solution: Ensure proper type hints and interface compliance
async def get_guilds_formatted(self) -> str:  # Must return str
    # Implementation must match interface contract
```

#### Test Failures After Refactor
```python
# Problem: Tests fail after switching to service
# Solution: Update tests to mock DiscordService instead of DiscordClient
@pytest.fixture
def mock_discord_service():
    return Mock(spec=IDiscordService)
```

### Debugging Guidelines
- **Use structured logging** to trace service method calls
- **Add debug logging** for permission checks and API calls
- **Validate service injection** in FastMCP context
- **Test service methods in isolation** before integration

---

## 📚 Reference Information

### Key Files & Locations
- **PRD**: `.amazonq/Active/PRD.md` - Complete project requirements
- **Planning**: `.amazonq/Active/PLANNING.md` - Technical architecture and planning
- **Tasks**: `.amazonq/Active/TASKS.md` - Current task list and progress
- **Service Code**: `src/discord_mcp/services/` - Service implementation
- **Tests**: `tests/services/` - Service-specific tests

### Important Code Patterns
- **Service Interface**: Abstract base class with @abstractmethod decorators
- **Dependency Injection**: Constructor injection of dependencies
- **Error Handling**: Centralized error management with consistent formatting
- **Context Integration**: Service registration in FastMCP lifespan context

### Quality Standards
- **Code Coverage**: 90%+ for all modified files, 95%+ for service
- **Type Hints**: 100% coverage on all service methods
- **Performance**: No regression in API response times
- **Documentation**: Comprehensive docstrings and inline comments

---

**Rule Version**: 1.0  
**Created**: 2025-08-07  
**Project**: DiscordService Refactor  
**Status**: Active Development  

---

*These rules ensure consistent, high-quality implementation of the DiscordService refactor while maintaining system reliability and backward compatibility.*
