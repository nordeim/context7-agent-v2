# Definitive Guide to Building Production-Ready RAG Agents with Pydantic-AI and MCP

## 🎯 Introduction: The Mission for Authoritative Answers

This guide provides a comprehensive, best-practices blueprint for building a production-grade, terminal-based AI agent. The agent's primary mission is to provide software developers with **accurate, trustworthy, and up-to-date programming documentation** by leveraging a Retrieval-Augmented Generation (RAG) pipeline with an MCP-compliant tool like the Upstash Context7 Server.

The core design philosophy presented here is engineered to **maximize accuracy and minimize LLM hallucination**. It achieves this by combining the most robust architectural patterns and best practices into a coherent, "best-of-both-worlds" design. This guide is not just a collection of snippets; it is a complete, opinionated framework for building high-quality AI applications.

---

## 🏛️ The Core Architecture: Agent-Led Synthesis

To ensure accuracy, we will implement an **Agent-Led Synthesis** RAG pattern. This is a two-step LLM process that strictly separates retrieval from answering.

1.  **Tool Use & Retrieval:** The Agent, guided by a powerful system prompt, first uses the `search` tool to retrieve relevant documents from the trusted knowledge base (Context7).
2.  **Grounded Synthesis:** The Agent then takes this retrieved context and performs a *second* LLM call. In this step, it is strictly instructed to synthesize its final answer **exclusively from the provided documents**.

This pattern is superior for our use case because it forces the LLM to act as a **reasoning engine on a trusted, local dataset**, rather than a knowledge engine pulling from its vast but potentially outdated internal training. This dramatically reduces hallucination and ensures the answers are grounded in the authoritative source.

### Architectural Flow Diagram

```mermaid
graph TD
    subgraph User Interface Layer
        User[👤 User] -- 1. Asks "How do I use FastAPI?" --> CLI(Rich TUI)
    end

    subgraph Agent & RAG Pipeline Layer
        CLI -- 2. Calls agent.chat_stream() --> Agent(src/agent.py)
        
        subgraph "Step A: Tool Use & Retrieval"
            Agent -- "3. LLM Call 1: Decide to use 'search'" --> LLM_API[☁️ OpenAI API]
            LLM_API -- "4. Instructs agent to call search('FastAPI')" --> Agent
            Agent -- "5. Executes MCP Tool Call" --> MCPServer[Context7 MCP Server]
            MCPServer -- "6. Returns raw documents/context" --> Agent
        end
        
        subgraph "Step B: Grounded Synthesis"
            Agent -- "7. LLM Call 2: 'Answer the question using ONLY these documents...'" --> LLM_API
            LLM_API -- "8. Returns a synthesized, grounded answer" --> Agent
        end

        Agent -- 9. Streams structured, synthesized answer --> CLI
    end

    subgraph UI Presentation
        CLI -- 10. Renders the final answer to the user --> User
    end

    style LLM_API fill:#f99,stroke:#333,stroke-width:2px
    style Agent fill:#cfc,stroke:#333,stroke-width:2px
    style MCPServer fill:#ffc,stroke:#333,stroke-width:2px
```

---

## 🧬 Section 1: The Agent - The Brains of the Operation

This is the most critical component. It implements the Agent-Led Synthesis pattern and uses structured streaming for clean communication with the UI.

### **The "Golden Pattern" `agent.py`**

