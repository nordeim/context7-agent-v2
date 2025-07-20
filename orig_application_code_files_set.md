# src/agent.py
```py
import os
from typing import Optional, List, Dict, Any

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Config
from .history import HistoryManager


class Context7Agent:
    """
    Production-ready AI agent implementing a robust RAG pattern, deeply integrated with Context7 MCP.
    All chat and tool-calling happens via agent.run(), enforcing strict RAG: answers ONLY from retrieved context.
    """

    def __init__(self, config: Optional[Config] = None):
        config = config or Config.load()
        self.config = config

        # Provider
        self.provider = OpenAIProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
        )

        # Model
        self.model = OpenAIModel(
            model_name=config.openai_model,
            provider=self.provider,
        )

        # MCP server (Context7)
        self.mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"],
        )

        # Gold-standard RAG system prompt
        self.agent = Agent(
            model=self.model,
            mcp_servers=[self.mcp_server],
            system_prompt=config.rag_system_prompt
        )

        # History manager
        self.history = HistoryManager(filepath=config.history_file)

    async def initialize(self):
        """Load persisted history and prepare agent."""
        await self.history.load_async()

    async def chat(
        self, user_text: str, message_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Processes a user query via the unified agent.run() method.
        MCP server lifecycle must be managed by the caller.
        """
        message_history = message_history or []
        result = await self.agent.run(user_text, message_history=message_history)
        return str(result.data)

    async def chat_stream(
        self, user_text: str, message_history: Optional[List[Dict]] = None
    ):
        """
        Streams the chat response (for live/animated UI).
        """
        message_history = message_history or []
        async for chunk in self.agent.run_stream(user_text, message_history=message_history):
            yield chunk

    def get_history(self):
        return self.history.history

    async def save_history(self):
        await self.history.save_async()

```

# src/cli.py
```py
import anyio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.syntax import Syntax

import os
from typing import List, Dict

from .agent import Context7Agent
from .config import Config
from .themes import get_theme, get_ascii_art, get_animation_frames
from .utils import format_error, format_success

console = Console()

def print_ascii_art(theme: str):
    art = get_ascii_art(theme)
    console.print(Panel(art, style="ascii"))

def print_help():
    help_text = """
[bold cyan]/help[/bold cyan]            Show this help screen
[bold cyan]/theme THEME[/bold cyan]     Switch theme (cyberpunk, ocean, forest, sunset)
[bold cyan]/preview N[/bold cyan]       Preview document N (from results)
[bold cyan]/bookmark N[/bold cyan]      Bookmark document N
[bold cyan]/analytics[/bold cyan]       Show search analytics
[bold cyan]/history[/bold cyan]         Show chat history
[bold cyan]/exit[/bold cyan]            Exit the agent
"""
    console.print(help_text)

async def render_loader(frames, duration=2.0):
    import time
    from itertools import cycle
    start = time.time()
    with Live("", refresh_per_second=8, console=console) as live:
        for frame in cycle(frames):
            if time.time() - start > duration:
                break
            live.update(frame)
            await anyio.sleep(0.12)

async def main():
    config = Config.load()
    agent = Context7Agent(config)
    await agent.initialize()

    theme = config.theme
    console.push_theme(get_theme(theme))

    print_ascii_art(theme)
    console.print(f"[header]Welcome to Context7 Agent! (Theme: {theme})[/header]")
    print_help()

    history = agent.get_history()
    bookmarks = agent.history.get_bookmarks()
    last_results: List[Dict] = []

    async with agent.agent.agent.run_mcp_servers():
        while True:
            try:
                user_input = await anyio.to_thread.run_sync(
                    lambda: Prompt.ask("[bold cyan]You[/bold cyan]")
                )
            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold magenta]Goodbye![/bold magenta]")
                break

            if not user_input.strip():
                continue

            if user_input.lower() == "/exit":
                console.print("[bold magenta]Goodbye![/bold magenta]")
                break
            elif user_input.lower() == "/help":
                print_help()
                continue
            elif user_input.startswith("/theme"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1] in get_theme.__annotations__:
                    theme = parts[1]
                else:
                    theme = parts[1] if len(parts) > 1 else "cyberpunk"
                console.pop_theme()
                console.push_theme(get_theme(theme))
                print_ascii_art(theme)
                continue
            elif user_input.lower() == "/history":
                table = Table(title="Conversation History")
                table.add_column("Role")
                table.add_column("Message")
                for msg in history:
                    table.add_row(msg.get("role", ""), msg.get("content", ""))
                console.print(table)
                continue
            elif user_input.startswith("/bookmark"):
                try:
                    idx = int(user_input.split()[1]) - 1
                    doc = last_results[idx]
                    agent.history.add_bookmark(doc)
                    console.print(format_success("Bookmarked!"))
                except Exception:
                    console.print(format_error("Could not bookmark."))
                continue
            elif user_input.startswith("/preview"):
                try:
                    idx = int(user_input.split()[1]) - 1
                    doc = last_results[idx]
                    content = doc.get("content", "")
                    filetype = doc.get("type", "txt")
                    syntax = Syntax(content, filetype, theme="monokai", line_numbers=True)
                    console.print(syntax)
                except Exception:
                    console.print(format_error("Could not preview document."))
                continue
            elif user_input.lower() == "/analytics":
                # Dummy analytics for now
                console.print("[bold yellow]Analytics coming soon![/bold yellow]")
                continue

            # Animated loader
            await render_loader(get_animation_frames(theme), duration=1.5)

            # Intent detection: if user asks about a subject, auto-search via MCP
            try:
                response = await agent.chat(user_input, history)
                # Assume response may include search results (if RAG)
                console.print(Panel(response, title="Agent", style="primary"))
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": response})
                await agent.save_history()
                # Optionally: parse/search results here to populate last_results for /preview, /bookmark
                # For now, stub it:
                last_results = []
            except Exception as e:
                console.print(format_error(str(e)))

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        console.print("\n[bold magenta]Goodbye![/bold magenta]")

```

