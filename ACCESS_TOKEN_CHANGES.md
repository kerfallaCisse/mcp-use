# Access Token Injection Feature - Implementation Changes

This document outlines all the changes made to implement the access token injection functionality in mcp-use. This feature allows intercepting tool calls and automatically injecting access tokens before the MCP client executes tools, keeping tokens hidden from the LLM.

## Test project with access token

There is a test project in the `test-projects` folder to see how to integrate the access token.

## Overview

The access token injection feature enables:

- **Automatic token injection**: Access tokens are automatically added to tool calls
- **LLM privacy**: Tokens are never visible to the LLM in prompts or responses
- **Secure authentication**: Tools receive necessary authentication tokens for API calls
- **Flexible configuration**: Tokens can be set at initialization or dynamically per request

## Files Modified

### 1. `mcp_use/agents/mcpagent.py` - MCPAgent Class

#### Changes Made:

- **Constructor parameter**: Added `access_token: str | None = None` parameter
- **Instance variable**: Added `self.access_token` to store the token
- **Adapter initialization**: Pass access token to LangChainAdapter constructor
- **New methods**: Added `set_access_token()` and `get_access_token()` methods
- **Run method enhancement**: Added `access_token` parameter to `run()` method with logic to set token before execution

#### Key Code Changes:

```python
# Constructor modification
def __init__(
    self,
    llm: BaseLanguageModel,
    client: MCPClient | None = None,
    connectors: list[BaseConnector] | None = None,
    max_steps: int = 5,
    auto_initialize: bool = False,
    memory_enabled: bool = True,
    system_prompt: str | None = None,
    system_prompt_template: str | None = None,
    additional_instructions: str | None = None,
    disallowed_tools: list[str] | None = None,
    use_server_manager: bool = False,
    verbose: bool = False,
    access_token: str | None = None,  # NEW PARAMETER
):
    # ... existing code ...
    self.access_token = access_token  # NEW: Store access token

    # Create the adapter for tool conversion with access token
    self.adapter = LangChainAdapter(
        disallowed_tools=self.disallowed_tools,
        access_token=self.access_token  # NEW: Pass token to adapter
    )

# New access token management methods
def set_access_token(self, access_token: str | None) -> None:
    """Set or update the access token for tool calls."""
    self.access_token = access_token
    if self.adapter:
        self.adapter.access_token = access_token

def get_access_token(self) -> str | None:
    """Get the current access token."""
    return self.access_token

# Enhanced run method
async def run(
    self,
    query: str,
    max_steps: int | None = None,
    manage_connector: bool = True,
    external_history: list[BaseMessage] | None = None,
    access_token: str | None = None,  # NEW PARAMETER
) -> str:
    # NEW: Set access token if provided for this run
    if access_token is not None:
        self.set_access_token(access_token)
    # ... rest of method ...
```

### 2. `mcp_use/adapters/langchain_adapter.py` - LangChainAdapter Class

#### Changes Made:

- **Constructor parameter**: Added `access_token: str | None = None` parameter
- **Instance variable**: Added `self.access_token` to store the token
- **Token injection logic**: Modified `_convert_tool()` method's `_arun()` to inject access tokens

#### Key Code Changes:

```python
# Constructor modification
def __init__(self, disallowed_tools: list[str] | None = None, access_token: str | None = None) -> None:
    """Initialize a new LangChain adapter.

    Args:
        disallowed_tools: list of tool names that should not be available.
        access_token: optional access token to inject into tool calls.  # NEW
    """
    super().__init__(disallowed_tools)
    self._connector_tool_map: dict[BaseConnector, list[BaseTool]] = {}
    self.access_token = access_token  # NEW: Store access token

# Token injection in tool execution
async def _arun(self, **kwargs: Any) -> Any:
    """Asynchronously execute the tool with given arguments."""
    logger.debug(f'MCP tool: "{self.name}" received input: {kwargs}')

    try:
        # NEW: Inject access token if available
        if adapter_self.access_token:
            # Add access_token to the arguments if not already present
            if "access_token" not in kwargs:
                kwargs["access_token"] = adapter_self.access_token
                logger.debug(f'Injected access token for tool: "{self.name}"')

        tool_result: CallToolResult = await self.tool_connector.call_tool(
            self.name, kwargs
        )
        # ... rest of method ...
```

## New Files Created

### 3. `examples/access_token_example.py` - Basic Usage Examples

**Purpose**: Demonstrates basic access token injection usage patterns

**Key Features**:

