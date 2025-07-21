$ python3 verify_mcp.py
🔍 Verifying Context7 MCP integration...
Context7 Documentation MCP Server running on stdio
✅ MCP server running
INFO:httpx:HTTP Request: POST https://api.moonshot.ai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://api.moonshot.ai/v1/chat/completions "HTTP/1.1 200 OK"
Failed to fetch documentation. Please try again later. Error code: 404
INFO:httpx:HTTP Request: POST https://api.moonshot.ai/v1/chat/completions "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: POST https://api.moonshot.ai/v1/chat/completions "HTTP/1.1 200 OK"
✅ Query executed successfully
📋 Result:
Based on the official pydantic-ai documentation, here are the key aspects of MCP (Model Context Protocol) tool calling in pydantic-ai:

## MCP Tool Calling in Pydantic-AI

### Installation
```bash
pip install "pydantic-ai-slim[mcp]"
```

### Basic MCP Server Setup
The official documentation shows how to create MCP servers using FastMCP:

```python
from mcp.server.fastmcp import FastMCP
from pydantic_ai import Agent

server = FastMCP('Pydantic AI Server')
server_agent = Agent(
    'anthropic:claude-3-5-haiku-latest', 
    system_prompt='always reply in rhyme'
)

@server.tool()
async def poet(theme: str) -> str:
    """Poem generator"""
    r = await server_agent.run(f'write a poem about {theme}')
    return r.output

if __name__ == '__main__':
    server.run()
```

### MCP Client Integration

#### 1. Standard I/O Connection
```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio('python', ['mcp_server.py'])
agent = Agent('openai:gpt-4o', toolsets=[server])

async def main():
    async with agent:
        result = await agent.run('Generate a poem about nature')
    print(result.output)
```

#### 2. Streamable HTTP Connection
```python
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')
agent = Agent('openai:gpt-4o', toolsets=[server])
```

#### 3. Server-Sent Events (SSE)
```python
from pydantic_ai.mcp import MCPServerSSE

weather_server = MCPServerSSE(
    url='http://localhost:3001/sse',
    tool_prefix='weather'  # Prevents naming conflicts
)
```

### Advanced MCP Features

#### Custom Tool Call Processing
```python
from pydantic_ai.mcp import CallToolFunc, MCPServerStdio
from pydantic_ai.tools import RunContext

async def process_tool_call(
    ctx: RunContext[int],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """Custom tool call processor that injects dependencies."""
    return await call_tool(name, tool_args, {'deps': ctx.deps})

server = MCPServerStdio(
    'python', 
    ['mcp_server.py'], 
    process_tool_call=process_tool_call
)
```

#### MCP Sampling Support
MCP servers can make LLM calls back through the client:

```python
# Server-side (with sampling)
from pydantic_ai.models.mcp_sampling import MCPSamplingModel

@server.tool()
async def image_generator(ctx: Context, subject: str, style: str) -> str:
    prompt = f'{subject=} {style=}'
    result = await ctx.session.create_message(
        [SamplingMessage(role='user', content=TextContent(type='text', text=prompt))],
        max_tokens=1_024,
        system_prompt='Generate an SVG image as per the user input',
    )
    # Process result...
```

#### Client-side Sampling Callback
```python
async def sampling_callback(context, params):
    # Handle LLM requests from the server
    response_content = 'Generated response...'
    return CreateMessageResult(
        role='assistant',
        content=TextContent(type='text', text=response_content),
        model='fictional-llm',
    )

async with ClientSession(read, write, sampling_callback=sampling_callback) as session:
    # Use session...
```

### Tool Naming and Conflict Resolution
```python
# Use prefixes to avoid conflicts
weather_server = MCPServerSSE(
    url='http://localhost:3001/sse',
    tool_prefix='weather'
)

calculator_server = MCPServerSSE(
    url='http://localhost:3002/sse',
    tool_prefix='calc'
)

agent = Agent('openai:gpt-4o', toolsets=[weather_server, calculator_server])
# Tools become: 'weather_get_data', 'calc_get_data'
```

### Observability
```python
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
logfire.instrument_mcp()
```

These examples represent the official pydantic-ai documentation for MCP tool calling functionality. The framework provides comprehensive support for MCP servers and clients, including advanced features like sampling, custom processing, and conflict resolution.

