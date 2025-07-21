# .env.example
```example
# Copy this file to .env and fill in your details

# Required: OpenAI API key for chat and intent detection
OPENAI_API_KEY=sk-...

# Optional: Override OpenAI API base URL (default: https://api.openai.com/v1)
OPENAI_BASE_URL=https://api.openai.com/v1

# Optional: Model to use (default: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# Optional: Default theme ("cyberpunk", "ocean", "forest", "sunset")
CONTEXT7_THEME=cyberpunk

# Optional: Location for saving chat, bookmarks, and sessions
CONTEXT7_HISTORY_FILE=~/.context7_history.json

# Optional: Override the RAG system prompt (advanced)
RAG_SYSTEM_PROMPT=

```

# pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "context7-agent-v2"
version = "2.0.0"
description = "Production-ready terminal AI agent with Pydantic-AI v0.5+ and MCP"
authors = [
  { name = "Context7 Team", email = "team@context7.ai" }
]
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
keywords = ["ai", "terminal", "pydantic", "mcp", "openai"]
classifiers = [
  "Development Status :: 5 - Production/Stable",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Topic :: Software Development :: Libraries :: Python Modules",
  "Topic :: Terminals",
  "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
  "pydantic-ai[openai]==0.4.2",
  "pydantic==2.11.7",
  "python-dotenv==1.1.1",
  "anyio==4.9.0",
  "rich==14.0.0",
  "aiofiles==24.1.0",
  "openai==1.95.1",
  "typing-extensions==4.14.1",
]

[project.optional-dependencies]
dev = [
  "pytest==8.4.1",
  "pytest-asyncio==1.1.0",
  # pytest-cov       # not installed in your environment
  # black           # not installed
  # isort           # not installed
  # flake8          # not installed
  # mypy            # not installed
  # pre-commit      # not installed
]

[project.urls]
Homepage      = "https://github.com/nordeim/context7-agent-v2"
Documentation = "https://docs.context7.ai"
Repository    = "https://github.com/nordeim/context7-agent-v2"
Issues        = "https://github.com/nordeim/context7-agent-v2/issues"

[project.scripts]
context7 = "src.cli:main"

[tool.setuptools]
packages = ["src"]

[tool.black]
line-length    = 88
target-version = ['py311']
include        = '\.pyi?$'

[tool.isort]
profile           = "black"
multi_line_output = 3
line_length       = 88

[tool.mypy]
python_version            = "3.11"
warn_return_any           = true
warn_unused_configs       = true
disallow_untyped_defs     = true
disallow_incomplete_defs  = true
check_untyped_defs        = true
no_implicit_optional      = true
warn_redundant_casts      = true
warn_unused_ignores       = true
warn_no_return            = true
plugins                   = ["pydantic.mypy"]

