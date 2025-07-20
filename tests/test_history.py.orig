import pytest
import tempfile
import os
from src.history import HistoryManager

def test_history_save_and_load(tmp_path):
    # Use a temp directory to avoid polluting real data
    history_path = tmp_path / "history.json"
    manager = HistoryManager(filepath=history_path)

    # Add conversation
    manager.append({"role": "user", "content": "Hello"})
    manager.append({"role": "assistant", "content": "Hi there!"})
    manager.save()

    # Load new instance, should get same history
    new_manager = HistoryManager(filepath=history_path)
    new_manager.load()
    assert new_manager.history == manager.history

def test_history_append_and_clear(tmp_path):
    manager = HistoryManager(filepath=tmp_path / "h.json")
    manager.append({"role": "user", "content": "A"})
    manager.append({"role": "assistant", "content": "B"})
    assert len(manager.history) == 2
    manager.clear()
    assert manager.history == []

def test_history_session_restore(tmp_path):
    manager = HistoryManager(filepath=tmp_path / "session.json")
    session_data = [
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "2"}
    ]
    manager.history = session_data
    manager.save()

    # Simulate restore
    new_manager = HistoryManager(filepath=tmp_path / "session.json")
    new_manager.load()
    assert new_manager.history == session_data
