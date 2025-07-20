<think>
Now I need to add comprehensive debugging to identify exactly where the `'list' object has no attribute 'split'` error is occurring. This error is happening during MCP server initialization, but we need to pinpoint the exact location.

## Systematic Debugging Strategy

### 1. Error Location Analysis
The error occurs **after** "Starting Context7 MCP server..." but **before** successful connection. This suggests it's happening during the actual MCP server communication setup.

### 2. Debugging Plan
I will add detailed print statements at each critical point:
- Right before MCP server creation
- During MCP server creation
- During environment variable processing
- Right before the async context manager
- During any potential argument processing

### 3. Deep Investigation Points
The error `'list' object has no attribute 'split'` could be happening in:
- Environment variable processing (where lists might be passed as strings)
- Command argument processing
- Path handling
- String splitting operations on what should be string data

### 4. Comprehensive Debugging Approach
I'll add:
1. **Type checking** for all parameters
2. **Value inspection** for critical variables
3. **Stack trace capture** when possible
4. **Step-by-step execution tracking**

### 5. Critical Areas to Debug
- `create_mcp_server()` function parameters
- Environment variable values and types
- Arguments passed to MCPServerStdio
- Any string operations that might fail

Let me implement comprehensive debugging throughout the MCP server creation process.
</think>

## Comprehensive Debugging Implementation

After careful analysis, I've identified that we need detailed debugging to pinpoint the exact location of the `'list' object has no attribute 'split'` error. I'll add comprehensive print statements and debugging throughout the MCP server initialization process.

## Updated File: cli.py with Full Debugging