- Example with token set at agent initialization
- Example with token set dynamically per request
- Configuration for notes MCP server
- Error handling and cleanup

**Main Functions**:

- `handle_request_with_access_token()`: Sets token at initialization
- `handle_request_with_dynamic_token()`: Sets token per request
- `main()`: Demonstrates both approaches

### 4. `examples/web_server_integration.py` - Web Server Integration

**Purpose**: Shows how to integrate access token injection in web applications

**Key Features**:

- FastAPI-style request handling
- Request body model with optional access token
- Two approaches: initialization-time vs runtime token setting
- Production-ready error handling and resource cleanup

**Main Classes/Functions**:

- `RequestBody`: Pydantic model for request structure
- `MCPWebServer`: Web server class with MCP integration
- `handle_request()`: Processes requests with token injection
- `handle_request_with_dynamic_token()`: Alternative runtime approach

### 5. `tests/unit/test_access_token.py` - Unit Tests

**Purpose**: Comprehensive test suite for access token functionality

**Test Coverage**:

- Adapter initialization with/without tokens
- MCPAgent initialization with tokens
- Token setting and getting methods
- Actual token injection during tool calls
- Behavior when no token is set
- Existing token preservation (no override)
- Runtime token setting via `run()` parameter

**Key Test Classes**:

- `TestAccessTokenInjection`: Main test class with fixtures and test methods

### 6. `docs/essentials/access-token-injection.md` - Documentation

**Purpose**: Complete user guide for the access token injection feature

**Content Sections**:

- Overview and use cases
- Basic usage examples
- Web server integration patterns
- How the feature works internally
- Security considerations and best practices
- MCP server requirements
- Troubleshooting guide
- Advanced usage patterns

## Implementation Details

### Token Injection Flow

1. **Initialization**: Access token stored in MCPAgent and passed to LangChainAdapter
2. **Tool Conversion**: LangChainAdapter converts MCP tools to LangChain tools with injection capability
3. **Execution Interception**: Before tool execution, `_arun()` method checks for available access token
4. **Conditional Injection**: Token injected only if not already present in arguments
5. **Tool Execution**: MCP tool receives enhanced arguments including access token
6. **Privacy Maintained**: LLM never sees the token in any context

### Security Features

- **No LLM Exposure**: Tokens never appear in prompts, responses, or logs visible to LLM
- **Conditional Injection**: Existing tokens in arguments are preserved (no override)
- **Debug Logging**: Token injection logged for debugging but token value excluded
- **Flexible Management**: Tokens can be set, updated, or removed at runtime

### Integration Patterns

#### Pattern 1: Initialization-Time Token

```python
agent = MCPAgent(
    llm=llm,
    client=client,
    access_token="user_token_here"  # Set once
)
```

#### Pattern 2: Runtime Token Setting

```python
agent = MCPAgent(llm=llm, client=client)  # No token initially
result = await agent.run(query, access_token="user_token_here")  # Per request
```

#### Pattern 3: Dynamic Token Management

```python
agent = MCPAgent(llm=llm, client=client)
agent.set_access_token("user_token_here")  # Update anytime
current_token = agent.get_access_token()  # Check current value
```

## Testing

All changes are covered by comprehensive unit tests that validate:

- ✅ Proper initialization with and without tokens
- ✅ Token injection during actual tool calls
- ✅ Preservation of existing tokens in arguments
- ✅ Runtime token setting and getting
- ✅ Integration between MCPAgent and LangChainAdapter
- ✅ Error handling and edge cases

## Backward Compatibility

All changes are **fully backward compatible**:

- New parameters are optional with `None` defaults
- Existing code continues to work without modification
- No breaking changes to existing APIs
- Feature is opt-in and doesn't affect existing functionality

## Usage Examples

### Basic Usage

```python
from mcp_use import MCPAgent, MCPClient
from langchain_openai import ChatOpenAI

# Create agent with access token
agent = MCPAgent(
    llm=ChatOpenAI(model="gpt-4o"),
    client=MCPClient.from_config_file("config.json"),
    access_token="your_access_token_here"
)

# Token automatically injected into tool calls
result = await agent.run("Create a note saying 'Hello World'")
```

### Web Application Integration

```python
@app.post("/query")
async def chat_endpoint(request: QueryRequest):
    agent = MCPAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        client=client,
        access_token=request.access_token  # From frontend
    )

    result = await agent.run(request.query)
    return {"result": result}
```

This implementation provides a secure, flexible, and user-friendly way to handle authenticated tool calls while maintaining the privacy and security of access tokens.
