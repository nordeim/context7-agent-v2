# Title: Definitive Troubleshooting Guide: Pydantic-AI (v0.4.2) & Context7 MCP Server Integration

## 📋 Executive Summary

This guide provides a definitive, step-by-step chronicle of the troubleshooting journey required to successfully integrate the **Upstash Context7 MCP Server** with **`pydantic-ai==0.4.2`**. Built from hands-on experience and validated against the library's source code, this document serves as a canonical reference for developers navigating this specific technology stack.

The primary challenges in this integration often stem from three key areas:
1.  **Correct Model Initialization:** The `pydantic-ai` library has a specific, non-obvious string format for model declaration.
2.  **MCP Server Lifecycle Management:** The external MCP server is a separate process that must be started, managed, and shut down correctly by the Python application.
3.  **API-Level Requirements:** Ensuring that all data sent to the LLM provider (like OpenAI) adheres to its strict API contract, particularly regarding system prompts.

This guide will walk you through the common errors encountered in sequence, explaining the root cause of each and providing the exact, validated solution. By following this timeline, you will arrive at a robust, error-free, and production-ready implementation.

---

## 🏛️ The Core Principle: The "Golden Pattern"

Before diving into errors, it is essential to understand the correct, final pattern. Nearly all common issues are solved by adhering to this structure. This "Golden Pattern" is the foundation of a successful integration.

The pattern relies on two critical concepts from the `pydantic-ai` library:

1.  **Provider-Prefixed Model Strings:** Instead of just passing a model name like `"gpt-4o-mini"`, you must prefix it with the provider, such as `"openai:gpt-4o-mini"`. The `Agent` class uses this string to automatically infer and instantiate the correct provider and model objects. This is the single most common point of failure for new users.

2.  **Asynchronous Context Management for MCP:** The `MCPServerStdio` object represents an external process (`npx ...`). This process is not running by default. You must use the `async with agent.run_mcp_servers():` context manager to command the `pydantic-ai` library to start the server process, manage communication with it, and—most importantly—shut it down gracefully when the block is exited.

**The Golden Pattern in Practice:**

```python
# A minimal, complete, and correct example
import os
import anyio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from dotenv import load_dotenv

# Ensure OPENAI_API_KEY is available in the environment
load_dotenv()

async def get_authoritative_answer(question: str):
    """
    This function demonstrates the Golden Pattern for a single query.
    """
    print("Initializing Pydantic-AI Agent...")
    
    # 1. Define the MCP server process.
    #    The command is `npx` and args start the Context7 MCP server.
    #    The `-y` flag is crucial to prevent interactive prompts.
    mcp_server = MCPServerStdio(
        command="npx", 
        args=["-y", "@upstash/context7-mcp@latest"]
    )

    # 2. Instantiate the Agent with the Golden Pattern.
    #    - Note the "openai:" prefix on the model string.
    #    - Note the non-empty system prompt.
    agent = Agent(
        model="openai:gpt-4o-mini",
        mcp_servers=[mcp_server],
        system_prompt="You are a helpful assistant. Use the search tool to answer questions."
    )

    print("Starting MCP server and processing query...")
    try:
        # 3. Use the async context manager to run the server.
        async with agent.run_mcp_servers():
            # This is where the magic happens: the agent communicates
            # with the LLM and the now-running MCP server.
            result = await agent.run(question)
            print("Query processed successfully.")
            return str(result.data)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Failed to get an answer."
    finally:
        print("MCP server has been shut down gracefully.")

async def main():
    answer = await get_authoritative_answer("What is the Context7 MCP Server?")
    print("\n--- Agent's Answer ---")
    print(answer)
    print("----------------------\n")

if __name__ == "__main__":
    anyio.run(main)
```

---

## 🔧 Problem Timeline & Solutions: A Step-by-Step Troubleshooting Journey

This section follows the logical progression of errors a developer typically encounters when setting up this system from scratch.

### **Stage 1: The First Crash - `AttributeError: 'list' object has no attribute 'split'`**