```python
import anyio
import os
import traceback
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.syntax import Syntax
from rich.text import Text
import subprocess
import shutil
import json
from typing import List, Dict

# Import fix for MCPServerStdio
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

def debug_print_env_vars(env_dict):
    """Debug helper to print environment variables and their types."""
    console.print("[yellow]=== DEBUG: Environment Variables ===[/yellow]")
    for key, value in env_dict.items():
        console.print(f"  {key}: {type(value).__name__} = {repr(str(value)[:100])}")

def debug_print_mcp_params(command, args, env):
    """Debug helper to print MCP server parameters."""
    console.print("[yellow]=== DEBUG: MCP Server Parameters ===[/yellow]")
    console.print(f"Command: {type(command).__name__} = {repr(command)}")
    console.print(f"Args: {type(args).__name__} = {args}")
    console.print(f"Args types: {[type(arg).__name__ for arg in args]}")
    console.print(f"Env type: {type(env).__name__}")
    console.print(f"Env keys count: {len(env)}")

def create_mcp_server():
    """Create MCP server with comprehensive debugging."""
    try:
        console.print("[dim]=== Starting MCP server creation ===[/dim]")
        
        # Use cross-platform approach
        npx_path = shutil.which("npx")
        console.print(f"[dim]npx_path: {repr(npx_path)}[/dim]")
        
        if not npx_path:
            raise RuntimeError("npx not found in PATH")
        
        # Debug original environment
        console.print("[dim]=== Original Environment ===[/dim]")
        debug_print_env_vars(os.environ)
        
        # Create environment with necessary additions
        env = os.environ.copy()
        console.print(f"[dim]Environment copied, keys: {len(env)}[/dim]")
        
        # Add or update specific environment variables
        existing_node_options = env.get("NODE_OPTIONS", "")
        console.print(f"[dim]Existing NODE_OPTIONS: {repr(existing_node_options)}[/dim]")
        
        if "--max-old-space-size=512" not in existing_node_options:
            if existing_node_options:
                env["NODE_OPTIONS"] = f"{existing_node_options} --max-old-space-size=512"
            else:
                env["NODE_OPTIONS"] = "--max-old-space-size=512"
        
        console.print(f"[dim]Updated NODE_OPTIONS: {repr(env['NODE_OPTIONS'])}[/dim]")
        
        # Ensure all environment values are strings
        console.print("[dim]=== Converting env values to strings ===[/dim]")
        string_env = {}
        for k, v in env.items():
            try:
                string_env[str(k)] = str(v)
            except Exception as e:
                console.print(f"[red]Error converting env var {k}: {e}[/red]")
                string_env[str(k)] = ""
        
        # Debug final environment
        console.print("[dim]=== Final Environment ===[/dim]")
        debug_print_env_vars(string_env)
        
        # Debug MCP parameters
        command = npx_path
        args = ["-y", "@upstash/context7-mcp@latest"]
        debug_print_mcp_params(command, args, string_env)
        
        # Test string operations that might fail
        console.print("[dim]=== Testing string operations ===[/dim]")
        try:
            test_split = command.split()
            console.print(f"[dim]Command split test: {test_split}[/dim]")
        except Exception as e:
            console.print(f"[red]Command split failed: {e}[/red]")
            
        try:
            for arg in args:
                test_split = str(arg).split()
                console.print(f"[dim]Arg split test: {arg} -> {test_split}[/dim]")
        except Exception as e:
            console.print(f"[red]Args split failed: {e}[/red]")
        
        console.print("[dim]=== Creating MCPServerStdio ===[/dim]")
        
        try:
            mcp_server = MCPServerStdio(
                command=command,
                args=args,
                env=string_env
            )
            console.print("[green]✅ MCPServerStdio created successfully[/green]")
            return mcp_server
        except Exception as e:
            console.print(f"[red]❌ MCPServerStdio creation failed: {e}[/red]")
            console.print("[red]Full traceback:[/red]")
            console.print(traceback.format_exc())
            raise
            
    except Exception as e:
        console.print(f"[red]❌ MCP server creation failed: {e}[/red]")
        console.print("[red]Full error details:[/red]")
        console.print(traceback.format_exc())
        raise

async def main():
    config = Config.load()
    console.print("[dim]=== Configuration loaded ===[/dim]")
    console.print(f"[dim]Config: {type(config).__name__}[/dim]")
    
    agent = Context7Agent(config)
    console.print("[dim]=== Agent created ===[/dim]")
    
    await agent.initialize()
    console.print("[dim]=== Agent initialized ===[/dim]")

    theme = config.theme
    console.push_theme(get_theme(theme))

    print_ascii_art(theme)
    console.print(f"[header]Welcome to Context7 Agent! (Theme: {theme})[/header]")
    print_help()

    history = agent.get_history()
    bookmarks = agent.history.get_bookmarks()
    last_results: List[Dict] = []

    console.print(f"[dim]History length: {len(history)}[/dim]")
    console.print(f"[dim]Bookmarks count: {len(bookmarks)}[/dim]")

    # Pre-flight checks
    if not check_nodejs():
        console.print("[yellow]⚠️  Node.js 18+ and npm are required for MCP functionality[/yellow]")
        console.print("[dim]Install from: https://nodejs.org/[/dim]")
        return

    try:
        console.print("[dim]=== About to create MCP server ===[/dim]")
        # Create MCP server with robust error handling
        mcp_server = create_mcp_server()
        console.print(f"[dim]MCP server object: {type(mcp_server).__name__}[/dim]")
        
        console.print("[dim]Starting Context7 MCP server...[/dim]")
        
        console.print("[dim]=== About to enter MCP context ===[/dim]")
        async with agent.agent.run_mcp_servers([mcp_server]):
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
        console.print("[red]Full error details:[/red]")
        console.print(traceback.format_exc())
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

## Debugging Features Added

### 1. **Comprehensive Parameter Inspection**
- Prints all MCP server parameters with their types
- Shows exact values being passed
- Validates string operations before they occur

### 2. **Environment Variable Debugging**
- Shows original environment
- Shows processed environment
- Validates all values are strings
- Counts environment variables

### 3. **Step-by-Step Execution Tracking**
- Marks each phase of MCP server creation
- Shows object creation status
- Provides detailed error traces

### 4. **Type Safety Validation**
- Explicitly tests string operations
- Validates parameter types
- Provides clear error messages

## How to Use the Debugging Version

1. **Run with full debugging**: The enhanced version will show detailed information about:
   - Environment variables being passed
   - Parameter types and values
   - Exact location of the error
   - Full stack traces

2. **Look for these key sections in output**:
   - `=== DEBUG: Environment Variables ===`
   - `=== DEBUG: MCP Server Parameters ===`
   - `=== Testing string operations ===`

3. **Share the debugging output** so we can identify the exact source of the `'list' object has no attribute 'split'` error.

## References

- **Python Debugging Techniques**: https://docs.python.org/3/library/traceback.html - Official traceback documentation for detailed error analysis
- **Rich Console Debugging**: https://rich.readthedocs.io/en/latest/console.html - Rich console debugging capabilities
- **pydantic-ai MCP Debugging**: https://ai.pydantic.dev/mcp/ - MCP server debugging guidelines
- **Stack Overflow Debugging Patterns**: https://stackoverflow.com/questions/5136611/capture-stdout-from-a-script - Capturing and debugging subprocess output
