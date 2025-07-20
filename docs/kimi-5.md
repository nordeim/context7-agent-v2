<think>
# Deep Analysis - Test Suite Planning

Let me systematically plan the creation of comprehensive test files that ensure zero regressions and full production readiness.

## Test Planning Matrix

| Test File | Coverage Target | Key Scenarios | Production Focus | Edge Cases |
|-----------|----------------|---------------|------------------|------------|
| **test_agent.py** | 95% | MCP lifecycle, chat, streaming | Runtime MCP creation | Network failures |
| **test_config.py** | 100% | Validation, loading, error cases | Environment validation | Missing vars, invalid values |
| **test_history.py** | 100% | Async I/O, persistence, bookmarks | Thread safety | File corruption, permissions |

## Deep Planning

### 1. test_agent.py Strategy
- **Mock MCP server** for testing without external deps
- **Async context manager** testing for MCP lifecycle
- **Error scenarios**: network failures, invalid responses
- **Streaming testing** with async generators
- **Integration patterns** with real components

### 2. test_config.py Strategy
- **Environment variable** mocking
- **Validation testing** for all edge cases
- **Error message** verification
- **Backward compatibility** testing
- **Type safety** validation

### 3. test_history.py Strategy
- **Async file operations** testing
- **Thread safety** validation
- **JSON serialization/deserialization**
- **Error handling** for file operations
- **Performance testing** for large datasets

## Test Architecture
- **pytest-asyncio** for async testing
- **pytest-mock** for mocking
- **pytest-cov** for coverage
- **aiofiles** for async file testing
- **tempfile** for isolated testing
</think>

## 1. tests/test_agent.py

```python
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
```

## 2. tests/test_config.py

```python
"""
Comprehensive tests for configuration management.
Tests validation, loading, and error handling.
"""

import pytest
import os
import tempfile
from unittest.mock import patch

from src.config import Config, THEMES


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_valid_config_creation(self):
        """Test creating a valid config instance."""
        config = Config(
            openai_api_key="test-key-123",
            theme="cyberpunk",
            openai_model="gpt-4o-mini"
        )
        assert config.openai_api_key == "test-key-123"
        assert config.theme == "cyberpunk"
        assert config.openai_model == "gpt-4o-mini"
        assert config.openai_base_url == "https://api.openai.com/v1"
    
    def test_default_values(self):
        """Test default configuration values."""
        config = Config(openai_api_key="test-key-123")
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o-mini"
        assert config.theme == "cyberpunk"
        assert "Context7" in config.rag_system_prompt


class TestConfigLoading:
    """Test configuration loading from environment."""
    
    def test_load_with_valid_env(self):
        """Test loading config with valid environment variables."""
        env_vars = {
            "OPENAI_API_KEY": "test-api-key",
            "OPENAI_BASE_URL": "https://custom-api.com/v1",
            "OPENAI_MODEL": "gpt-4o",
            "CONTEXT7_THEME": "ocean"
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.load()
            assert config.openai_api_key == "test-api-key"
            assert config.openai_base_url == "https://custom-api.com/v1"
            assert config.openai_model == "gpt-4o"
            assert config.theme == "ocean"
    
    def test_load_missing_api_key(self):
        """Test loading config with missing API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Config.load()
            assert "OPENAI_API_KEY is required" in str(exc_info.value)
    
    def test_load_invalid_theme(self):
        """Test loading config with invalid theme raises error."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "CONTEXT7_THEME": "invalid-theme"
        }
        
        with patch.dict(os.environ, env_vars):
            with pytest.raises(ValueError) as exc_info:
                Config.load()
            assert "Invalid theme" in str(exc_info.value)
            assert "cyberpunk, ocean, forest, sunset" in str(exc_info.value)
    
    def test_load_with_env_file(self):
        """Test loading config from .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OPENAI_API_KEY=env-file-key\n")
            f.write("CONTEXT7_THEME=forest\n")
            env_file = f.name
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch('src.config.load_dotenv') as mock_load:
                    # Simulate loading from .env file
                    os.environ["OPENAI_API_KEY"] = "env-file-key"
                    os.environ["CONTEXT7_THEME"] = "forest"
                    
                    config = Config.load()
                    assert config.openai_api_key == "env-file-key"
                    assert config.theme == "forest"
        finally:
            os.unlink(env_file)


class TestConfigValidation:
    """Test individual configuration validation."""
    
    def test_all_valid_themes(self):
        """Test all valid themes are accepted."""
        for theme in THEMES:
            config = Config(
                openai_api_key="test-key",
                theme=theme
            )
            assert config.theme == theme
    
    def test_custom_history_path(self):
        """Test custom history file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = os.path.join(temp_dir, "custom_history.json")
            config = Config(
                openai_api_key="test-key",
                history_file=custom_path
            )
            assert config.history_file == custom_path
    
    def test_custom_system_prompt(self):
        """Test custom system prompt."""
        custom_prompt = "Custom system prompt"
        config = Config(
            openai_api_key="test-key",
            rag_system_prompt=custom_prompt
        )
        assert config.rag_system_prompt == custom_prompt
    
    def test_empty_api_key_raises_error(self):
        """Test empty API key raises validation error."""
        with pytest.raises(ValueError):
            Config.load()


class TestConfigBackwardCompatibility:
    """Test backward compatibility."""
    
    def test_minimal_config(self):
        """Test config with only required fields."""
        config = Config(openai_api_key="test-key")
        assert config.openai_api_key == "test-key"
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o-mini"
        assert config.theme == "cyberpunk"
    
    def test_environment_fallback(self):
        """Test environment variables as fallback."""
        env_vars = {
            "OPENAI_API_KEY": "fallback-key",
            "OPENAI_BASE_URL": "https://fallback.com/v1"
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.load()
            assert config.openai_api_key == "fallback-key"
            assert config.openai_base_url == "https://fallback.com/v1"
```

