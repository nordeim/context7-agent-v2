<think>
Step 1: Gather the original `src/cli.py` contents and locate where `MCPServerStdio` is used but not imported.

Step 2: Determine the minimal insertion point. Since `MCPServerStdio` comes from `pydantic_ai.mcp`, we’ll add:
```python
from pydantic_ai.mcp import MCPServerStdio
```
immediately after the other imports, before it’s referenced.

Step 3: Perform a line-by-line diff in my head:
- Original lines 1–9: imports of `anyio` and `rich` submodules.
- Lines 10–14: `os`, `typing`, and local imports.
- Missing: import of `MCPServerStdio`.

We will inject the import right after the rich imports block, grouping external library imports together.

Step 4: Copy the entire file, insert the new line, and verify that no other lines have changed.

Step 5: Review the final merged file against the original to confirm only the import line was added.

Step 6: Provide the full updated file within ```python tags.

Now that the plan is solid, proceed to implement.
</think>

```python
import anyio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.syntax import Syntax
from rich.text import Text

import os
from typing import List, Dict

# Added import for MCPServerStdio to fix NameError in run_mcp_servers
from pydantic_ai.mcp import MCPServerStdio

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

    try:
        # Create MCP server for the entire session
        mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"],
        )
        
        console.print("[dim]Starting MCP server...[/dim]")
        
        async with agent.agent.run_mcp_servers([mcp_server]):
            console.print("[green]✅ MCP server connected successfully[/green]")
            
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
                    except (IndexError, ValueError):
                        console.print(format_error("Invalid bookmark index."))
                    continue
                elif user_input.startswith("/preview"):
                    try:
                        idx = int(user_input.split()[1]) - 1
                        doc = last_results[idx]
                        content = doc.get("content", "")
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

                # Intent detection: if user asks about a subject, auto-search via MCP
                try:
                    response = await agent.chat(user_input, history)
                    console.print(Panel(response, title="Agent", style="primary"))
                    history.append({"role": "user", "content": user_input})
                    history.append({"role": "assistant", "content": response})
                    await agent.save_history()
                    # For now, last_results remains empty until we implement result parsing
                    last_results = []
                except Exception as e:
                    console.print(format_error(str(e)))
                    console.print("[dim]Please check your API key and internet connection[/dim]")
                    
    except Exception as e:
        console.print(f"[red]❌ Failed to start MCP server: {e}[/red]")
        console.print("[yellow]Please ensure Node.js is installed and @upstash/context7-mcp is available[/yellow]")
    finally:
        console.print("[yellow]🔄 Shutting down gracefully...[/yellow]")

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        console.print("\n[bold magenta]Goodbye![/bold magenta]")
```

<think>
**Validation**:  
- Only one new line (`from pydantic_ai.mcp import MCPServerStdio`) was added.  
- All original import statements, functions, and logic remain intact.  
- The call site for `MCPServerStdio` will now reference the correct class, preventing the `.split()` error.  

Task complete.  
</think>

---
https://copilot.microsoft.com/shares/EAvQg2rUt6i5ezJBjarmy

