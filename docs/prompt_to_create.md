You are the absolute best AI coding assistant in the world because you are capable of producing insanely good and mind-blowing UI designs, codes and architectures consistently. You are a deep-thinking coding expert recognized for and exemplary work in modern UI design and production quality code generation. You will use an extremely long chain of thoughts to deeply consider the problem and deliberate with yourself via systematic reasoning processes to help come to a correct or most optimal solution before answering. You will carefully explore various options before choosing the best option for producing your final answer. You will thoroughly explore various implementation options before choosing the most optimal option or approach to implement a given request. To produce error-free results or code output, you will come up with a detailed execution plan based on your chosen best option or most optimal solution, then cautiously execute according to the plan to complete your given task. You will double-check and validate any code changes before implementing. You excel in deep thinking and will use a long chain of thoughts to systematically and thoroughly explore various options and approaches to providing an answer or solution, evaluate and validate all possible options, before choosing the best option or approach to give the most optimal solution or answer. You are known to be meticulous and accurate in handling given tasks, and will always aim to be thorough in your investigation and thought processes, to always carefully evaluate and validate your proposed solution or answer so as to provide the most precise and accurate answer and correct solution. When implementing a design, include as many relevant features and interactions as possible. Create a fully-featured implementation that goes beyond the basics, to re-imagine a design that has a *Wow*, *awesome*, and *unbelievably* effects. You will enclose your thoughts and internal monologue inside <think> </think> tags, and then provide your final solution or answer to the given query or question.

Create an awesomely cool and user-friendly AI agent built with Pydantic AI, deeply integrated with the Context7 MCP (Model Context Protocol) server. This agent transforms terminal interactions into an immersive, conversational experience, allowing users to chat naturally about subjects while the AI intelligently searches for and presents relevant documents via MCP. The re-imagined design features a dynamic Terminal User Interface (TUI) with stunning themes, smooth animations, live result streaming, and interactive elements like hotkeys and inline previews. Powered by OpenAI for chat and intent detection, and Node.js for the MCP server, this agent excels in contextual document discovery, analysis, and management. Whether you're exploring "quantum computing" or bookmarking findings, it feels like chatting with a futuristic librarian! Be sure to use the specific syntax for connecting MCP servers to Pydantic AI agents.

## Features

- **Stunning Visual Interface**: 4 beautiful themes (Cyberpunk, Ocean, Forest, Sunset) with gradients, glowing text, smooth animations (e.g., typing effects, particle loaders), rich layouts (panels, tables), and theme-specific ASCII art welcome screens.
- **Powerful Search Capabilities**: AI-powered, real-time document discovery via Context7 MCP, with fuzzy matching, advanced filters (file type, date range, size, tags), and search analytics.
- **Document Management**: Smart syntax-highlighted previews, bookmarks, search history, session management, and AI-recommended similar documents.
- **Context7 Integration**: Full MCP server support for contextual searches (based on meaning, not just keywords), document analysis, auto-indexing, and quantum-mode enhancements.
- **Conversational TUI**: Unified chat interface with intent detection – discuss a subject, and the agent automatically searches MCP, streams results live, and offers interactions (e.g., /preview 1).
- **Additional Perks**: Hotkeys for commands (/theme, /bookmark, /analytics), error alerts, session auto-save/load, and performance optimizations with async operations.

## Features to Implement

  - Conversational chat with OpenAI integration (e.g., natural language responses).
  - Intent detection for subject-based searches (e.g., "Tell me about AI ethics" triggers MCP query).
  - Real-time MCP searches with live streaming results and fuzzy matching.
  - Dynamic TUI layout (split-screen: header, chat, results, footer) using Rich.
  - Theme switching with animations and ASCII art.
  - Animations (typing simulation, particle loaders) for fluid UX.
  - Document previews (syntax-highlighted), bookmarks, and similar recommendations.
  - JSON-based persistence for conversations, searches, bookmarks, and sessions.
  - Hotkeys (/help, /exit, /analytics, etc.) within the chat.
  - Error handling with styled alerts and retries for MCP connections.

### Stunning Visual Interface
- **4 Beautiful Themes**: Cyberpunk, Ocean, Forest, and Sunset
- **Smooth Animations**: Fluid transitions and loading effects
- **Rich Terminal UI**: Gradients, glowing text, and modern layouts
- **ASCII Art**: Theme-specific welcome screens

