import json
import os
from typing import List, Dict, Optional, Any
import anyio

class HistoryManager:
    """Manages chat, bookmarks, sessions, and search history with persistent JSON storage."""

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or os.path.expanduser("~/.context7_history.json")
        self.history: List[Dict] = []
        self.bookmarks: List[Dict] = []
        self.sessions: List[Dict] = []

    def append(self, msg: Dict[str, Any]):
        self.history.append(msg)

    def clear(self):
        self.history.clear()

    def save(self):
        data = {
            "history": self.history,
            "bookmarks": self.bookmarks,
            "sessions": self.sessions,
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.isfile(self.filepath):
            return
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.history = data.get("history", [])
            self.bookmarks = data.get("bookmarks", [])
            self.sessions = data.get("sessions", [])

    async def save_async(self):
        await anyio.to_thread.run_sync(self.save)

    async def load_async(self):
        await anyio.to_thread.run_sync(self.load)

    def add_bookmark(self, doc: Dict):
        if doc not in self.bookmarks:
            self.bookmarks.append(doc)
            self.save()

    def get_bookmarks(self):
        return self.bookmarks

    def add_session(self, session: Dict):
        self.sessions.append(session)
        self.save()

    def get_sessions(self):
        return self.sessions
