## 🎯 **Root Cause Identified!**

After extensive debugging, I found the exact source of the error! The issue is **not** in the MCP server creation itself, but in how the **agent is trying to parse the model name** within the pydantic-ai library.

### 🔍 **Error Analysis**

The error occurs at this line in the pydantic-ai library:
```python
provider, model_name = model.split(':', maxsplit=1)
```

The problem is that **a list is being passed as the model parameter** instead of a string, causing the `'list' object has no attribute 'split'` error.

### 🚨 **The Real Issue**

Looking at the debug output, the error happens **inside** the agent's `run_mcp_servers()` method, specifically when it tries to **infer the model** from the agent configuration.

### 🛠️ **The Fix**

We need to modify how the agent is initialized. The issue is in the `Context7Agent` class where the model might be receiving a list instead of a string.

## Updated File: agent.py

```python
import os
from typing import Optional, List, Dict, Any
import logging
import traceback

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
    Production-ready AI agent implementing a robust RAG pattern, deeply integrated with Context7 MCP.
    All chat and tool-calling happens via agent.run(), enforcing strict RAG: answers ONLY from retrieved context.
    """

    def __init__(self, config: Optional[Config] = None):
        config = config or Config.load()
        self.config = config

        # Debug model configuration
        print(f"[DEBUG] Model from config: {repr(config.openai_model)}")
        print(f"[DEBUG] Model type: {type(config.openai_model).__name__}")

        # Ensure model is a string
        if isinstance(config.openai_model, list):
            model_name = config.openai_model[0] if config.openai_model else "gpt-4o-mini"
            print(f"[DEBUG] Fixed model from list to: {model_name}")
        else:
            model_name = str(config.openai_model)

        # Provider
        self.provider = OpenAIProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
        )

        # Model - ensure it's a string
        self.model = OpenAIModel(
            model_name=model_name,
            provider=self.provider,
        )

        # Agent - MCP servers will be attached at runtime
        self.agent = Agent(
            model=self.model,
            system_prompt=config.rag_system_prompt
        )

        # History manager
        self.history = HistoryManager(filepath=config.history_file)

    async def initialize(self):
        """Load persisted history and prepare agent."""
        try:
            await self.history.load_async()
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            raise

    def create_mcp_server(self) -> MCPServerStdio:
        """Create MCP server with proper error handling."""
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
        """
        Processes a user query via the unified agent.run() method.
        MCP server lifecycle is managed internally for each call.
        """
        if not user_text.strip():
            return "I didn't receive any input. Please try again."

        message_history = message_history or []
        
        try:
            mcp_server = self.create_mcp_server()
            
            async with self.agent.run_mcp_servers([mcp_server]):
                logger.debug(f"Processing query: {user_text}")
                result = await self.agent.run(user_text, message_history=message_history)
                return str(result.data)
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            print(f"[DEBUG] Chat error details: {traceback.format_exc()}")
            return f"I encountered an error: {str(e)}. Please check your configuration and try again."

    async def chat_stream(
        self, user_text: str, message_history: Optional[List[Dict]] = None
    ):
        """
        Streams the chat response (for live/animated UI).
        MCP server lifecycle is managed internally for each call.
        """
        if not user_text.strip():
            yield "I didn't receive any input. Please try again."
            return

        message_history = message_history or []
        
        try:
            mcp_server = self.create_mcp_server()
            
            async with self.agent.run_mcp_servers([mcp_server]):
                logger.debug(f"Streaming query: {user_text}")
                async for chunk in self.agent.run_stream(user_text, message_history=message_history):
                    yield chunk
                    
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

## Updated File: config.py (with additional validation)

```python
import os
from typing import List
from pydantic import BaseModel, Field
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
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    openai_model: str = Field(default="gpt-4o-mini")
    rag_system_prompt: str = Field(default=DEFAULT_PROMPT)
    theme: str = Field(default="cyberpunk")
    history_file: str = Field(default=os.path.expanduser("~/.context7_history.json"))

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
        
        # Ensure model is a string, not a list
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if isinstance(model, list):
            model = model[0] if model else "gpt-4o-mini"
        
        return cls(
            openai_api_key=api_key,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_model=str(model),
            rag_system_prompt=os.getenv("RAG_SYSTEM_PROMPT", DEFAULT_PROMPT),
            theme=theme,
            history_file=os.getenv("CONTEXT7_HISTORY_FILE", os.path.expanduser("~/.context7_history.json"))
        )
```

## 🔧 **Key Fixes Applied**

### 1. **Root Cause Fix**
The error was coming from **pydantic-ai's model inference** when it tried to parse the model name. The fix ensures the model is always a string.

### 2. **Type Safety**
- Added explicit string conversion for model names
- Added validation to handle potential list inputs
- Added debugging output for model configuration

### 3. **Enhanced Error Handling**
- Added comprehensive error tracking
- Added traceback output for debugging
- Added specific handling for model configuration issues

## 🧪 **Testing Instructions**

Run the updated code:
```bash
python3 -m src.cli
```

The application should now start correctly without the `'list' object has no attribute 'split'` error.