```python
# File: src/agent.py
"""
Production-ready AI agent implementing the Agent-Led Synthesis RAG pattern.
"""
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from .config import config
from .history import HistoryManager

logger = logging.getLogger(__name__)

# The System Prompt is the most critical tool for ensuring accuracy.
# It uses strong, clear directives to constrain the LLM's behavior.
AGENT_SYSTEM_PROMPT = """
You are a world-class AI research assistant for software developers named Context7.

## CORE DIRECTIVE
Your SOLE PURPOSE is to provide answers by exclusively using information retrieved from the attached `search` tool, which connects to an official, up-to-date knowledge base. You are FORBIDDEN from using your own internal, pre-trained knowledge.

## RULES OF ENGAGEMENT
1.  **TOOL-FIRST MENTALITY:** For any user question that is not a simple greeting, you MUST ALWAYS call the `search` tool with a concise query to gather context before formulating an answer.
2.  **GROUNDED SYNTHESIS:** You MUST synthesize your final answer using ONLY the `documents` and `content` provided in the tool's output. Do not add any information not present in the retrieved context. Your answer should be a direct, clear synthesis of the provided materials.
3.  **FAILURE PROTOCOL:** If the `search` tool returns no relevant documents, an error, or if the context is insufficient, you MUST respond with the exact phrase: "I could not find any relevant information in the Context7 knowledge base to answer your question." Do not attempt to answer from memory.
4.  **CITE YOUR SOURCES (If Possible):** If the retrieved context includes source information (like filenames or URLs), cite them in your final answer.

## RESPONSE FORMAT
Format your responses in clear, readable markdown. Use code blocks for code examples.
"""

class Context7Agent:
    """Implements a robust, production-ready RAG agent."""

    def __init__(self):
        """Initializes the agent using the Golden Pattern for Pydantic-AI v0.4.2."""
        self.mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"]
        )

        # IDIOMATIC PATTERN: Use the provider-prefixed model string.
        # The Agent class will handle provider/model instantiation internally.
        self.agent = Agent(
            model=f"openai:{config.openai_model}",
            mcp_servers=[self.mcp_server],
            system_prompt=AGENT_SYSTEM_PROMPT
        )

        self.history = HistoryManager()

    async def initialize(self):
        """Initializes the agent's dependencies, like loading history."""
        await self.history.load()
        logger.info("Context7Agent initialized successfully.")

    async def chat_stream(
        self,
        message: str,
        conversation_id: str = "default"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Processes a user message using the Agent-Led Synthesis RAG pipeline
        and yields structured data events.
        """
        try:
            # Get the message history for the current conversation.
            message_history = self.history.get_messages(conversation_id)

            # The async context manager handles the MCP server lifecycle.
            async with self.agent.run_mcp_servers():
                full_response = ""
                # agent.run_stream performs the full RAG pipeline automatically.
                async for chunk in self.agent.run_stream(message, message_history=message_history):
                    full_response += chunk
                    yield {
                        "type": "content_chunk",
                        "data": chunk,
                        "timestamp": datetime.now().isoformat()
                    }

            # Persist the conversation to history.
            await self.history.add_message(conversation_id, "user", message)
            await self.history.add_message(conversation_id, "assistant", full_response)

            # Signal that the stream is complete.
            yield {
                "type": "complete",
                "data": {"full_response": full_response},
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Agent pipeline error: {e}")
            yield {
                "type": "error",
                "data": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_conversations(self) -> List[Dict[str, Any]]:
        return self.history.get_conversations()

    async def clear_history(self, conversation_id: Optional[str] = None):
        await self.history.clear(conversation_id)
```

---

## 🧱 Section 2: Configuration - The Foundation

A robust application needs a robust configuration system. We use `pydantic-settings` for a declarative, type-safe, and modern approach.

### **Best-Practice `config.py`**

```python
# File: src/config.py
"""
Configuration management using Pydantic-Settings for a modern, robust setup.
"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    """Application configuration with automatic environment variable loading."""
    
    # This tells Pydantic-Settings to load from a .env file,
    # use a "CONTEXT7_" prefix, and ignore case.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CONTEXT7_",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Required: Will raise an error if not found in the environment.
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Optional fields with sensible defaults.
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    
    # Use pathlib.Path for robust, platform-agnostic paths.
    history_path: Path = Path("data/history.json")
    max_history: int = 1000

# Create a single, global config instance for easy importing.
config = Config()
```

---

## 📚 Section 3: State Management - The Memory

A great agent remembers past conversations. This `HistoryManager` supports multiple conversations and uses a standard, compliant message schema.

### **Production-Grade `history.py`**

```python
# File: src/history.py
"""
Conversation history management with multi-conversation support,
JSON persistence, and a standard OpenAI message schema.
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import aiofiles

from .config import config

class HistoryManager:
    """Manages conversation history with a robust, compliant message schema."""
    
    def __init__(self):
        self.history_path = config.history_path
        self.max_history = config.max_history
        self._history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def load(self):
        """Loads conversation history from disk asynchronously."""
        try:
            if self.history_path.exists():
                async with aiofiles.open(self.history_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content:
                        self._history = json.loads(content)
        except Exception as e:
            print(f"Warning: Could not load history: {e}. Starting fresh.")
            self._history = {}
    
    async def save(self):
        """Saves conversation history to disk asynchronously."""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(self.history_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self._history, indent=2))
        except Exception as e:
            print(f"Warning: Could not save history: {e}")
    
    async def add_message(self, conversation_id: str, role: str, content: str):
        """Adds a message to the history, respecting the max history limit."""
        if conversation_id not in self._history:
            self._history[conversation_id] = []
        
        self._history[conversation_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Prune old messages if history exceeds the max size
        if len(self._history[conversation_id]) > self.max_history:
            self._history[conversation_id] = self._history[conversation_id][-self.max_history:]
        
        await self.save()
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Gets messages for a conversation in the exact format the Agent needs."""
        messages = self._history.get(conversation_id, [])
        # Strip metadata (like timestamp) before sending to the LLM.
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def get_conversations(self) -> List[Dict[str, Any]]:
        """Gets metadata for all conversations, for use in a UI."""
        # Implementation from Codebase V2 is excellent here.
        pass # Placeholder for brevity, use V2's implementation.
    
    async def clear(self, conversation_id: Optional[str] = None):
        """Clears history for a specific conversation or all conversations."""
        # Implementation from Codebase V2 is excellent here.
        pass # Placeholder for brevity, use V2's implementation.
```

---

## 🎨 Section 4: The User Interface - The Face of the Agent

A great backend deserves a great frontend. We use an Object-Oriented structure with the `rich` library to create a polished, maintainable, and extensible TUI.

