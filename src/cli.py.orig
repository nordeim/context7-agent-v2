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