# src/config.py
```py
import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

THEMES = ["cyberpunk", "ocean", "forest", "sunset"]

DEFAULT_PROMPT = """
You are a specialized AI research assistant named Context7.

## CORE DIRECTIVE
Your SOLE PURPOSE is to provide answers by exclusively using the information retrieved from the attached `search` tool, which connects to the official Context7 knowledge base. You are forbidden from using your own internal, pre-trained knowledge, as it is considered outdated and unreliable.

## RULES OF ENGAGEMENT
1.  **MUST use the tool:** For any user question that is not a simple greeting (like "hello"), you MUST ALWAYS call the `search` tool to gather context before formulating an answer.
2.  **MUST ground your answer:** You MUST synthesize your final answer using ONLY the `documents` and `content` provided in the tool's output. Do not add any information not present in the retrieved context.
3.  **MUST handle failure:** If the `search` tool returns no relevant documents or an error, you MUST respond with the exact phrase: "I could not find any relevant information in the Context7 knowledge base to answer your question." Do not attempt to answer from memory.
4.  **MUST be concise:** When you call the tool, formulate a concise and effective search query string based on the user's intent. Do not pass the user's entire conversational text to the tool.

## OPERATIONAL FLOW
For every user query, you will follow this exact sequence:
1.  **Analyze:** Deconstruct the user's query to identify the core topic.
2.  **Formulate Query:** Create a clear, concise search term (e.g., "pydantic-ai MCP server setup" or "agent streaming").
3.  **Execute Tool:** Call the `search` tool with the formulated query.
4.  **Analyze Context:** Carefully review the documents returned by the tool.
5.  **Synthesize Answer:** Construct a comprehensive answer based only on the retrieved documents, citing sources if possible.
"""

class Config(BaseModel):
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    rag_system_prompt: str = DEFAULT_PROMPT
    theme: str = "cyberpunk"
    history_file: str = os.path.expanduser("~/.context7_history.json")

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            rag_system_prompt=os.getenv("RAG_SYSTEM_PROMPT", DEFAULT_PROMPT),
            theme=os.getenv("CONTEXT7_THEME", "cyberpunk"),
            history_file=os.getenv("CONTEXT7_HISTORY_FILE", os.path.expanduser("~/.context7_history.json"))
        )

```

# src/history.py
```py
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

```