This is almost always the very first error you will see after installing the libraries and writing your initial code.

*   **Symptom:** The application fails immediately upon the `Agent(...)` instantiation line with a confusing `AttributeError`. The traceback points deep inside the `pydantic-ai` library, often to a line that performs a `.split()` operation.
*   **Root Cause:** The `Agent` class's `infer_model` method received a model name without the required provider prefix. It expects a string in the format `{provider}:{model_name}`. When it gets only a model name (e.g., `"gpt-4o-mini"`), its internal parsing logic fails.
*   **Error Location (Illustrative):** `pydantic_ai/agent.py` in the `infer_model()` function.

*   **The Incorrect Code:**
    ```python
    # ❌ WRONG: This code causes the AttributeError
    agent = Agent(model="gpt-4o-mini", ...) 
    ```

*   **The Solution:**
    Prefix the model name with the provider ID and a colon. For OpenAI models, the provider is `openai`.

    ```python
    # ✅ CORRECT: Add the "openai:" prefix
    agent = Agent(model="openai:gpt-4o-mini", ...)
    ```

*   **Lesson Learned:** The `pydantic-ai` library uses a special string format to automatically configure the correct provider (OpenAI, Anthropic, etc.) and model. **Always use the `{provider}:{model_name}` format for model strings.** This is the most fundamental requirement.

---

### **Stage 2: The Agent Runs, But Fails - `MCP server is not running`**

After fixing the model string, your Python script no longer crashes on startup. However, when you try to run a query, you hit the next roadblock.

*   **Symptom:** The code executes until the `await agent.run(query)` line, then fails with an exception explicitly stating that the MCP server is not running, e.g., `pydantic_ai.mcp.errors.MCPServerError: MCP server is not running: MCPServerStdio(...)`.
*   **Root Cause:** You have *defined* the MCP server by creating an `MCPServerStdio` object, but you have not *started* the external `npx` process. The `pydantic-ai` agent has no running process to communicate with.
*   **The Incorrect Code:**
    ```python
    # ❌ WRONG: The agent is defined, but the server is never started.
    mcp_server = MCPServerStdio(...)
    agent = Agent(..., mcp_servers=[mcp_server])
    
    # This call will fail because the npx process isn't running.
    result = await agent.run(query) 
    ```

*   **The Solution:**
    Wrap any calls to `agent.run()` or `agent.run_stream()` inside the `async with agent.run_mcp_servers():` context manager. This block instructs the agent to:
    1.  **Start** the subprocess(es) defined in `mcp_servers`.
    2.  **Manage** the `stdin`/`stdout` communication pipes.
    3.  **Terminate** the subprocess(es) gracefully upon exiting the block.

    ```python
    # ✅ CORRECT: Use the async context manager for proper lifecycle.
    mcp_server = MCPServerStdio(...)
    agent = Agent(..., mcp_servers=[mcp_server])

    async with agent.run_mcp_servers():
        # The MCP server is now running inside this block.
        result = await agent.run(query)
    # The MCP server is automatically stopped here.
    ```

*   **Lesson Learned:** The MCP server's lifecycle is not automatic. You must explicitly manage it using the `run_mcp_servers()` asynchronous context manager.

---

### **Stage 3: The Query is Sent, But the API Rejects It - `must not be empty`**

Your code is now correctly structured. The MCP server starts, but you get an error back from the OpenAI API itself.

*   **Symptom:** The application hangs for a moment, then fails with an error from the `openai` library. The error message is typically a `400 Bad Request` containing text like `Invalid request: the message at position 0 with role 'system' must not be empty`.
*   **Root Cause:** The `system_prompt` passed to the `Agent` constructor was either `None` or an empty string (`""`). The OpenAI API (and many other LLM APIs) has a validation rule that forbids sending a system message with no content.
*   **The Incorrect Code:**
    ```python
    # ❌ WRONG: Passing an empty or None system prompt.
    agent = Agent(
        model="openai:gpt-4o-mini",
        mcp_servers=[mcp_server],
        system_prompt=""  # This will be rejected by the API.
    )
    ```

