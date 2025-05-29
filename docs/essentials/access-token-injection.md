# Access Token Injection

This document explains how to use the access token injection feature in mcp-use, which allows you to securely inject access tokens into tool calls without exposing them to the LLM.

## Overview

The access token injection feature enables you to:

- **Intercept tool calls**: Automatically inject access tokens before tools are executed
- **Keep tokens hidden**: Access tokens are never visible to the LLM in prompts or responses
- **Secure authentication**: Tools receive the necessary authentication tokens for API calls
- **Flexible configuration**: Set tokens at initialization or dynamically per request

## Use Cases

This feature is particularly useful for:

- **Web applications**: Frontend sends access tokens with queries for authenticated API calls
- **Multi-tenant systems**: Different users have different access tokens for the same tools
- **API integrations**: Tools need authentication tokens to access external services
- **Security compliance**: Keeping sensitive tokens out of LLM context and logs

## Basic Usage

### Setting Access Token at Initialization

```python
import asyncio
from mcp_use import MCPAgent, MCPClient
from langchain_openai import ChatOpenAI

async def main():
    # Load your MCP configuration
    client = MCPClient.from_config_file("config.json")

    # Create agent with access token
    agent = MCPAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        client=client,
        access_token="your_access_token_here"  # Token will be injected into all tool calls
    )

    # Initialize and run
    await agent.initialize()
    result = await agent.run("Create a note saying 'Hello World'")

    # Clean up
    await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

### Setting Access Token Dynamically

```python
async def handle_request(query: str, access_token: str = None):
    client = MCPClient.from_config_file("config.json")

    # Create agent without token initially
    agent = MCPAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        client=client
    )

    await agent.initialize()

    # Run with token provided as parameter
    result = await agent.run(query, access_token=access_token)

    await client.close_all_sessions()
    return result
```

### Updating Access Token

```python
# Update token after agent creation
agent.set_access_token("new_access_token")

# Get current token
current_token = agent.get_access_token()

# Remove token
agent.set_access_token(None)
```

## Web Server Integration

Here's how to integrate access token injection in a web application:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp_use import MCPAgent, MCPClient

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    access_token: str = None

@app.post("/chat")
async def chat_endpoint(request: QueryRequest):
    """Handle chat requests with optional access token."""

    try:
        # Create MCP client
        client = MCPClient.from_config_file("config.json")

        # Create agent with access token injection
        agent = MCPAgent(
            llm=ChatOpenAI(model="gpt-4o"),
            client=client,
            access_token=request.access_token  # Token automatically injected into tool calls
        )

        await agent.initialize()
        result = await agent.run(request.query)

        await client.close_all_sessions()

        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend Integration

```javascript
// Frontend code (JavaScript/TypeScript)
async function sendQuery(query, accessToken) {
  const response = await fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: query,
      access_token: accessToken, // Token sent securely to backend
    }),
  });

  return await response.json();
}

// Usage
const result = await sendQuery(
  "Create a note with important information",
  "user_access_token_here"
);
```

## How It Works

1. **Token Storage**: Access tokens are stored in the MCPAgent and LangChainAdapter
2. **Interception**: Before each tool call, the adapter checks if an access token is available
3. **Injection**: If a token exists and isn't already in the arguments, it's automatically added as `access_token`
4. **Execution**: The tool receives the token and can use it for authentication
5. **Privacy**: The LLM never sees the token in prompts, responses, or logs

## Security Considerations

### Best Practices

- **Environment Variables**: Store tokens in environment variables, not in code
- **HTTPS Only**: Always use HTTPS when transmitting tokens
- **Token Rotation**: Implement token rotation and expiration
- **Logging**: Avoid logging access tokens (the library automatically excludes them from debug logs)

### Example with Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()

async def secure_agent_creation():
    # Get token from environment
    access_token = os.getenv("USER_ACCESS_TOKEN")

    agent = MCPAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        client=client,
        access_token=access_token
    )

    return agent
```

## MCP Server Requirements

For this feature to work, your MCP server tools should accept an `access_token` parameter:

```python
# Example MCP server tool
@tool
def create_note(content: str, access_token: str = None):
    """Create a note with the given content.

    Args:
        content: The note content
        access_token: Authentication token for the service
    """
    if access_token:
        # Use token for authenticated API call
        headers = {"Authorization": f"Bearer {access_token}"}
        # Make authenticated request...
    else:
        # Handle unauthenticated case
        pass
```

## Configuration Examples

### Single Server with Authentication

```json
{
  "mcpServers": {
    "notes_api": {
      "command": "npx",
      "args": ["@my-company/notes-mcp-server"],
      "env": {
        "API_BASE_URL": "https://api.mycompany.com"
      }
    }
  }
}
```

### Multiple Servers with Shared Authentication

```json
{
  "mcpServers": {
    "notes": {
      "command": "npx",
      "args": ["@my-company/notes-mcp-server"]
    },
    "calendar": {
      "command": "npx",
      "args": ["@my-company/calendar-mcp-server"]
    },
    "tasks": {
      "command": "npx",
      "args": ["@my-company/tasks-mcp-server"]
    }
  }
}
```

## Troubleshooting

### Token Not Being Injected

1. **Check Initialization**: Ensure the token is set before calling `agent.run()`
2. **Verify Tool Schema**: Confirm your MCP tools accept an `access_token` parameter
3. **Debug Logging**: Enable debug logging to see token injection messages

```python
import logging
from mcp_use import set_debug

# Enable debug logging
set_debug(True)
logging.getLogger("mcp_use").setLevel(logging.DEBUG)
```

### Token Conflicts

If a tool call already has an `access_token` parameter, the existing value takes precedence:

```python
# This token will NOT be overridden
tool_args = {"content": "Hello", "access_token": "existing_token"}
# The existing_token will be used, not the agent's access_token
```

## Advanced Usage

### Custom Token Parameter Name

If your tools use a different parameter name for tokens, you can modify the injection logic:

```python
# Extend the LangChainAdapter for custom token parameter names
class CustomTokenAdapter(LangChainAdapter):
    def __init__(self, token_param_name="api_key", **kwargs):
        super().__init__(**kwargs)
        self.token_param_name = token_param_name

    # Override _convert_tool method to use custom parameter name
    # (implementation details depend on your specific requirements)
```

### Conditional Token Injection

```python
# Only inject token for specific tools
class ConditionalTokenAdapter(LangChainAdapter):
    def __init__(self, token_tools=None, **kwargs):
        super().__init__(**kwargs)
        self.token_tools = token_tools or []

    # Modify injection logic to only apply to specific tools
```

## Examples

For complete working examples, see:

- [`examples/access_token_example.py`](../examples/access_token_example.py) - Basic usage examples
- [`examples/web_server_integration.py`](../examples/web_server_integration.py) - Web server integration
- [`tests/unit/test_access_token.py`](../tests/unit/test_access_token.py) - Unit tests and validation
