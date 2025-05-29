"""
Tests for payload injection functionality.

This test module validates that payload data is properly injected
into tool calls before execution without being visible to the LLM.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp_use import MCPAgent
from mcp_use.adapters.langchain_adapter import LangChainAdapter
from mcp_use.connectors.base import BaseConnector
from mcp.types import CallToolResult, TextContent


class TestPayloadInjection:
    """Test payload injection functionality."""

    @pytest.fixture
    def mock_connector(self):
        """Create a mock connector for testing."""
        connector = MagicMock(spec=BaseConnector)
        connector.call_tool = AsyncMock()
        connector.tools = []
        connector.resources = []
        connector.prompts = []
        return connector

    @pytest.fixture
    def mock_tool_result(self):
        """Create a mock tool result."""
        return CallToolResult(
            content=[TextContent(
                type="text", text="Tool executed successfully")],
            isError=False
        )

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = MagicMock()
        llm.bind_tools = MagicMock(return_value=llm)
        return llm

    def test_adapter_initialization_with_payload(self):
        """Test that LangChainAdapter can be initialized with a payload."""
        payload = {"auth_token": "test_token_123", "user_id": "user123"}
        adapter = LangChainAdapter(payload=payload)

        assert adapter.payload == payload

    def test_adapter_initialization_without_payload(self):
        """Test that LangChainAdapter can be initialized without a payload."""
        adapter = LangChainAdapter()

        assert adapter.payload is None

    def test_mcpagent_initialization_with_payload(self, mock_llm):
        """Test that MCPAgent can be initialized with a payload."""
        payload = {"auth_token": "test_token_456", "session_id": "sess123"}

        with patch('mcp_use.agents.mcpagent.LangChainAdapter') as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter_class.return_value = mock_adapter

            agent = MCPAgent(
                llm=mock_llm,
                connectors=[MagicMock()],
                payload=payload
            )

            assert agent.payload == payload
            # Verify adapter was created with payload
            mock_adapter_class.assert_called_once_with(
                disallowed_tools=[],
                payload=payload
            )

    def test_set_payload(self, mock_llm):
        """Test setting payload after initialization."""
        payload = {"auth_token": "new_token_789", "user_role": "admin"}

        with patch('mcp_use.agents.mcpagent.LangChainAdapter') as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter_class.return_value = mock_adapter

            agent = MCPAgent(llm=mock_llm, connectors=[MagicMock()])
            agent.set_payload(payload)

            assert agent.payload == payload
            assert agent.adapter.payload == payload

    def test_get_payload(self, mock_llm):
        """Test getting the current payload."""
        payload = {"auth_token": "get_token_abc", "user_id": "user456"}

        with patch('mcp_use.agents.mcpagent.LangChainAdapter'):
            agent = MCPAgent(
                llm=mock_llm,
                connectors=[MagicMock()],
                payload=payload
            )

            assert agent.get_payload() == payload

    @pytest.mark.asyncio
    async def test_payload_injection_in_tool_call(self, mock_connector, mock_tool_result):
        """Test that payload data is injected into tool calls."""
        payload = {"auth_token": "injection_token_def", "user_id": "user789"}

        # Setup mock connector to return the mock result
        mock_connector.call_tool.return_value = mock_tool_result

        # Create adapter with payload
        adapter = LangChainAdapter(payload=payload)

        # Create a mock MCP tool
        mcp_tool = MagicMock()
        mcp_tool.name = "test_tool"
        mcp_tool.description = "A test tool"
        mcp_tool.inputSchema = {"type": "object", "properties": {}}

        # Convert to LangChain tool
        langchain_tool = adapter._convert_tool(mcp_tool, mock_connector)

        # Execute the tool
        result = await langchain_tool.ainvoke({"test_param": "test_value"})

        # Verify tool was called with injected payload
        mock_connector.call_tool.assert_called_once()
        call_args = mock_connector.call_tool.call_args

        # Check that payload data was injected
        arguments = call_args[1]['arguments']
        assert arguments["auth_token"] == "injection_token_def"
        assert arguments["user_id"] == "user789"
        assert arguments["test_param"] == "test_value"

    @pytest.mark.asyncio
    async def test_multiple_payload_keys_injection(self, mock_connector, mock_tool_result):
        """Test that multiple payload keys are injected correctly."""
        payload = {
            "auth_token": "multi_token_123",
            "user_id": "user456",
            "session_id": "session789",
            "role": "admin"
        }

        # Setup mock connector to return the mock result
        mock_connector.call_tool.return_value = mock_tool_result

        # Create adapter with payload
        adapter = LangChainAdapter(payload=payload)

        # Create a mock MCP tool
        mcp_tool = MagicMock()
        mcp_tool.name = "multi_test_tool"
        mcp_tool.description = "A test tool for multiple payload keys"
        mcp_tool.inputSchema = {"type": "object", "properties": {}}

        # Convert to LangChain tool
        langchain_tool = adapter._convert_tool(mcp_tool, mock_connector)

        # Execute the tool with some user arguments
        user_args = {"query": "test query", "limit": 10}
        result = await langchain_tool.ainvoke(user_args)

        # Verify tool was called with all payload keys injected
        mock_connector.call_tool.assert_called_once()
        call_args = mock_connector.call_tool.call_args
        arguments = call_args[1]['arguments']

        # Check that all payload keys were injected
        assert arguments["auth_token"] == "multi_token_123"
        assert arguments["user_id"] == "user456"
        assert arguments["session_id"] == "session789"
        assert arguments["role"] == "admin"

        # Check that user arguments are also present
        assert arguments["query"] == "test query"
        assert arguments["limit"] == 10

    @pytest.mark.asyncio
    async def test_no_payload_injection_when_none(self, mock_connector, mock_tool_result):
        """Test that no extra data is injected when payload is None."""
        # Setup mock connector to return the mock result
        mock_connector.call_tool.return_value = mock_tool_result

        # Create adapter without payload
        adapter = LangChainAdapter(payload=None)

        # Create a mock MCP tool
        mcp_tool = MagicMock()
        mcp_tool.name = "no_payload_tool"
        mcp_tool.description = "A test tool without payload"
        mcp_tool.inputSchema = {"type": "object", "properties": {}}

        # Convert to LangChain tool
        langchain_tool = adapter._convert_tool(mcp_tool, mock_connector)

        # Execute the tool with user arguments only
        user_args = {"query": "test query"}
        result = await langchain_tool.ainvoke(user_args)

        # Verify tool was called with only user arguments
        mock_connector.call_tool.assert_called_once()
        call_args = mock_connector.call_tool.call_args
        arguments = call_args[1]['arguments']

        # Check that only user arguments are present
        assert arguments == user_args
        assert "auth_token" not in arguments
        assert "user_id" not in arguments

    def test_payload_update_affects_adapter(self, mock_llm):
        """Test that updating payload on MCPAgent also updates the adapter."""
        initial_payload = {"auth_token": "initial_token"}
        updated_payload = {"auth_token": "updated_token", "user_id": "user123"}

        with patch('mcp_use.agents.mcpagent.LangChainAdapter') as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter_class.return_value = mock_adapter

            agent = MCPAgent(
                llm=mock_llm,
                connectors=[MagicMock()],
                payload=initial_payload
            )

            # Update payload
            agent.set_payload(updated_payload)

            # Verify both agent and adapter have updated payload
            assert agent.payload == updated_payload
            assert mock_adapter.payload == updated_payload
