import os
from typing import Optional, List, Dict, Any

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Config
from .history import HistoryManager


class Context7Agent:
    """
    Production-ready AI agent implementing a robust RAG pattern, deeply integrated with Context7 MCP.
    All chat and tool-calling happens via agent.run(), enforcing strict RAG: answers ONLY from retrieved context.
    """

    def __init__(self, config: Optional[Config] = None):
        config = config or Config.load()
        self.config = config

        # Provider
        self.provider = OpenAIProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
        )

        # Model
        self.model = OpenAIModel(
            model_name=config.openai_model,
            provider=self.provider,
        )

        # MCP server (Context7)
        self.mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"],
        )

        # Gold-standard RAG system prompt
        self.agent = Agent(
            model=self.model,
            mcp_servers=[self.mcp_server],
            system_prompt=config.rag_system_prompt
        )

        # History manager
        self.history = HistoryManager(filepath=config.history_file)

    async def initialize(self):
        """Load persisted history and prepare agent."""
        await self.history.load_async()

    async def chat(
        self, user_text: str, message_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Processes a user query via the unified agent.run() method.
        MCP server lifecycle must be managed by the caller.
        """
        message_history = message_history or []
        result = await self.agent.run(user_text, message_history=message_history)
        return str(result.data)

    async def chat_stream(
        self, user_text: str, message_history: Optional[List[Dict]] = None
    ):
        """
        Streams the chat response (for live/animated UI).
        """
        message_history = message_history or []
        async for chunk in self.agent.run_stream(user_text, message_history=message_history):
            yield chunk

    def get_history(self):
        return self.history.history

    async def save_history(self):
        await self.history.save_async()
