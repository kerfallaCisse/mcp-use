"""
Payload Injection Example for mcp_use.

This example demonstrates how to intercept tool calls and inject payload data
before the mcp client executes the tool. The payload will be automatically
added to tool arguments when provided, keeping it hidden from the LLM.

The frontend can send a request like:
{
    "query": "Inscrit la note 'AmenityDev est la meilleure entreprise au monde' dans mes notes",
    "payload": {
        "auth_token": "sdawdoiqweduq2323092093e2deukdjwekdjwe",
        "user_id": "user123",
        "session_id": "sess456"
    }
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


async def handle_request_with_payload(request_body: dict):
    """Handle a request from the frontend that includes payload data.

    Args:
        request_body: The request body from the frontend containing query and payload data
    """
    # Load environment variables
    load_dotenv()

    # Extract query and payload from request
    query = request_body.get("query", "")
    payload = request_body.get("payload")

    print(f"Received query: {query}")
    if payload:
        # Don't log sensitive data for security
        print(
            f"Payload provided with {len(payload)} keys: {list(payload.keys())}")
    else:
        print("No payload provided")

    # Create MCPClient from configuration
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Create agent - payload can be set at initialization
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10,
        payload=payload  # The payload will be injected into tool calls
    )

    try:
        # Initialize the agent
        await agent.initialize()

        # Run the query - the payload will be automatically injected into any tool calls
        # The LLM will not see the payload data in the prompts or responses
        result = await agent.run(query)

        print(f"Result: {result}")
        return result

    finally:
        # Clean up
        await client.close_all_sessions()


async def handle_request_with_dynamic_payload(request_body: dict):
    """Alternative approach: set payload dynamically per request.

    This approach is useful when you want to reuse the same agent instance
    but change the payload for different requests.
    """
    # Load environment variables
    load_dotenv()

    # Extract query and payload from request
    query = request_body.get("query", "")
    payload = request_body.get("payload")

    print(f"Received query: {query}")

    # Create MCPClient from configuration
    client = MCPClient.from_dict(config)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o")

    # Create agent without payload initially
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10
    )

    try:
        # Initialize the agent
        await agent.initialize()

        # Run the query with payload provided as parameter
        # This will temporarily set the payload for this specific run
        result = await agent.run(query, payload=payload)

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
        "payload": {
            "auth_token": "sdawdoiqweduq2323092093e2deukdjwekdjwe",
            "user_id": "user123",
            "session_id": "sess456"
        }
    }

    print("=== Approach 1: Set payload at agent initialization ===")
    await handle_request_with_payload(example_request)

    print("\n=== Approach 2: Set payload dynamically per request ===")
    await handle_request_with_dynamic_payload(example_request)

    # Example without payload
    example_request_no_payload = {
        "query": "List available tools",
        "payload": None
    }

    print("\n=== Example without payload ===")
    await handle_request_with_dynamic_payload(example_request_no_payload)


if __name__ == "__main__":
    asyncio.run(main())
