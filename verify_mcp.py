#!/usr/bin/env python3
"""
Complete verification that Context7 MCP integration works end-to-end.
"""
import asyncio
import logging
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

logging.basicConfig(level=logging.INFO)

async def verify_integration():
    """Verify complete Context7 MCP integration."""
    print("🔍 Verifying Context7 MCP integration...")
    
    try:
        # Create MCP server
        mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"]
        )
        
        # Create agent with correct format
        agent = Agent(
            "openai:gpt-4o-mini",
            mcp_servers=[mcp_server],
            system_prompt="You are a helpful assistant that uses Context7 to answer questions."
        )
        
        # Test query
        query = "n8n json format"
        
        # Execute with proper lifecycle management
        async with agent.run_mcp_servers([mcp_server]):
            print("✅ MCP server running")
            result = await agent.run(query)
            print("✅ Query executed successfully")
            print("📋 Result:")
            print(result.data)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(verify_integration())