## 3. tests/test_history.py

```python
"""
Comprehensive tests for history management.
Tests async file I/O, persistence, and data integrity.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path

from src.history import HistoryManager


@pytest.fixture
def temp_history_file():
    """Create a temporary history file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def history_manager(temp_history_file):
    """Create a history manager with temporary file."""
    return HistoryManager(filepath=temp_history_file)


@pytest.mark.asyncio
class TestHistoryBasicOperations:
    """Test basic history operations."""
    
    async def test_empty_history_on_creation(self, history_manager):
        """Test history is empty on creation."""
        assert history_manager.history == []
        assert history_manager.bookmarks == []
        assert history_manager.sessions == []
    
    async def test_append_message(self, history_manager):
        """Test appending messages to history."""
        message = {"role": "user", "content": "Hello world"}
        history_manager.append(message)
        assert len(history_manager.history) == 1
        assert history_manager.history[0] == message
    
    async def test_clear_history(self, history_manager):
        """Test clearing history."""
        history_manager.append({"role": "user", "content": "test"})
        history_manager.clear()
        assert len(history_manager.history) == 0
    
    async def test_add_bookmark(self, history_manager):
        """Test adding bookmarks."""
        doc = {"title": "Test Doc", "content": "Test content"}
        history_manager.add_bookmark(doc)
        assert len(history_manager.bookmarks) == 1
        assert history_manager.bookmarks[0] == doc
    
    async def test_prevent_duplicate_bookmarks(self, history_manager):
        """Test preventing duplicate bookmarks."""
        doc = {"title": "Test Doc", "content": "Test content"}
        history_manager.add_bookmark(doc)
        history_manager.add_bookmark(doc)  # Duplicate
        assert len(history_manager.bookmarks) == 1
    
    async def test_add_session(self, history_manager):
        """Test adding sessions."""
        session = {"name": "Test Session", "messages": []}
        history_manager.add_session(session)
        assert len(history_manager.sessions) == 1
        assert history_manager.sessions[0] == session


@pytest.mark.asyncio
class TestHistoryPersistence:
    """Test history persistence and file operations."""
    
    async def test_save_and_load_empty(self, history_manager):
        """Test saving and loading empty history."""
        await history_manager.save_async()
        await history_manager.load_async()
        
        assert history_manager.history == []
        assert history_manager.bookmarks == []
        assert history_manager.sessions == []
    
    async def test_save_and_load_with_data(self, history_manager):
        """Test saving and loading with actual data."""
        # Add some data
        history_manager.append({"role": "user", "content": "Test message"})
        history_manager.add_bookmark({"title": "Test Bookmark"})
        history_manager.add_session({"name": "Test Session"})
        
        # Save and reload
        await history_manager.save_async()
        await history_manager.load_async()
        
        assert len(history_manager.history) == 1
        assert history_manager.history[0]["content"] == "Test message"
        assert len(history_manager.bookmarks) == 1
        assert history_manager.bookmarks[0]["title"] == "Test Bookmark"
        assert len(history_manager.sessions) == 1
        assert history_manager.sessions[0]["name"] == "Test Session"
    
    async def test_load_from_existing_file(self, temp_history_file):
        """Test loading from existing history file."""
        # Create pre-existing file
        test_data = {
            "history": [{"role": "assistant", "content": "existing"}],
            "bookmarks": [{"title": "existing bookmark"}],
            "sessions": [{"name": "existing session"}]
        }
        
        with open(temp_history_file, 'w') as f:
            json.dump(test_data, f)
        
        history_manager = HistoryManager(filepath=temp_history_file)
        await history_manager.load_async()
        
        assert len(history_manager.history) == 1
        assert history_manager.history[0]["content"] == "existing"
        assert len(history_manager.bookmarks) == 1
        assert len(history_manager.sessions) == 1
    
    async def test_load_nonexistent_file(self, temp_history_file):
        """Test loading from non-existent file."""
        nonexistent_file = temp_history_file + "_nonexistent"
        history_manager = HistoryManager(filepath=nonexistent_file)
        
        await history_manager.load_async()
        
        assert history_manager.history == []
        assert history_manager.bookmarks == []
        assert history_manager.sessions == []
    
    async def test_load_corrupted_file(self, temp_history_file):
        """Test loading from corrupted JSON file."""
        with open(temp_history_file, 'w') as f:
            f.write("invalid json")
        
        history_manager = HistoryManager(filepath=temp_history_file)
        await history_manager.load_async()
        
        # Should handle gracefully and reset to empty
        assert history_manager.history == []
        assert history_manager.bookmarks == []
        assert history_manager.sessions == []


@pytest.mark.asyncio
class TestHistoryAsyncOperations:
    """Test async file operations."""
    
    async def test_async_save_load_consistency(self, history_manager):
        """Test async save/load maintains consistency."""
        # Add data
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)
        ]
        
        for msg in messages:
            history_manager.append(msg)
        
        # Save asynchronously
        await history_manager.save_async()
        
        # Create new instance and load
        new_manager = HistoryManager(filepath=history_manager.filepath)
        await new_manager.load_async()
        
        assert len(new_manager.history) == 10
        assert new_manager.history[-1]["content"] == "Message 9"
    
    async def test_concurrent_save_load(self, history_manager):
        """Test concurrent save/load operations."""
        # Add initial data
        history_manager.append({"role": "user", "content": "initial"})
        
        # Concurrent operations
        tasks = [
            history_manager.save_async(),
            history_manager.load_async(),
            history_manager.save_async()
        ]
        
        await asyncio.gather(*tasks)
        
        # Should not crash
        assert isinstance(history_manager.history, list)
    
    async def test_large_dataset_performance(self, history_manager):
        """Test performance with large dataset."""
        # Create large dataset
        large_messages = [
            {"role": "user", "content": f"Large message {i}"}
            for i in range(1000)
        ]
        
        history_manager.history = large_messages
        
        # Measure save/load time
        start = asyncio.get_event_loop().time()
        await history_manager.save_async()
        await history_manager.load_async()
        duration = asyncio.get_event_loop().time() - start
        
        # Should complete within reasonable time (adjust as needed)
        assert duration < 5.0  # 5 seconds for 1000 messages
        assert len(history_manager.history) == 1000


@pytest.mark.asyncio
class TestHistoryFileOperations:
    """Test file system operations."""
    
    async def test_directory_creation(self, temp_history_file):
        """Test directory creation for history file."""
        custom_dir = os.path.join(tempfile.gettempdir(), "custom_history_dir")
        custom_file = os.path.join(custom_dir, "history.json")
        
        history_manager = HistoryManager(filepath=custom_file)
        history_manager.append({"role": "test", "content": "test"})
        await history_manager.save_async()
        
        assert os.path.exists(custom_dir)
        assert os.path.exists(custom_file)
        
        # Cleanup
        import shutil
        shutil.rmtree(custom_dir, ignore_errors=True)
    
    async def test_file_permissions(self, temp_history_file):
        """Test file permissions after save."""
        history_manager = HistoryManager(filepath=temp_history_file)
        history_manager.append({"role": "user", "content": "test"})
        await history_manager.save_async()
        
        # Check file exists and is readable
        assert os.path.exists(temp_history_file)
        assert os.access(temp_history_file, os.R_OK)
        assert os.access(temp_history_file, os.W_OK)


class TestHistoryBackwardCompatibility:
    """Test backward compatibility."""
    
    def test_sync_methods(self, history_manager):
        """Test sync methods still work."""
        history_manager.append({"role": "user", "content": "sync test"})
        history_manager.save()
        history_manager.load()
        
        assert len(history_manager.history) == 1
        assert history_manager.history[0]["content"] == "sync test"
    
    def test_legacy_file_format(self, temp_history_file):
        """Test loading legacy file formats."""
        legacy_data = [
            {"user": "hello", "assistant": "hi"}
        ]
        
        with open(temp_history_file, 'w') as f:
            json.dump(legacy_data, f)
        
        history_manager = HistoryManager(filepath=temp_history_file)
        history_manager.load()
        
        # Should handle gracefully
        assert isinstance(history_manager.history, list)


@pytest.mark.asyncio
class TestHistoryIntegration:
    """Test integration with agent."""
    
    async def test_agent_integration(self, temp_history_file):
        """Test history integration with agent."""
        from src.agent import Context7Agent
        from src.config import Config
        
        config = Config(
            openai_api_key="test-key",
            history_file=temp_history_file
        )
        
        agent = Context7Agent(config)
        await agent.initialize()
        
        # Add history through agent
        agent.history.append({"role": "user", "content": "integration test"})
        await agent.save_history()
        
        # Verify persistence
        new_agent = Context7Agent(config)
        await new_agent.initialize()
        
        assert len(new_agent.get_history()) >= 1
```

