#!/usr/bin/env python3
"""
Minimal test to verify Context7 MCP integration works.
"""
import asyncio
import logging
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

async def test_context7_mcp():
    """Test Context7 MCP integration with the exact working pattern."""
    logger.info("Testing Context7 MCP integration...")
    
    # Create MCP server exactly as in working examples
    mcp_server = MCPServerStdio(
        command="npx",
        args=["-y", "@upstash/context7-mcp@latest"]
    )
    
    # Create agent with correct model format
    agent = Agent(
        "openai:gpt-4o-mini",
        mcp_servers=[mcp_server],
        system_prompt="You are a helpful assistant."
    )
    
    user_query = "n8n json format"
    
    # Use the exact working pattern
    async with agent.run_mcp_servers([mcp_server]):
        logger.info(f"Executing query: {user_query}")
        result = await agent.run(user_query)
        print("✅ Success! Result:")
        print(result.data)

if __name__ == "__main__":
    asyncio.run(test_context7_mcp())
