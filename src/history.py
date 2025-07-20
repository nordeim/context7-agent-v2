import json
import os
from typing import List, Dict, Optional, Any
import anyio
import aiofiles


class HistoryManager:
    """Manages chat, bookmarks, sessions, and search history with persistent JSON storage."""

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or os.path.expanduser("~/.context7_history.json")
        self.history: List[Dict] = []
        self.bookmarks: List[Dict] = []
        self.sessions: List[Dict] = []

    def append(self, msg: Dict[str, Any]):
        """Add a message to chat history."""
        self.history.append(msg)

    def clear(self):
        """Clear chat history."""
        self.history.clear()

    def save(self):
        """Save data to file (sync version for backwards compatibility)."""
        data = {
            "history": self.history,
            "bookmarks": self.bookmarks,
            "sessions": self.sessions,
        }
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load data from file (sync version for backwards compatibility)."""
        if not os.path.isfile(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.history = data.get("history", [])
                self.bookmarks = data.get("bookmarks", [])
                self.sessions = data.get("sessions", [])
        except (json.JSONDecodeError, FileNotFoundError):
            self.history = []
            self.bookmarks = []
            self.sessions = []

    async def save_async(self):
        """Thread-safe async file save using aiofiles."""
        data = {
            "history": self.history,
            "bookmarks": self.bookmarks,
            "sessions": self.sessions,
        }
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        async with aiofiles.open(self.filepath, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2))

    async def load_async(self):
        """Thread-safe async file load using aiofiles."""
        if not os.path.isfile(self.filepath):
            return
        try:
            async with aiofiles.open(self.filepath, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                self.history = data.get("history", [])
                self.bookmarks = data.get("bookmarks", [])
                self.sessions = data.get("sessions", [])
        except (json.JSONDecodeError, FileNotFoundError):
            self.history = []
            self.bookmarks = []
            self.sessions = []

    def add_bookmark(self, doc: Dict):
        """Add a document to bookmarks."""
        if doc not in self.bookmarks:
            self.bookmarks.append(doc)
            self.save()

    def get_bookmarks(self):
        """Get all bookmarked documents."""
        return self.bookmarks

    def add_session(self, session: Dict):
        """Add a session to sessions."""
        self.sessions.append(session)
        self.save()

    def get_sessions(self):
        """Get all saved sessions."""
        return self.sessions