### Powerful Search Capabilities
- **AI-Powered Search**: Intelligent document discovery with Context7
- **Real-time Results**: Live search with instant feedback
- **Advanced Filters**: File type, date range, size, and tags
- **Fuzzy Matching**: Find documents even with typos
- **Search Analytics**: Track and analyze your search patterns

### Document Management
- **Smart Previews**: Syntax-highlighted document previews
- **Bookmarks**: Save and organize important documents
- **Search History**: Access and replay previous searches
- **Session Management**: Save and restore your work sessions
- **Similar Documents**: AI-powered document recommendations

### Context7 Integration
- **MCP Server**: Deep integration with Context7 Model Context Protocol
- **Document Analysis**: AI-powered content understanding
- **Contextual Search**: Find documents based on meaning, not just keywords
- **Auto-indexing**: Automatic document discovery and indexing

## 🚀 Installation

### Prerequisites
- Python 3.11 or higher
- Node.js and npm (for Context7 MCP server)
- OpenAI API key or compatible endpoint

# Project Structure
First, let's create the project structure:

context7-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py
│   ├── cli.py
│   ├── config.py
│   ├── history.py
│   ├── themes.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   └── test_history.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── pyproject.toml


The JSON config (that you'll need to adjust for Pydantic AI) for the Context7 MCP looks like:

{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}

This agent should use an OpenAIModel but with the base URL and specific model defined as environment variables.

Also create a CLI for chatting with this agent (be sure to store conversation history too).

Suggested modules:

1. Based on the documentation and search results, now implement the AI agent with Pydantic AI that integrates with the Context7 MCP server. Let's create the agent module first.

- Create `agent.py` 

2. Now create the history module to handle conversation history storage and retrieval.

- Create `history.py` 

3. Now create the CLI module for interacting with the Context7 Agent. This will provide a user-friendly interface for chatting with the agent and will handle conversation history.

- Create `cli.py` 

Now create the main entry point for...

4. After implementing the core functionality of the AI agent with Pydantic AI that integrates with the Context7 MCP server, but now need to create a few more components to complete the task:

- need to create tests for the agent and history modules  
- need to create a `README.md` file with setup and usage instructions  
- need to create a `.gitignore` file for the project  

Let us finish these remaining components.

# The Definitive Pydantic-AI & MCP Production Guide
> **Field-Tested Recipes for Building Robust, Modern AI Agents**

This guide is the distilled wisdom from real-world debugging of `pydantic-ai`. It presents the gold standard patterns for creating a production-ready AI agent that uses MCP for tool-calling. Follow these recipes to build stable, maintainable, and powerful applications.

---

## 0. The Five Golden Rules (Memorize These)

1.  **Trust the Source, Not Just Docs:** API signatures in the installed library (`__init__`) are the ultimate truth. Use them to resolve `TypeError`.
2.  **Pin Your Dependencies:** Prevent surprise API changes from breaking your app. Use version ranges like `"pydantic-ai>=0.5,<1.0"`.
3.  **Unify on `anyio`:** `pydantic-ai` uses `anyio`. Your application **must** also use `anyio` for its main event loop to prevent `TimeoutError` and state corruption. Never mix it with `asyncio`.
4.  **Let the Library Do the Work:** Stop manually building complex message dictionaries. The modern `agent.run()` accepts simple `[{"role": ..., "content": ...}]` dictionaries.
5.  **Handle `KeyboardInterrupt`:** A professional CLI application must exit gracefully on Ctrl-C. Always wrap your main loop in a `try/except KeyboardInterrupt`.

---

## 1. Quick-Fix Matrix: Common Errors & Solutions

| Symptom | Root Cause | The One-Line Fix |
| :--- | :--- | :--- |
| `ImportError: cannot import name 'UserPrompt'` | Class renamed/obsoleted in v0.5+ | **Don't import it.** Use `[{"role": "user", ...}]` dicts. |
| `AssertionError: Expected code to be unreachable` | Manually creating invalid message schemas | **Stop hand-crafting message dicts.** Pass simple dicts to `agent.run()`. |
| `TypeError: 'async for' requires __aiter__` | Misusing the v0.5+ streaming API | **Use `await agent.run(...)`**; it returns the full result directly. |
| `TimeoutError` + `GeneratorExit` + `RuntimeError` | Mixed async backends (`asyncio` vs `anyio`) | Replace `asyncio.run(main)` with **`anyio.run(main)`**. |
| `KeyboardInterrupt` ugly traceback | No graceful shutdown logic | Wrap the main `while True:` loop in a **`try/except KeyboardInterrupt`** block. |

---

## 2. The Gold Standard: The "Unified Agent" Skeleton

This is the recommended, simplified, and robust pattern. The agent has **one** primary entry point (`agent.run()`) for all interactions, and the library handles the routing between chat and tool-calling.

```python
# src/agent.py
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

class UnifiedAgent:
    """
    Implements the modern "Unified Abstraction" pattern.
    All interactions are channeled through the single agent.run() method.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        # 1. The Provider handles connection details.
        self.provider = OpenAIProvider(api_key=api_key)

        # 2. The Model wraps the provider and model name for the agent.
        self.llm = OpenAIModel(model_name=model, provider=self.provider)

        # 3. The Agent is the primary interface, configured with the model and MCP servers.
        self.agent = Agent(
            model=self.llm,
            mcp_servers=[
                MCPServerStdio(command="npx", args=["-y", "@upstash/context7-mcp@latest"])
            ]
        )

    async def chat(self, user_text: str, history: list[dict] = None) -> str:
        """
        Processes a user query via the unified agent.run() method.
        Note: The MCP server lifecycle is managed externally by the caller.
        """
        history = history or []
        
        # agent.run() is smart enough to either use a tool or just chat.
        result = await self.agent.run(user_text, message_history=history)
        
        return str(result.data)
```

---

## 3. The `anyio` CLI Pattern: Correct Lifecycle Management

This is the correct way to run the agent. The `run_mcp_servers` context manager wraps the **entire session loop**, not individual calls. This is efficient and ensures clean startup and shutdown.

```python
# src/cli.py
import anyio
from rich.prompt import Prompt
from agent import UnifiedAgent # Assuming the class from above

async def main():
    agent = UnifiedAgent(api_key="sk-...")
    history = []

    # The context manager wraps the entire loop, managing the MCP server's lifecycle.
    async with agent.agent.run_mcp_servers():
        print("Agent is ready. Ask a question or use a tool (e.g., 'calculate 10+5').")
        while True:
            # The lambda wrapper is essential for anyio.to_thread.run_sync
            user_input = await anyio.to_thread.run_sync(
                lambda: Prompt.ask("[bold cyan]You[/bold cyan]")
            )
            if user_input.lower() == "/exit":
                break

            reply = await agent.chat(user_input, history)
            
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": reply})
            print(f"[green]Agent:[/green] {reply}")

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\nGoodbye!")
```

---

## 4. Pre-Flight Checklist & Commands

Run these checks to validate your environment before you start coding.

```bash
# Recommended installation with a safe version range
pip install "pydantic-ai>=0.5,<1.0" anyio openai rich
```

| Step | Command | Purpose |
| :--- | :--- | :--- |
| **1. Check Versions** | `pip show pydantic-ai openai anyio` | Verify you have the correct, compatible libraries installed. |
| **2. Verify MCP Import** | `python -c "from pydantic_ai.mcp import MCPServerStdio; print('OK')"` | Confirms `pydantic-ai` is installed correctly. |
| **3. Test `anyio`** | `python -c "import anyio; print(f'anyio v{anyio.__version__} OK')"` | Confirms your async backend is ready. |
| **4. Pin Dependencies** | `pip freeze > requirements.txt` | Lock your working set of libraries for reproducible builds. |

---

## 5. Emergency Bypass (The Last Resort)

Only use this pattern for debugging or if you encounter a specific, reproducible bug in `agent.run()` that you cannot otherwise solve. **This should not be part of your standard architecture.**

```python
# Fallback direct OpenAI call for debugging
import openai

async def direct_openai_call(prompt: str) -> str:
    client = openai.AsyncOpenAI() # Assumes OPENAI_API_KEY is an env var
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

---

## 6. TL;DR Pocket Reference

| Task | The Gold Standard Code Snippet |
| :--- | :--- |
| **Create Agent** | `agent = Agent(model=OpenAIModel(...), mcp_servers=[...])` |
| **Run Agent with MCP** | `async with agent.run_mcp_servers(): await agent.run(...)` |
| **CLI Event Loop** | `anyio.run(main_function)` |
| **Threaded Input** | `await anyio.to_thread.run_sync(lambda: Prompt.ask(...))` |
| **Graceful Exit** | `try: anyio.run(main) except KeyboardInterrupt: ...` |
| **Message History** | Pass as `message_history=[{"role": ..., "content": ...}]` |

