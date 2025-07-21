# Troubleshooting Guide: Pydantic-AI & Context7 MCP Server Integration

## 📋 Executive Summary
This guide chronicles the complete troubleshooting journey from initial errors to a fully working Context7 MCP integration with pydantic-ai. It serves as a reference for developers facing similar challenges.

## 🎯 Problem Timeline & Solutions

### **Stage 1: Initial Error - `'list' object has no attribute 'split'`**
**Symptom**: Application crashes with AttributeError during model initialization
**Root Cause**: Incorrect model parameter format in Agent constructor
**Error Location**: `pydantic-ai/agent.py:573` in `infer_model()`

**Solution Applied**:
```python
# ❌ WRONG
Agent(model="gpt-4o-mini", ...)

# ✅ CORRECT
Agent(model="openai:gpt-4o-mini", ...)
```

**Lesson Learned**: Pydantic-ai expects model strings in format `{provider}:{model_name}`

### **Stage 2: MCP Server Not Running**
**Symptom**: `MCP server is not running: MCPServerStdio(...)`
**Root Cause**: Incorrect MCP server lifecycle management

**Solution Applied**:
```python
# Use async context manager for proper lifecycle
async with agent.run_mcp_servers([mcp_server]):
    result = await agent.run(query)
```

### **Stage 3: Empty System Prompt Rejection**
**Symptom**: `Invalid request: the message at position 0 with role 'system' must not be empty`
**Root Cause**: API rejecting empty system prompts

**Solution Applied**:
```python
# Ensure non-empty system prompt
system_prompt = config.rag_system_prompt or "fallback prompt..."
```

### **Stage 4: Missing Model Declaration**
**Symptom**: Runtime error due to incomplete model initialization
**Root Cause**: Missing `OpenAIModel` instantiation

**Solution Applied**:
```python
# Complete model initialization
self.model = OpenAIModel(
    model_name=config.openai_model,
    provider=self.provider,
)
```

## 🔧 Complete Working Implementation

### **Final Architecture Pattern**
```python
class WorkingAgent:
    def __init__(self):
        # 1. Provider setup
        self.provider = OpenAIProvider(api_key="...")
        
        # 2. Model setup
        self.model = OpenAIModel(model_name="gpt-4o-mini", provider=self.provider)
        
        # 3. MCP server
        self.mcp_server = MCPServerStdio("npx", ["-y", "@upstash/context7-mcp@latest"])
        
        # 4. Agent with correct format
        self.agent = Agent(
            "openai:gpt-4o-mini",
            mcp_servers=[self.mcp_server],
            system_prompt="Your non-empty prompt here..."
        )
```

## 📚 Common Pitfalls & Solutions

### **1. Version Compatibility Matrix**
| Component | Version | Notes |
|-----------|---------|--------|
| pydantic-ai | ≥0.4.2, <1.0 | API stabilized at 0.4.2 |
| Node.js | ≥18.0 | Required for MCP server |
| @upstash/context7-mcp | latest | Context7 MCP package |

### **2. Environment Setup Checklist**
```bash
# 1. Install dependencies
pip install "pydantic-ai>=0.4.2,<1.0" anyio openai rich

# 2. Install Context7 MCP
npm install -g @upstash/context7-mcp@latest

# 3. Verify installations
python -c "from pydantic_ai import Agent; print('OK')"
npx -y @upstash/context7-mcp@latest --help
```

### **3. Error-Free Configuration**
```python
# Environment variables
OPENAI_API_KEY=sk-...          # Required
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
OPENAI_MODEL=gpt-4o-mini       # Optional
```

## 🚀 Production Deployment Guide

### **Step 1: Pre-Flight Validation**
```bash
#!/bin/bash
# validate.sh
python -c "
import pydantic_ai, openai, anyio
print(f'✅ pydantic-ai {pydantic_ai.__version__}')
print(f'✅ openai {openai.__version__}')
print(f'✅ anyio {anyio.__version__}')
"
```

### **Step 2: Health Check**
```python
# health_check.py
import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

async def health_check():
    agent = Agent("openai:gpt-4o-mini", mcp_servers=[
        MCPServerStdio("npx", ["-y", "@upstash/context7-mcp@latest"])
    ])
    
    async with agent.run_mcp_servers():
        result = await agent.run("health check")
        print("✅ System healthy:", result.data)

asyncio.run(health_check())
```

## 📖 Troubleshooting Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `'list' object has no attribute 'split'` | Wrong model format | Use `"openai:gpt-4o-mini"` |
| `MCP server is not running` | Missing context manager | Wrap with `async with agent.run_mcp_servers([...])` |
| `system prompt must not be empty` | Empty system prompt | Provide non-empty prompt |
| `ImportError: AsyncGenerator` | Missing import | Add `from typing import AsyncGenerator` |

## 🎯 Key Takeaways

1. **Always use provider prefix**: `"openai:gpt-4o-mini"` not `"gpt-4o-mini"`
2. **Non-empty system prompts**: Always provide fallback prompts
3. **MCP lifecycle**: Use `run_mcp_servers()` context manager
4. **Error handling**: Wrap all async operations with proper exception handling
5. **Version pinning**: Lock dependencies to prevent surprise changes

## ✅ Success Indicators

When working correctly, you should see:
- ✅ `Context7 Documentation MCP Server running on stdio`
- ✅ Successful HTTP requests to your LLM provider
- ✅ Context7-specific responses based on retrieved documentation
- ✅ Proper shutdown on exit
