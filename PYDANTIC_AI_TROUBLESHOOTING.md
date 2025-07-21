## 🚀 **Context7 MCP + Pydantic-AI 0.4.2 Production Guide**

### **1. The Golden Pattern (Copy-Paste Ready)**

```python
# Minimal working pattern
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

agent = Agent(
    "openai:gpt-4o-mini",  # Critical: provider prefix
    mcp_servers=[MCPServerStdio("npx", ["-y", "@upstash/context7-mcp@latest"])],
    system_prompt="Your non-empty prompt here"
)

async with agent.run_mcp_servers():
    result = await agent.run("your question")
```

### **2. Installation Commands**

```bash
# Required dependencies
pip install "pydantic-ai>=0.4.2,<1.0" anyio openai rich

# MCP server
npm install -g @upstash/context7-mcp@latest

# Verify installation
npx -y @upstash/context7-mcp@latest --help
```

### **3. Environment Setup**

```bash
# .env file
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
OPENAI_MODEL=gpt-4o-mini                   # Optional
```

### **4. Common Pitfalls & Solutions**

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Model format** | `'list' object has no attribute 'split'` | Use `"openai:gpt-4o-mini"` |
| **Empty prompt** | API rejection | Ensure system_prompt is non-empty |
| **MCP lifecycle** | Server not running | Wrap with `async with agent.run_mcp_servers([...])` |
| **Missing imports** | ImportError | Use `from typing import List, Dict, Optional` |

### **5. Production Patterns**

#### **A. Basic Usage**
```python
async def ask_question(question: str) -> str:
    agent = Agent(
        "openai:gpt-4o-mini",
        mcp_servers=[MCPServerStdio("npx", ["-y", "@upstash/context7-mcp@latest"])]
    )
    
    async with agent.run_mcp_servers():
        result = await agent.run(question)
        return str(result.data)
```

#### **B. With Error Handling**
```python
async def robust_ask(question: str) -> str:
    try:
        async with agent.run_mcp_servers():
            result = await agent.run(question)
            return str(result.data)
    except Exception as e:
        return f"Error: {str(e)}"
```

#### **C. With Streaming**
```python
async def stream_response(question: str):
    async with agent.run_mcp_servers():
        async for chunk in agent.run_stream(question):
            yield str(chunk)
```

### **6. Debugging Commands**

```bash
# Quick health check
python -c "from pydantic_ai import Agent; print('✅ OK')"

# Test MCP server
python -c "from pydantic_ai.mcp import MCPServerStdio; print('✅ MCP OK')"

# Full integration test
python -c "
import asyncio
from pydantic_ai import Agent
async def test():
    agent = Agent('openai:gpt-4o-mini', mcp_servers=[MCPServerStdio('npx', ['-y', '@upstash/context7-mcp@latest'])])
    async with agent.run_mcp_servers():
        print(await agent.run('test'))
asyncio.run(test())
"
```

### **7. Production Checklist**

- [ ] Node.js 18+ installed
- [ ] @upstash/context7-mcp@latest installed globally
- [ ] OPENAI_API_KEY set in environment
- [ ] System prompt is non-empty
- [ ] Model uses provider prefix
- [ ] Async context manager used
- [ ] Error handling implemented
- [ ] KeyboardInterrupt handled

### **8. Performance Tips**

- **Keep system prompts concise** - reduces token usage
- **Use `run_mcp_servers()` once per session** - not per query
- **Pin dependency versions** - prevents API breakages
- **Handle KeyboardInterrupt** - graceful shutdown

### **9. Common Integration Patterns**

#### **With FastAPI**
```python
from fastapi import FastAPI
from pydantic_ai import Agent

app = FastAPI()
agent = Agent("openai:gpt-4o-mini", mcp_servers=[...])

@app.post("/ask")
async def ask(question: str):
    async with agent.run_mcp_servers():
        return {"answer": await agent.run(question)}
```

#### **With CLI**
```python
import anyio
from rich.prompt import Prompt

async def main():
    agent = Agent("openai:gpt-4o-mini", mcp_servers=[...])
    async with agent.run_mcp_servers():
        while True:
            question = await anyio.to_thread.run_sync(
                lambda: Prompt.ask("You")
            )
            if question == "/exit":
                break
            result = await agent.run(question)
            print(result.data)

anyio.run(main)
```

## 🎯 **Success Verification**

When working correctly, you'll see:
```
✅ Node.js v22.16.0 found
✅ Context7 MCP server connected successfully
You: your question
[Context7-based response using retrieved documentation]
```
