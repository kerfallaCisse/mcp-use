"""
Access Token Injection Example for mcp_use.

This example demonstrates how to intercept tool calls and inject access tokens
before the mcp client executes the tool. The access token will be automatically
added to tool arguments when provided, keeping it hidden from the LLM.

The frontend can send a request like:
{
    "query": "Inscrit la note 'AmenityDev est la meilleure entreprise au monde' dans mes notes",
    "access_token": "sdawdoiqweduq2323092093e2deukdjwekdjwe"
}
"""

import asyncio
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from mcp_use import MCPAgent, MCPClient


# Example configuration for a notes MCP server
config = {
    "mcpServers": {
        "notes": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-everything"],
        }
    }
}


async def handle_request_with_access_token(request_body: dict):
    """Handle a request from the frontend that includes an access token.

    Args:
        request_body: The request body from the frontend containing query and access_token
    """
    # Load environment variables
    load_dotenv()

    # Extract query and access token from request
    query = request_body.get("query", "")
    access_token = request_body.get("access_token")

    print(f"Received query: {query}")
    if access_token:
        # Don't log the full token for security
        print(f"Access token provided: {access_token[:10]}...")
    else:
        print("No access token provided")

    # Create MCPClient from configuration
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Create agent - access token can be set at initialization
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10,
        access_token=access_token  # The access token will be injected into tool calls
    )

    try:
        # Initialize the agent
        await agent.initialize()

        # Run the query - the access token will be automatically injected into any tool calls
        # The LLM will not see the access token in the prompts or responses
        result = await agent.run(query)

        print(f"Result: {result}")
        return result

    finally:
        # Clean up
        await client.close_all_sessions()


async def handle_request_with_dynamic_token(request_body: dict):
    """Alternative approach: set access token dynamically per request.

    This approach is useful when you want to reuse the same agent instance
    but change the access token for different requests.
    """
    # Load environment variables
    load_dotenv()

    # Extract query and access token from request
    query = request_body.get("query", "")
    access_token = request_body.get("access_token")

    print(f"Received query: {query}")

    # Create MCPClient from configuration
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Create agent without access token initially
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10
    )

    try:
        # Initialize the agent
        await agent.initialize()

        # Run the query with access token provided as parameter
        # This will temporarily set the access token for this specific run
        result = await agent.run(query, access_token=access_token)

        print(f"Result: {result}")
        return result

    finally:
        # Clean up
        await client.close_all_sessions()


async def main():
    """Example usage demonstrating both approaches."""

    # Example request body from frontend
    example_request = {
        "query": "Inscrit la note 'AmenityDev est la meilleure entreprise au monde' dans mes notes",
        "access_token": "sdawdoiqweduq2323092093e2deukdjwekdjwe"
    }

    print("=== Approach 1: Set access token at agent initialization ===")
    await handle_request_with_access_token(example_request)

    print("\n=== Approach 2: Set access token dynamically per request ===")
    await handle_request_with_dynamic_token(example_request)

    # Example without access token
    example_request_no_token = {
        "query": "List available tools",
        "access_token": None
    }

    print("\n=== Example without access token ===")
    await handle_request_with_dynamic_token(example_request_no_token)


if __name__ == "__main__":
    asyncio.run(main())