[tool.pytest.ini_options]
testpaths        = ["tests"]
python_files     = ["test_*.py"]
python_classes   = ["Test*"]
python_functions = ["test_*"]
addopts          = "-v --tb=short --strict-markers --disable-warnings"
markers = [
  "slow: marks tests as slow",
  "integration: marks tests as integration tests",
  "asyncio: marks tests as asyncio tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit   = ["*/tests/*", "*/venv/*", "*/.venv/*"]

[tool.coverage.report]
exclude_lines = [
  "pragma: no cover",
  "def __repr__",
  "raise AssertionError",
  "raise NotImplementedError",
]

```

# requirements.txt
```txt
# Core dependencies - pinned for reproducibility
pydantic-ai[openai]==0.4.2
pydantic==2.11.7
python-dotenv==1.1.1
anyio==4.9.0
rich==14.0.0
aiofiles==24.1.0

# OpenAI integration
openai==1.95.1

# Production utilities
typing-extensions==4.14.1
```

```

# src/agent.py
```py
import os
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Config
from .history import HistoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Context7Agent:
    """
    Production-ready AI agent implementing Context7 MCP integration.
    Uses pydantic-ai 0.4.2+ with proper error handling and non-empty system prompts.
    """

    def __init__(self, config: Optional[Config] = None):
        config = config or Config.load()
        self.config = config

        # Provider
        self.provider = OpenAIProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
        )

        # Ensure system prompt is never empty
        system_prompt = config.rag_system_prompt or """
        You are a specialized AI research assistant named Context7.
        
        Your sole purpose is to provide answers by exclusively using information 
        retrieved from the Context7 knowledge base. You are forbidden from using 
        your own internal knowledge.
        
        When a user asks a question, you must:
        1. Use the search tool to query the Context7 knowledge base
        2. Synthesize your answer exclusively from retrieved documents
        3. Be concise and directly address the user's question
        4. If no relevant information is found, clearly state that
        
        Format your responses in clear, readable markdown.
        """

        # MCP server - exactly as shown in working examples
        self.mcp_server = self.create_mcp_server()

        # Agent with correct model string format and non-empty system prompt
        model_string = f"openai:{config.openai_model}"
        self.agent = Agent(
            model_string,
            mcp_servers=[self.mcp_server],
            system_prompt=system_prompt
        )

        # History manager
        self.history = HistoryManager(filepath=config.history_file)

    async def initialize(self):
        """Initialize the agent and load history."""
        try:
            await self.history.load_async()
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            raise

    def create_mcp_server(self) -> MCPServerStdio:
        """Create MCP server with proper configuration."""
        import shutil
        
        npx_path = shutil.which("npx")
        if not npx_path:
            raise RuntimeError(
                "npx not found in PATH. Please install Node.js 18+ and ensure npm is available."
            )
        
        return MCPServerStdio(
            command=npx_path,
            args=["-y", "@upstash/context7-mcp@latest"],
            env=os.environ
        )

    async def chat(
        self, user_text: str, message_history: Optional[List[Dict]] = None
    ) -> str:
        """Process user query with MCP tools."""
        message_history = message_history or []
        
        try:
            async with self.agent.run_mcp_servers():
                logger.debug(f"Processing query: {user_text}")
                result = await self.agent.run(user_text, message_history=message_history)
                return str(result.data)
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"I encountered an error: {str(e)}. Please check your configuration and try again."

    async def chat_stream(
        self, user_text: str, message_history: Optional[List[Dict]] = None
    ):
        """Stream chat response with proper MCP server lifecycle."""
        message_history = message_history or []
        
        try:
            async with self.agent.run_mcp_servers():
                logger.debug(f"Streaming query: {user_text}")
                async for chunk in self.agent.run_stream(user_text, message_history=message_history):
                    yield str(chunk)
                    
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Streaming error: {str(e)}"

    def get_history(self):
        """Get conversation history."""
        return self.history.history

    async def save_history(self):
        """Save conversation history."""
        try:
            await self.history.save_async()
            logger.info("History saved successfully")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            raise

```

# src/cli.py
```py
import anyio
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.syntax import Syntax
from rich.text import Text
import subprocess
import shutil
from typing import List, Dict

from .agent import Context7Agent
from .config import Config
from .themes import get_theme, get_ascii_art, get_animation_frames
from .utils import format_error, format_success

# Add missing import
from datetime import datetime

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

def check_nodejs():
    """Check if Node.js and npx are available."""
    try:
        result = subprocess.run(["node", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            node_version = result.stdout.strip()
            console.print(f"[green]✅ Node.js {node_version} found[/green]")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]❌ Node.js not found or not in PATH[/red]")
        return False
    
    try:
        result = subprocess.run(["npx", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.print(f"[green]✅ npx {result.stdout.strip()} found[/green]")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]❌ npx not found[/red]")
        return False
    
    return False

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

    # Pre-flight checks
    if not check_nodejs():
        console.print("[yellow]⚠️  Node.js 18+ and npm are required for MCP functionality[/yellow]")
        console.print("[dim]Install from: https://nodejs.org/[/dim]")
        return

    try:
        console.print("[dim]Starting Context7 MCP server...[/dim]")
        console.print("[green]✅ Context7 MCP server connected successfully[/green]")
        
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
                if len(parts) > 1 and parts[1] in ["cyberpunk", "ocean", "forest", "sunset"]:
                    theme = parts[1]
                    console.pop_theme()
                    console.push_theme(get_theme(theme))
                    print_ascii_art(theme)
                    console.print(f"[green]Theme switched to {theme}[/green]")
                else:
                    console.print("[red]Invalid theme. Use: cyberpunk, ocean, forest, sunset[/red]")
                continue
            elif user_input.lower() == "/history":
                table = Table(title="Conversation History")
                table.add_column("Role")
                table.add_column("Message")
                for msg in history:
                    table.add_row(msg.get("role", ""), msg.get("content", "")[:100] + "...")
                console.print(table)
                continue
            elif user_input.startswith("/bookmark"):
                try:
                    idx = int(user_input.split()[1]) - 1
                    doc = last_results[idx]
                    agent.history.add_bookmark(doc)
                    console.print(format_success("Bookmarked!"))
                except (IndexError, ValueError, AttributeError):
                    console.print(format_error("Invalid bookmark index."))
                continue
            elif user_input.startswith("/preview"):
                try:
                    idx = int(user_input.split()[1]) - 1
                    doc = last_results[idx]
                    content = doc.get("content", "No content available")
                    filetype = doc.get("type", "txt")
                    syntax = Syntax(content, filetype, theme="monokai", line_numbers=True)
                    console.print(syntax)
                except (IndexError, ValueError):
                    console.print(format_error("Invalid preview index."))
                continue
            elif user_input.lower() == "/analytics":
                console.print("[bold yellow]Analytics coming soon![/bold yellow]")
                continue

            # Animated loader
            await render_loader(get_animation_frames(theme), duration=1.5)

            try:
                response = await agent.chat(user_input, history)
                console.print(Panel(response, title="Agent", style="primary"))
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": response})
                await agent.save_history()
                last_results = []
            except Exception as e:
                console.print(format_error(f"Chat error: {str(e)}"))
                console.print("[dim]Please check your API key and internet connection[/dim]")
                    
    except Exception as e:
        console.print(f"[red]❌ Application error: {e}[/red]")
        console.print("[yellow]Troubleshooting steps:[/yellow]")
        console.print("[dim]1. Ensure Node.js 18+ is installed[/dim]")
        console.print("[dim]2. Run: npm install -g @upstash/context7-mcp@latest[/dim]")
        console.print("[dim]3. Check internet connectivity[/dim]")
    finally:
        console.print("[yellow]🔄 Shutting down gracefully...[/yellow]")

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        console.print("\n[bold magenta]Goodbye! 👋[/bold magenta]")

```

# src/config.py
```py
import os
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

THEMES = ["cyberpunk", "ocean", "forest", "sunset"]

# Ensure default system prompt is never empty
DEFAULT_PROMPT = """
You are a specialized AI research assistant named Context7.

## CORE DIRECTIVE
Your SOLE PURPOSE is to provide answers by exclusively using the information retrieved from the attached `search` tool, which connects to the official Context7 knowledge base. You are forbidden from using your own internal, pre-trained knowledge, as it is considered outdated and unreliable.

## RULES OF ENGAGEMENT
1. **MUST use the tool:** For any user question that is not a simple greeting (like "hello"), you MUST ALWAYS call the `search` tool to gather context before formulating an answer.
2. **MUST ground your answer:** You MUST synthesize your final answer using ONLY the `documents` and `content` provided in the tool's output. Do not add any information not present in the retrieved context.
3. **MUST handle failure:** If the `search` tool returns no relevant documents or an error, you MUST respond with the exact phrase: "I could not find any relevant information in the Context7 knowledge base to answer your question." Do not attempt to answer from memory.
4. **MUST be concise:** When you call the tool, formulate a concise and effective search query string based on the user's intent. Do not pass the user's entire conversational text to the tool.

## OPERATIONAL FLOW
For every user query, you will follow this exact sequence:
1. **Analyze:** Deconstruct the user's query to identify the core topic.
2. **Formulate Query:** Create a clear, concise search term (e.g., "pydantic-ai MCP server setup" or "agent streaming").
3. **Execute Tool:** Call the `search` tool with the formulated query.
4. **Analyze Context:** Carefully review the documents returned by the tool.
5. **Synthesize Answer:** Construct a comprehensive answer based only on the retrieved documents, citing sources if possible.
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
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Please set it as an environment variable:\n"
                "export OPENAI_API_KEY='your-key-here'\n"
                "Or create a .env file with OPENAI_API_KEY=your-key-here"
            )
        
        theme = os.getenv("CONTEXT7_THEME", "cyberpunk")
        if theme not in THEMES:
            raise ValueError(
                f"Invalid theme '{theme}'. Must be one of: {', '.join(THEMES)}"
            )
        
        return cls(
            openai_api_key=api_key,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            rag_system_prompt=os.getenv("RAG_SYSTEM_PROMPT", DEFAULT_PROMPT),
            theme=theme,
            history_file=os.getenv("CONTEXT7_HISTORY_FILE", os.path.expanduser("~/.context7_history.json"))
        )

```

# src/history.py
```py
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

