"""
Tests for access token injection functionality.

This test module validates that access tokens are properly injected
into tool calls before execution without being visible to the LLM.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp_use import MCPAgent
from mcp_use.adapters.langchain_adapter import LangChainAdapter
from mcp_use.connectors.base import BaseConnector
from mcp.types import CallToolResult, TextContent


class TestAccessTokenInjection:
    """Test access token injection functionality."""

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

    def test_adapter_initialization_with_access_token(self):
        """Test that LangChainAdapter can be initialized with an access token."""
        access_token = "test_token_123"
        adapter = LangChainAdapter(access_token=access_token)

        assert adapter.access_token == access_token

    def test_adapter_initialization_without_access_token(self):
        """Test that LangChainAdapter can be initialized without an access token."""
        adapter = LangChainAdapter()

        assert adapter.access_token is None

    def test_mcpagent_initialization_with_access_token(self, mock_llm):
        """Test that MCPAgent can be initialized with an access token."""
        access_token = "test_token_456"

        with patch('mcp_use.agents.mcpagent.LangChainAdapter') as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter_class.return_value = mock_adapter

            agent = MCPAgent(
                llm=mock_llm,
                connectors=[MagicMock()],
                access_token=access_token
            )

            assert agent.access_token == access_token
            # Verify adapter was created with access token
            mock_adapter_class.assert_called_once_with(
                disallowed_tools=[],
                access_token=access_token
            )

    def test_set_access_token(self, mock_llm):
        """Test setting access token after initialization."""
        access_token = "new_token_789"

        with patch('mcp_use.agents.mcpagent.LangChainAdapter') as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter_class.return_value = mock_adapter

            agent = MCPAgent(llm=mock_llm, connectors=[MagicMock()])
            agent.set_access_token(access_token)

            assert agent.access_token == access_token
            assert agent.adapter.access_token == access_token

    def test_get_access_token(self, mock_llm):
        """Test getting the current access token."""
        access_token = "get_token_abc"

        with patch('mcp_use.agents.mcpagent.LangChainAdapter'):
            agent = MCPAgent(
                llm=mock_llm,
                connectors=[MagicMock()],
                access_token=access_token
            )

            assert agent.get_access_token() == access_token

    @pytest.mark.asyncio
    async def test_access_token_injection_in_tool_call(self, mock_connector, mock_tool_result):
        """Test that access token is injected into tool calls."""
        access_token = "injection_token_def"

        # Setup mock connector to return the mock result
        mock_connector.call_tool.return_value = mock_tool_result

        # Create adapter with access token
        adapter = LangChainAdapter(access_token=access_token)

        # Create a mock MCP tool
        mcp_tool = MagicMock()
        mcp_tool.name = "test_tool"
        mcp_tool.description = "A test tool"
        mcp_tool.inputSchema = {"type": "object", "properties": {}}

        # Convert to LangChain tool
        langchain_tool = adapter._convert_tool(mcp_tool, mock_connector)

        # Execute the tool with some arguments
        test_args = {"param1": "value1", "param2": "value2"}
        result = await langchain_tool._arun(**test_args)

        # Verify the tool was called with access token injected
        expected_args = test_args.copy()
        expected_args["access_token"] = access_token

        mock_connector.call_tool.assert_called_once_with(
            "test_tool", expected_args)
        assert result == "Tool executed successfully"

    @pytest.mark.asyncio
    async def test_no_token_injection_when_not_set(self, mock_connector, mock_tool_result):
        """Test that no access token is injected when not set."""
        # Setup mock connector to return the mock result
        mock_connector.call_tool.return_value = mock_tool_result

        # Create adapter without access token
        adapter = LangChainAdapter()

        # Create a mock MCP tool
        mcp_tool = MagicMock()
        mcp_tool.name = "test_tool"
        mcp_tool.description = "A test tool"
        mcp_tool.inputSchema = {"type": "object", "properties": {}}

        # Convert to LangChain tool
        langchain_tool = adapter._convert_tool(mcp_tool, mock_connector)

        # Execute the tool with some arguments
        test_args = {"param1": "value1", "param2": "value2"}
        result = await langchain_tool._arun(**test_args)

        # Verify the tool was called without access token
        mock_connector.call_tool.assert_called_once_with(
            "test_tool", test_args)
        assert result == "Tool executed successfully"

    @pytest.mark.asyncio
    async def test_existing_access_token_not_overridden(self, mock_connector, mock_tool_result):
        """Test that existing access_token in arguments is not overridden."""
        adapter_token = "adapter_token"
        existing_token = "existing_token"

        # Setup mock connector to return the mock result
        mock_connector.call_tool.return_value = mock_tool_result

        # Create adapter with access token
        adapter = LangChainAdapter(access_token=adapter_token)

        # Create a mock MCP tool
        mcp_tool = MagicMock()
        mcp_tool.name = "test_tool"
        mcp_tool.description = "A test tool"
        mcp_tool.inputSchema = {"type": "object", "properties": {}}

        # Convert to LangChain tool
        langchain_tool = adapter._convert_tool(mcp_tool, mock_connector)

        # Execute the tool with arguments that already include access_token
        test_args = {"param1": "value1", "access_token": existing_token}
        result = await langchain_tool._arun(**test_args)

        # Verify the existing access token was preserved
        mock_connector.call_tool.assert_called_once_with(
            "test_tool", test_args)
        assert result == "Tool executed successfully"

    @pytest.mark.asyncio
    async def test_run_with_access_token_parameter(self, mock_llm):
        """Test running agent with access token as parameter."""
        run_token = "run_token_ghi"

        with patch('mcp_use.agents.mcpagent.LangChainAdapter') as mock_adapter_class:
            mock_adapter = MagicMock()
            mock_adapter_class.return_value = mock_adapter

            # Mock the agent initialization and execution
            with patch.object(MCPAgent, 'initialize') as mock_init, \
                    patch.object(MCPAgent, '_create_agent') as mock_create_agent, \
                    patch.object(MCPAgent, '_create_system_message_from_tools') as mock_create_system:

                mock_agent_executor = MagicMock()
                mock_agent_executor._atake_next_step = AsyncMock()
                mock_create_agent.return_value = mock_agent_executor

                agent = MCPAgent(llm=mock_llm, connectors=[MagicMock()])
                agent._tools = []
                agent._initialized = True
                agent._agent_executor = mock_agent_executor

                # Mock the agent execution to return immediately
                from langchain_core.agents import AgentFinish
                mock_agent_executor._atake_next_step.return_value = AgentFinish(
                    return_values={"output": "Test completed"}, log=""
                )

                # Run with access token
                result = await agent.run("test query", access_token=run_token)

                # Verify access token was set
                assert agent.access_token == run_token
                assert agent.adapter.access_token == run_token
