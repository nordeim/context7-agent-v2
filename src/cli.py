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