# src/themes.py
```py
from rich.style import Style
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.theme import Theme

THEMES = {
    "cyberpunk": Theme({
        "primary": "bold magenta",
        "accent": "bright_cyan",
        "header": "bold magenta on black",
        "background": "black",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "bright_magenta",
        "glow": "bold magenta blink",
        "gradient": "magenta on black",
    }),
    "ocean": Theme({
        "primary": "bold blue",
        "accent": "cyan",
        "header": "bold white on blue",
        "background": "blue",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "cyan",
        "glow": "bold blue blink",
        "gradient": "cyan on blue",
    }),
    "forest": Theme({
        "primary": "bold green",
        "accent": "bright_green",
        "header": "bold green on black",
        "background": "black",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "green",
        "glow": "bold green blink",
        "gradient": "green on black",
    }),
    "sunset": Theme({
        "primary": "bold yellow",
        "accent": "bright_red",
        "header": "bold white on red",
        "background": "red",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "ascii": "yellow",
        "glow": "bold yellow blink",
        "gradient": "yellow on red",
    }),
}

ASCII_ART = {
    "cyberpunk": r"""
     ____            _               _     _     _           
    / ___| ___ _ __ | |_ _   _ _ __ | |__ (_)___| | __       
   | |   / _ \ '_ \| __| | | | '_ \| '_ \| / __| |/ /       
   | |__|  __/ | | | |_| |_| | |_) | | | | \__ \   <        
    \____\___|_| |_|\__|\__,_| .__/|_| |_|_|___/_|\_\       
                             |_|                             
    """,
    "ocean": r"""
     ~~~~~  OCEAN THEME  ~~~~~
    ~~~  ~~~   ~~~   ~~~   ~~~
    """,
    "forest": r"""
      🌲🌳 FOREST THEME 🌳🌲
     ////\\\\////\\\\////\\\\
    """,
    "sunset": r"""
      🌅 SUNSET THEME 🌅
    ~~~~~~~~~~~~~~~~~~~~~~
    """,
}

ANIMATION_FRAMES = {
    "cyberpunk": [
        "[magenta]*[/magenta]    ",
        " [magenta]*[/magenta]   ",
        "  [magenta]*[/magenta]  ",
        "   [magenta]*[/magenta] ",
        "    [magenta]*[/magenta]",
        "   [magenta]*[/magenta] ",
        "  [magenta]*[/magenta]  ",
        " [magenta]*[/magenta]   ",
    ],
    "ocean": [
        "[cyan]~[/cyan]    ",
        " [cyan]~[/cyan]   ",
        "  [cyan]~[/cyan]  ",
        "   [cyan]~[/cyan] ",
        "    [cyan]~[/cyan]",
        "   [cyan]~[/cyan] ",
        "  [cyan]~[/cyan]  ",
        " [cyan]~[/cyan]   ",
    ],
    "forest": [
        "[green]🌲[/green]    ",
        " [green]🌲[/green]   ",
        "  [green]🌲[/green]  ",
        "   [green]🌲[/green] ",
        "    [green]🌲[/green]",
        "   [green]🌲[/green] ",
        "  [green]🌲[/green]  ",
        " [green]🌲[/green]   ",
    ],
    "sunset": [
        "[yellow]🌅[/yellow]    ",
        " [yellow]🌅[/yellow]   ",
        "  [yellow]🌅[/yellow]  ",
        "   [yellow]🌅[/yellow] ",
        "    [yellow]🌅[/yellow]",
        "   [yellow]🌅[/yellow] ",
        "  [yellow]🌅[/yellow]  ",
        " [yellow]🌅[/yellow]   ",
    ],
}

def get_theme(theme_name: str):
    return THEMES.get(theme_name, THEMES["cyberpunk"])

def get_ascii_art(theme_name: str):
    return ASCII_ART.get(theme_name, ASCII_ART["cyberpunk"])

def get_animation_frames(theme_name: str):
    return ANIMATION_FRAMES.get(theme_name, ANIMATION_FRAMES["cyberpunk"])

```

# src/utils.py
```py
import re
import difflib
from typing import List, Dict, Optional, Any

def fuzzy_match(query: str, choices: List[str], cutoff: float = 0.6) -> List[str]:
    """Return a list of choices that best match the query (fuzzy, case-insensitive)."""
    return difflib.get_close_matches(query, choices, n=5, cutoff=cutoff)

def filter_documents(
    docs: List[Dict[str, Any]], 
    file_type: Optional[str] = None, 
    date_range: Optional[List[str]] = None, 
    size_range: Optional[List[int]] = None,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Filter documents by type, date, size, or tags."""
    filtered = docs
    if file_type:
        filtered = [d for d in filtered if d.get("type") == file_type]
    if date_range:
        start, end = date_range
        filtered = [d for d in filtered if start <= d.get("date", "") <= end]
    if size_range:
        min_size, max_size = size_range
        filtered = [d for d in filtered if min_size <= d.get("size", 0) <= max_size]
    if tags:
        filtered = [d for d in filtered if set(tags) & set(d.get("tags", []))]
    return filtered

def syntax_highlight(text: str, filetype: str = "txt") -> str:
    """Dummy syntax highlighter (real logic should use Pygments or Rich in CLI)."""
    # For CLI, delegate to Rich's Syntax class
    return text

def format_error(msg: str) -> str:
    return f"[bold red]Error:[/bold red] {msg}"

def format_success(msg: str) -> str:
    return f"[bold green]Success:[/bold green] {msg}"

def async_sleep(secs: float):
    import anyio
    return anyio.sleep(secs)

```

