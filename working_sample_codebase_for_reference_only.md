# working sample file: src/cli.py
```py
"""
Rich TUI interface for Context7 Agent with robust async handling.
"""

import asyncio
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
import anyio

from .agent import Context7Agent
from .themes import ThemeManager
from .config import config

class Context7CLI:
    """Production-ready TUI interface for Context7 Agent."""
    
    def __init__(self):
        self.console = Console()
        self.agent = Context7Agent()
        self.theme_manager = ThemeManager()
        self.current_conversation = "default"
        self.running = True
    
    async def initialize(self):
        """Initialize the CLI interface."""
        await self.agent.initialize()
        self.theme_manager.get_current_theme().print_banner()
    
    async def display_welcome(self):
        """Display welcome screen with theme selection."""
        theme = self.theme_manager.get_current_theme()
        theme.print_banner()
        
        # Theme selection
        self.console.print("\n[bold]Available Themes:[/bold]")
        for t in self.theme_manager.list_themes():
            marker = "✓" if t == self.theme_manager.current_theme else "○"
            self.console.print(f"  {marker} {t}")
        
        choice = await anyio.to_thread.run_sync(
            lambda: Prompt.ask(
                "\nSelect theme (or press Enter for default)",
                choices=self.theme_manager.list_themes(),
                default=self.theme_manager.current_theme
            )
        )
        self.theme_manager.set_theme(choice)
    
    async def chat_loop(self):
        """Main chat interaction loop with robust error handling."""
        self.console.print("\n[bold green]Context7 AI is ready! Type your questions below.[/bold green]")
        self.console.print("[dim]Commands: /theme, /history, /clear, /exit[/dim]\n")
        
        while self.running:
            try:
                # Get user input with proper async handling
                user_input = await anyio.to_thread.run_sync(
                    lambda: Prompt.ask("[bold cyan]You[/bold cyan]")
                )
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                    continue
                
                # Process message
                await self.process_message(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Shutting down gracefully...[/yellow]")
                self.running = False
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                self.console.print("[dim]Please try again or use /exit to quit.[/dim]")
    
    async def handle_command(self, command: str):
        """Handle special commands with async support."""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "/exit":
            self.running = False
            self.console.print("[yellow]Goodbye! 👋[/yellow]")
            
        elif cmd == "/theme":
            if len(parts) > 1:
                if self.theme_manager.set_theme(parts[1]):
                    self.console.print(f"[green]Theme changed to {parts[1]}[/green]")
                    self.theme_manager.get_current_theme().print_banner()
                else:
                    self.console.print("[red]Invalid theme[/red]")
            else:
                themes = ", ".join(self.theme_manager.list_themes())
                self.console.print(f"[cyan]Available themes: {themes}[/cyan]")
                
        elif cmd == "/history":
            conversations = self.agent.get_conversations()
            if conversations:
                table = Table(title="Conversation History")
                table.add_column("ID")
                table.add_column("Last Message")
                table.add_column("Count")
                
                for conv in conversations[:10]:
                    table.add_row(
                        conv["id"],
                        conv["last_message"][:19],
                        str(conv["message_count"])
                    )
                
                self.console.print(table)
            else:
                self.console.print("[yellow]No conversation history[/yellow]")
                
        elif cmd == "/clear":
            await self.agent.clear_history()
            self.console.print("[green]History cleared[/green]")
            
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
    
    async def process_message(self, message: str):
        """Process a user message with streaming and robust error handling."""
        theme = self.theme_manager.get_current_theme()
        
        # Create progress indicator
        with theme.create_progress_spinner() as progress:
            task = progress.add_task("Thinking...", total=None)
            
            # Process the message
            response_parts = []
            async for chunk in self.agent.chat_stream(message, self.current_conversation):
                if chunk["type"] == "content":
                    response_parts.append(chunk["data"])
                    progress.update(task, description=f"Processing... ({len(response_parts)} chars)")
                
                elif chunk["type"] == "complete":
                    progress.update(task, description="Complete!")
                
                elif chunk["type"] == "error":
                    self.console.print(f"[red]Error: {chunk['data']}[/red]")
                    return
            
            # Display response
            full_response = "".join(response_parts)
            if full_response.strip():
                theme.console.print("\n[bold green]Assistant:[/bold green]")
                theme.console.print(Panel(full_response, border_style=theme.colors['secondary']))
            else:
                theme.console.print("[yellow]No response generated.[/yellow]")
    
    async def run(self):
        """Run the CLI application with proper async handling."""
        try:
            await self.initialize()
            await self.display_welcome()
            await self.chat_loop()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Goodbye! Thanks for using Context7 AI.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Fatal error: {e}[/red]")
            sys.exit(1)

async def main():
    """Main entry point with proper async handling."""
    cli = Context7CLI()
    await cli.run()

if __name__ == "__main__":
    anyio.run(main)

```

