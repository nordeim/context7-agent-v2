"""
Comprehensive tests for the Context7Agent class.
Tests MCP integration, chat functionality, and error handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.agent import Context7Agent
from src.config import Config


@pytest.fixture
def temp_config():
    """Create a temporary config for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('[]')
        temp_path = f.name
    
    config = Config(
        openai_api_key="test-key-123",
        openai_base_url="https://test-api.com/v1",
        openai_model="gpt-4o-mini-test",
        history_file=temp_path
    )
    yield config
    os.unlink(temp_path)


@pytest.fixture
async def agent(temp_config):
    """Create an agent instance for testing."""
    agent = Context7Agent(temp_config)
    await agent.initialize()
    return agent


@pytest.mark.asyncio
class TestAgentInitialization:
    """Test agent initialization and setup."""
    
    async def test_agent_creation(self, agent):
        """Test agent can be created successfully."""
        assert agent.config.openai_api_key == "test-key-123"
        assert agent.config.openai_model == "gpt-4o-mini-test"
        assert agent.agent is not None
    
    async def test_agent_initialization(self, agent):
        """Test agent initialization loads history."""
        assert agent.history is not None
        assert isinstance(agent.history.history, list)


@pytest.mark.asyncio
class TestChatFunctionality:
    """Test chat and streaming functionality."""
    
    @patch('src.agent.MCPServerStdio')
    async def test_chat_basic(self, mock_mcp, agent):
        """Test basic chat functionality."""
        mock_result = MagicMock()
        mock_result.data = "Test response"
        
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        with patch.object(agent.agent, 'run_mcp_servers', return_value=AsyncMock()):
            with patch.object(agent.agent, 'run', AsyncMock(return_value=mock_result)):
                response = await agent.chat("Hello world")
                assert response == "Test response"
    
    @patch('src.agent.MCPServerStdio')
    async def test_chat_with_history(self, mock_mcp, agent):
        """Test chat with message history."""
        mock_result = MagicMock()
        mock_result.data = "Response with history"
        
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        with patch.object(agent.agent, 'run_mcp_servers', return_value=AsyncMock()):
            with patch.object(agent.agent, 'run', AsyncMock(return_value=mock_result)):
                response = await agent.chat("New question", history)
                assert response == "Response with history"
    
    @patch('src.agent.MCPServerStdio')
    async def test_chat_stream(self, mock_mcp, agent):
        """Test streaming chat functionality."""
        async def mock_stream(*args, **kwargs):
            yield MagicMock(text_deltas=lambda: ["Hello", " ", "world"])
        
        with patch.object(agent.agent, 'run_mcp_servers', return_value=AsyncMock()):
            with patch.object(agent.agent, 'run_stream', mock_stream):
                chunks = []
                async for chunk in agent.chat_stream("Test"):
                    chunks.append(chunk)
                assert len(chunks) > 0


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    async def test_chat_with_empty_input(self, agent):
        """Test chat with empty input."""
        with patch.object(agent.agent, 'run_mcp_servers', return_value=AsyncMock()):
            with patch.object(agent.agent, 'run', AsyncMock(return_value=MagicMock(data=""))):
                response = await agent.chat("")
                assert response == ""
    
    async def test_chat_with_none_history(self, agent):
        """Test chat with None history."""
        with patch.object(agent.agent, 'run_mcp_servers', return_value=AsyncMock()):
            with patch.object(agent.agent, 'run', AsyncMock(return_value=MagicMock(data="response"))):
                response = await agent.chat("test", None)
                assert response == "response"
    
    @patch('src.agent.MCPServerStdio')
    async def test_mcp_server_failure(self, mock_mcp, agent):
        """Test graceful handling of MCP server failures."""
        mock_mcp.side_effect = Exception("MCP server error")
        
        with pytest.raises(Exception) as exc_info:
            await agent.chat("test")
        assert "MCP server error" in str(exc_info.value)


@pytest.mark.asyncio
class TestHistoryIntegration:
    """Test integration with history manager."""
    
    async def test_history_persistence(self, agent):
        """Test history is properly managed."""
        initial_history = agent.get_history()
        assert isinstance(initial_history, list)
        
        # Add some history
        agent.history.append({"role": "user", "content": "test"})
        
        # Save and reload
        await agent.save_history()
        await agent.history.load_async()
        
        new_history = agent.get_history()
        assert len(new_history) >= 1
        assert new_history[-1]["content"] == "test"


@pytest.mark.asyncio
class TestMCPIntegration:
    """Test MCP server integration patterns."""
    
    async def test_mcp_lifecycle(self, agent):
        """Test MCP server lifecycle management."""
        with patch('src.agent.MCPServerStdio') as mock_mcp:
            mock_server = AsyncMock()
            mock_mcp.return_value = mock_server
            
            with patch.object(agent.agent, 'run_mcp_servers') as mock_context:
                mock_context.return_value.__aenter__ = AsyncMock()
                mock_context.return_value.__aexit__ = AsyncMock()
                
                await agent.chat("test")
                
                # Verify MCP server was created
                mock_mcp.assert_called_once_with(
                    command="npx",
                    args=["-y", "@upstash/context7-mcp@latest"]
                )
    
    async def test_multiple_chat_calls(self, agent):
        """Test multiple chat calls create separate MCP instances."""
        call_count = 0
        
        def mock_mcp_factory():
            nonlocal call_count
            call_count += 1
            return AsyncMock()
        
        with patch('src.agent.MCPServerStdio', side_effect=mock_mcp_factory):
            with patch.object(agent.agent, 'run_mcp_servers', return_value=AsyncMock()):
                with patch.object(agent.agent, 'run', AsyncMock(return_value=MagicMock(data="response"))):
                    await agent.chat("test1")
                    await agent.chat("test2")
                    assert call_count == 2


@pytest.mark.asyncio
class TestPerformance:
    """Test performance characteristics."""
    
    async def test_concurrent_chat_calls(self, agent):
        """Test concurrent chat calls don't interfere."""
        with patch.object(agent.agent, 'run_mcp_servers', return_value=AsyncMock()):
            with patch.object(agent.agent, 'run', AsyncMock(return_value=MagicMock(data="response"))):
                tasks = [
                    agent.chat(f"test {i}")
                    for i in range(5)
                ]
                results = await asyncio.gather(*tasks)
                assert len(results) == 5
                assert all(r == "response" for r in results)