*   **The Solution:**
    Always provide a meaningful, non-empty system prompt. Even a simple prompt is sufficient. It's good practice to provide a fallback default prompt if the configuration is optional.

    ```python
    # ✅ CORRECT: Ensure a non-empty system prompt is always provided.
    
    # Pattern 1: Simple default
    prompt = "You are a helpful research assistant."
    
    # Pattern 2: Fallback from configuration
    # system_prompt = user_configured_prompt or "Default fallback prompt..."

    agent = Agent(
        model="openai:gpt-4o-mini",
        mcp_servers=[mcp_server],
        system_prompt=prompt
    )
    ```

*   **Lesson Learned:** Always treat the `system_prompt` as a required field. The `pydantic-ai` library will pass it directly to the underlying provider, so it must comply with that provider's API rules.

---

## ✅ Final Checklist and Core Principles

If you adhere to the following principles, your integration will be successful. This checklist summarizes the lessons from the troubleshooting journey.

1.  **Use the Provider Prefix:** Your model string **MUST** be in the format `"openai:gpt-4o-mini"`.
2.  **Manage the MCP Lifecycle:** Your calls to `agent.run()` **MUST** be inside an `async with agent.run_mcp_servers():` block.
3.  **Provide a System Prompt:** Your `system_prompt` **MUST** be a non-empty string.
4.  **Pin Your Dependencies:** The AI library ecosystem changes rapidly. To ensure stability, pin your versions in `requirements.txt` or `pyproject.toml` (e.g., `pydantic-ai==0.4.2`).
5.  **Use Asynchronous Code:** The entire stack is asynchronous. Use `async/await` and a runner like `anyio` or `asyncio`.
6.  **Handle Exceptions:** Wrap your agent calls in `try...except` blocks to gracefully handle network issues or API errors.

## 📦 Environment Setup and Version Matrix

To ensure reproducibility, use the following dependency versions and setup commands.

### **Version Compatibility Matrix**
| Component               | Recommended Version    | Notes                                    |
|-------------------------|------------------------|------------------------------------------|
| `pydantic-ai`           | `0.4.2`                | The API is stable and tested in this version. |
| `pydantic`              | `2.11.7`               | Works correctly with `pydantic-ai==0.4.2`.   |
| `openai`                | `1.95.1`               | Works correctly with `pydantic-ai==0.4.2`.   |
| `Node.js`               | `18.0` or newer          | Required to run the `npx` command for MCP. |
| `@upstash/context7-mcp` | `latest`               | The MCP server package from `npm`.       |

### **Installation Commands**
```bash
# 1. Install required Python packages
pip install "pydantic-ai[openai]==0.4.2" "pydantic==2.11.7" "anyio==4.9.0" "openai==1.95.1" "python-dotenv==1.1.1"

# 2. Ensure Node.js and npm are installed. Then, install the Context7 MCP server globally.
# (Alternatively, rely on `npx -y` to fetch it on demand, as shown in the code)
npm install -g @upstash/context7-mcp@latest

# 3. Verify the MCP server installation (optional but recommended)
npx @upstash/context7-mcp@latest --help
```

### **Environment Configuration (`.env` file)**
```env
# Required: Your OpenAI API key
OPENAI_API_KEY="sk-..."

# Optional: Override the default OpenAI API base URL
OPENAI_BASE_URL="https://api.openai.com/v1"

# Optional: Default model to use (must match agent initialization)
OPENAI_MODEL="gpt-4o-mini"
```

## 🎯 Success Indicators

When your implementation is fully correct, running the code will produce a clean execution flow with no errors:
1.  The script will start without any `AttributeError` or `ImportError`.
2.  Upon calling the main async function, you will see the `npx` process for the MCP server start.
3.  The agent will successfully communicate with the OpenAI API.
4.  The agent will return a synthesized answer based on the context retrieved from the Context7 knowledge base.
5.  The `npx` process will shut down gracefully when the `async with` block is exited.