# working sample file: src/agent.py
```py
"""
Production-ready AI agent with Pydantic AI and MCP integration.
This version implements a simplified RAG pattern that works with Context7 MCP server's
actual output format (human-readable markdown responses).
*** THIS VERSION INCLUDES DIAGNOSTIC PRINT STATEMENTS FOR DEBUGGING ***
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

# Import rich for styled, clear diagnostic printing
from rich import print as rprint

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import config
from .history import HistoryManager

logger = logging.getLogger(__name__)

class Context7Agent:
    """Production-ready AI agent implementing a simplified RAG pattern for Context7 MCP."""
    
    def __init__(self):
        """Initialize with correct Pydantic AI v0.5+ patterns."""
        self.provider = OpenAIProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        
        self.model = OpenAIModel(
            model_name=config.openai_model,
            provider=self.provider
        )
        
        self.mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"]
        )
        
        self.agent = Agent(
            model=self.model,
            mcp_servers=[self.mcp_server],
            system_prompt="""
            You are a helpful AI research assistant. Your task is to provide a clear and comprehensive answer to the user's question based on the provided context documents. Synthesize the information from the various documents into a single, coherent response. If the context is insufficient to answer the question, state that clearly.
            """
        )
        
        self.history = HistoryManager()
    
    async def initialize(self):
        """Initialize the agent and load history."""
        await self.history.load()
    
    async def chat_stream(
        self, 
        message: str, 
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat responses using a simplified RAG pipeline for Context7 MCP.
        """
        try:
            rprint("[bold yellow]--- Starting RAG Pipeline ---[/bold yellow]")
            async with self.agent.run_mcp_servers():
                # =====================================================================
                # == STEP 1: FORMULATE SEARCH QUERY                                  ==
                # =====================================================================
                rprint("[bold yellow][DEBUG-STEP-1A][/bold yellow] Formulating search query from user message...")
                query_formulation_prompt = f"""
                Based on the user's request, what is the optimal, concise search query for the Context7 documentation database?
                The user's request is: "{message}"
                Return ONLY the search query string, and nothing else.
                """
                
                query_formulation_agent = Agent(model=self.model)
                query_result = await query_formulation_agent.run(query_formulation_prompt)
                search_query = str(query_result.data).strip().strip('"')

                rprint(f"[bold yellow][DEBUG-STEP-1B][/bold yellow] Formulated Search Query: [cyan]'{search_query}'[/cyan]")

                if not search_query:
                    raise ValueError("LLM failed to formulate a search query.")
                
                # =====================================================================
                # == STEP 2: EXECUTE THE TOOL AND GET DIRECT RESPONSE                ==
                # =====================================================================
                search_prompt = f"search for documentation about: {search_query}"
                rprint(f"[bold yellow][DEBUG-STEP-2A][/bold yellow] Executing tool call with prompt: [cyan]'{search_prompt}'[/cyan]")
                
                retrieval_result = await self.agent.run(search_prompt)
                response_content = str(retrieval_result.data).strip()
                
                rprint(f"[bold green][DEBUG-STEP-2B][/bold green] Received response from Context7 MCP:")
                rprint(f"[dim white]{response_content[:200]}...[/dim white]")
                
                if not response_content:
                    rprint("[bold red][DEBUG-FAIL][/bold red] Empty response received from MCP server")
                    yield {
                        "type": "content",
                        "data": "I could not find any relevant information in the Context7 knowledge base to answer your question.",
                        "timestamp": datetime.now().isoformat()
                    }
                    return
                
                # =====================================================================
                # == STEP 3: STREAM THE RESPONSE                                     ==
                # =====================================================================
                rprint("[bold green][DEBUG-STEP-3A][/bold green] Streaming response to user...")
                rprint("[bold green]--- RAG Pipeline Succeeded ---[/bold green]")

                yield {
                    "type": "content",
                    "data": response_content,
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.history.add_message(conversation_id or "default", "user", message)
                await self.history.add_message(conversation_id or "default", "assistant", response_content)
                
                yield {
                    "type": "complete",
                    "data": response_content,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Agent RAG pipeline error: {e}")
            rprint(f"[bold red][DEBUG-FATAL-ERROR][/bold red] An unexpected exception occurred in the RAG pipeline: {e}")
            yield {
                "type": "error",
                "data": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using MCP tools with proper error handling."""
        try:
            async with self.agent.run_mcp_servers():
                search_prompt = f"Search the Context7 knowledge base for documents about: {query}"
                result = await self.agent.run(search_prompt)
                response_text = str(result.data)
                
                # Return the response as a single document
                return [{
                    "title": f"Search Results for: {query}",
                    "content": response_text,
                    "source": "Context7 MCP",
                    "score": 1.0
                }]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [{"title": "Search Error", "content": f"Unable to search documents: {str(e)}", "source": "Error", "score": 0.0}]
    
    def get_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversation histories."""
        return self.history.get_conversations()
    
    async def clear_history(self, conversation_id: Optional[str] = None):
        """Clear conversation history."""
        await self.history.clear(conversation_id)

```

# working sample file: src/config.py
```py
"""
Configuration management for Context7 Agent.
Handles environment variables and MCP server configuration.
*** UPDATED to use relative path for history. ***
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Config(BaseSettings):
    """Application configuration with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CONTEXT7_",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Required fields
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # Optional fields with defaults
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    mcp_config_path: Path = Field(
        default_factory=lambda: Path.home() / ".context7" / "mcp.json",
        description="Path to MCP configuration"
    )
    # UPDATED: Changed to a relative path as requested.
    history_path: Path = Field(
        default_factory=lambda: Path("data/history.json"),
        description="Path to conversation history"
    )
    max_history: int = Field(
        default=1000,
        description="Maximum conversation history entries"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure the new 'data' directory for history is created.
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP server configuration."""
        config = {
            "mcpServers": {
                "context7": {
                    "command": "npx",
                    "args": ["-y", "@upstash/context7-mcp@latest"],
                    "env": {}
                }
            }
        }
        
        if not self.mcp_config_path.exists():
            with open(self.mcp_config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        return config

# Global config instance
config = Config()

```