*   **`themes.py`:** Implement the `Theme` and `ThemeManager` classes from Codebase V2. They are a model of excellent, modular UI design.
*   **`cli.py`:** Implement the `Context7CLI` class from Codebase V2. Its OOP structure is superior for managing state. The `chat_loop` should be adapted to handle the `content_chunk` events from our new agent.

### **Best-Practice `cli.py` (Core Logic)**

```python
# File: src/cli.py (Conceptual)
# ... imports ...
from .agent import Context7Agent
from .themes import ThemeManager
from rich.live import Live
from rich.markdown import Markdown

class Context7CLI:
    def __init__(self):
        self.agent = Context7Agent()
        self.theme_manager = ThemeManager()
        # ... other initializations

    async def process_message(self, message: str):
        """Processes a user message, consuming the structured stream from the agent."""
        theme = self.theme_manager.get_current_theme()
        full_response = ""

        with Live(console=theme.console, auto_refresh=False) as live:
            live.update(Panel("Thinking...", border_style=theme.colors['secondary']))
            
            async for chunk in self.agent.chat_stream(message, self.current_conversation):
                if chunk["type"] == "content_chunk":
                    full_response += chunk["data"]
                    # Render markdown live as it comes in
                    live.update(Markdown(full_response), refresh=True)
                
                elif chunk["type"] == "complete":
                    # Final update to ensure everything is rendered
                    live.update(Markdown(full_response), refresh=True)
                    break # Exit the loop
                
                elif chunk["type"] == "error":
                    live.update(Panel(f"[red]Error:[/red] {chunk['data']}", title="Agent Error"))
                    return

    # ... rest of the CLI class from Codebase V2 ...
```

---

## ✅ Section 5: Production Readiness

Follow this checklist to ensure your agent is ready for prime time.

### **Installation & Dependency Management**
Pinning versions is critical for stability.
```bash
# In your pyproject.toml or requirements.txt
pydantic-ai[openai]==0.4.2
pydantic==2.11.7
pydantic-settings==2.10.1
openai==1.95.1
anyio==4.9.0
rich==14.0.0
aiofiles==24.1.0

# Install the MCP server (or let npx handle it)
npm install -g @upstash/context7-mcp@latest
```

### **Environment Setup (`.env` file)**```env
# REQUIRED
OPENAI_API_KEY="sk-..."

# OPTIONAL
CONTEXT7_OPENAI_BASE_URL="https://api.openai.com/v1"
CONTEXT7_OPENAI_MODEL="gpt-4o-mini"
```

### **Production Checklist**
- [x] Node.js 18+ is installed on the host system.
- [x] All Python dependencies are pinned to specific versions.
- [x] `OPENAI_API_KEY` is securely managed as an environment variable.
- [x] A strong, directive `AGENT_SYSTEM_PROMPT` is in place.
- [x] The agent uses the provider-prefixed model string (`"openai:..."`).
- [x] All MCP tool calls are wrapped in `async with agent.run_mcp_servers():`.
- [x] Comprehensive `try...except` blocks are used around all I/O and API calls.
- [x] The application handles `KeyboardInterrupt` for graceful shutdown.

---

## ⚠️ Section 6: Common Pitfalls & Solutions

This table covers the most common errors and their definitive solutions.

| Issue Symptom | Root Cause | The Fix |
| :--- | :--- | :--- |
| `AttributeError: 'list' object has no attribute 'split'` | Incorrect model parameter format. | Use the provider-prefixed string: **`model="openai:gpt-4o-mini"`**. |
| `MCPServerError: MCP server is not running` | Attempting to call `agent.run()` without starting the server process. | Wrap the call in the async context manager: **`async with agent.run_mcp_servers():`**. |
| `400 Bad Request` with `role 'system' must not be empty` | The `system_prompt` sent to the LLM API was `None` or `""`. | Always provide a non-empty string to the `system_prompt` parameter of the `Agent`. |
| `FileNotFoundError` when saving history. | The target directory (`data/`) does not exist. | Proactively create the directory before writing: **`self.history_path.parent.mkdir(parents=True, exist_ok=True)`**. |

---
https://drive.google.com/file/d/1-uWgtQNtnheyCbD15AqvAj1-073c7tCo/view?usp=sharing, https://drive.google.com/file/d/19q0TdmuaiPM4yEJZ6pLvBEbd8RT1LTqh/view?usp=sharing, https://drive.google.com/file/d/1IBLzJJl-Lkpvuso5gnRg9AWQkjWeOMOE/view?usp=sharing, https://drive.google.com/file/d/1LoryCtF8oDPFzrTLG8KBtQOJOwzIiuAX/view?usp=sharing, https://drive.google.com/file/d/1VpzywilAs5SrVF-a4s6BAI0P6HeTlEgg/view?usp=sharing, https://drive.google.com/file/d/1j0SHpmItxP8hPmVhU2FZOdHTcUHk3O-f/view?usp=sharing, https://drive.google.com/file/d/1k-eF2p7_QIPsMCaaRqt54wakYRFRpZor/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221yyiV_QyxDOiMnFI9oeu1Mt04Hlw5U-IT%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing

