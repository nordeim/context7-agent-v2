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
