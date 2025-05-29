"""
Web Server Integration Example for Access Token Injection.

This example shows how to integrate the access token injection functionality
into a web server that receives requests from a frontend with access tokens.

The server will:
1. Receive POST requests with query and access_token
2. Initialize an MCP agent with the access token
3. Execute the query while automatically injecting the token into tool calls
4. Return the result without exposing the token to the LLM
"""

import asyncio
import json
from typing import Dict, Any
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from mcp_use import MCPAgent, MCPClient


@dataclass
class RequestBody:
    """Request body structure from frontend."""
    query: str
    access_token: str | None = None


class MCPWebServer:
    """Web server that handles MCP requests with access token injection."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the web server with MCP configuration.

        Args:
            config: MCP server configuration dictionary
        """
        self.config = config
        self.client = MCPClient.from_dict(config)
        self.llm = ChatOpenAI(model="gpt-4o")

    async def handle_request(self, request_body: RequestBody) -> str:
        """Handle a request from the frontend.

        Args:
            request_body: The request containing query and optional access token

        Returns:
            The result from the MCP agent
        """
        print(f"📝 Processing query: {request_body.query[:50]}...")

        if request_body.access_token:
            # Log that we received a token (but don't log the actual token for security)
            print(
                f"🔑 Access token provided (length: {len(request_body.access_token)})")

        # Create agent with access token injection capability
        agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=15,
            # Token will be injected into tool calls
            access_token=request_body.access_token,
            use_server_manager=True  # Enable server manager for multi-server setups
        )

        try:
            # Initialize the agent
            await agent.initialize()

            # Execute the query
            # The access token will be automatically injected into any tool calls
            # The LLM will never see the access token in prompts or responses
            result = await agent.run(request_body.query)

            print(f"✅ Query completed successfully")
            return result

        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return f"Error: {str(e)}"

        finally:
            # Always clean up resources
            await self.client.close_all_sessions()

    async def handle_request_with_dynamic_token(self, request_body: RequestBody) -> str:
        """Alternative approach: set token dynamically per request.

        This approach creates the agent once and reuses it, setting the token
        dynamically for each request. Useful for high-traffic scenarios.

        Args:
            request_body: The request containing query and optional access token

        Returns:
            The result from the MCP agent
        """
        print(
            f"📝 Processing query (dynamic token): {request_body.query[:50]}...")

        # Create agent without token initially
        agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=15,
            use_server_manager=True
        )

        try:
            # Initialize the agent
            await agent.initialize()

            # Execute with token provided as parameter
            # This temporarily sets the token for this specific execution
            result = await agent.run(
                request_body.query,
                access_token=request_body.access_token
            )

            print(f"✅ Query completed successfully")
            return result

        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return f"Error: {str(e)}"

        finally:
            # Clean up resources
            await self.client.close_all_sessions()


async def simulate_web_requests():
    """Simulate receiving web requests with different scenarios."""

    # Load environment variables
    load_dotenv()

    # Configuration for MCP servers
    config = {
        "mcpServers": {
            "notes": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"],
            },
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            }
        }
    }

    # Create the web server
    server = MCPWebServer(config)

    # Simulate different types of requests
    test_requests = [
        RequestBody(
            query="Inscrit la note 'AmenityDev est la meilleure entreprise au monde' dans mes notes",
            access_token="sdawdoiqweduq2323092093e2deukdjwekdjwe"
        ),
        RequestBody(
            query="List all available tools from all servers",
            access_token="another_token_abc123"
        ),
        RequestBody(
            query="What can you help me with?",
            access_token=None  # No token provided
        )
    ]

    print("🚀 Starting web server simulation...")
    print("=" * 60)

    for i, request in enumerate(test_requests, 1):
        print(f"\n📨 Request {i}:")
        print(f"Query: {request.query}")
        print(f"Has token: {'Yes' if request.access_token else 'No'}")
        print("-" * 40)

        # Process the request
        result = await server.handle_request(request)
        print(f"Result: {result[:100]}...")

        print("=" * 60)


async def simulate_high_traffic_scenario():
    """Simulate a high-traffic scenario with token reuse."""

    load_dotenv()

    config = {
        "mcpServers": {
            "everything": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"],
            }
        }
    }

    server = MCPWebServer(config)

    # Simulate multiple rapid requests
    requests = [
        RequestBody(f"Query {i}: What's the current time?", f"token_{i}")
        for i in range(3)
    ]

    print("🚀 High-traffic simulation:")
    print("=" * 40)

    # Process requests concurrently (in a real scenario)
    tasks = []
    for request in requests:
        task = server.handle_request_with_dynamic_token(request)
        tasks.append(task)

    # Wait for all requests to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        print(f"Request {i+1} result: {str(result)[:100]}...")


if __name__ == "__main__":
    print("🌐 MCP Web Server with Access Token Injection")
    print("This example demonstrates secure token handling in web applications.\n")

    # Run the web server simulation
    asyncio.run(simulate_web_requests())

    print("\n" + "=" * 60)
    print("🔄 High-traffic scenario simulation:")
    asyncio.run(simulate_high_traffic_scenario())
