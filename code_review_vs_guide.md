# Analysis Report: `src/agent.py` vs Cheat Sheet Guide

## Methodology
We performed a side-by-side comparison of your `Context7Agent` implementation in `src/agent.py` against each section of the cheat-sheet guide.  
For each deviation, we consulted the installed PydanticAI v0.4.2 source code and official docs (ai.pydantic.dev) to determine whether the guide or your code reflects the true, supported API and recommended pattern.

---

## 0. The Five Golden Rules

| Rule                                                     | Guide Requirement                                                                                             | Actual Code                                                                               | Verdict                                                                                         |
|----------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **1. Trust the Source, Not Just Docs**                   | Use real API signatures from the installed library to resolve mismatches.                                      | You construct `Agent(model=…, system_prompt=…)` exactly as the `__init__` signature shows. | ✔ Compliant: Code uses true constructor parameters.                                            |
| **2. Pin Your Dependencies**                             | Ranges like `pydantic-ai>=0.5,<1.0`.                                                                           | You run v0.4.2 (pinned via requirements).                                                 | ⚠ Guide targets v0.5+, but code correctly pins v0.4.2 for your environment.                    |
| **3. Unify on `anyio`**                                  | Application must use `anyio` to drive event loop; do not mix with `asyncio`.                                  | `Context7Agent` methods are `async def` and use `async with`, but event loop choice is external. | ➖ Library code agnostic. You rely on the caller (CLI) to use `anyio.run()`.                    |
| **4. Let the Library Do the Work**                       | Pass simple `[{"role":..,"content":..}]` dicts to `agent.run()`.                                               | You pass `user_text` and optional `message_history` list of dicts.                         | ✔ Compliant: No handcrafted part structures.                                                   |
| **5. Handle `KeyboardInterrupt`**                        | Wrap main loop in `try/except KeyboardInterrupt`.                                                             | Not present in `Context7Agent` (library class).                                           | ➖ Not applicable: graceful shutdown belongs in CLI, not core agent class.                      |

---

## 1. Quick-Fix Matrix

| Symptom                                                 | Guide Fix                                                                                      | Actual Code                                                                                                                               | Verdict                                                                                                        |
|---------------------------------------------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `ImportError: cannot import name 'UserPrompt'`          | Don’t import it. Use plain dicts.                                                              | No import of `UserPrompt`.                                                                                                                  | ✔ Compliant.                                                                                                   |
| `AssertionError: Expected code to be unreachable`       | Stop hand-crafting message schemas.                                                            | You rely solely on `agent.run()`.                                                                                                           | ✔ Compliant.                                                                                                   |
| `TypeError: 'async for' requires __aiter__`             | *In v0.5+* streaming changed—use `await agent.run()` instead.                                   | You do `async for chunk in agent.run_stream(...)`: in v0.4.2 this is correct behavior.                                                        | ⚠ Guide is for v0.5+—in v0.4.x `run_stream` returns an async iterator. Your code is correct for v0.4.2.       |
| `TimeoutError` + `GeneratorExit` + `RuntimeError`       | Mix of backends—replace `asyncio.run(main)` with `anyio.run(main)`.                              | Not in library code.                                                                                                                         | ➖ Not applicable here.                                                                                        |
| `KeyboardInterrupt` ugly traceback                      | Wrap main loop in `try/except KeyboardInterrupt`.                                              | Not in library code.                                                                                                                         | ➖ Handled in CLI layer.                                                                                       |

---

## 2. The Gold Standard “Unified Agent” Skeleton

**Guide Skeleton**  
```python
self.agent = Agent(
    model=self.llm,
    mcp_servers=[ MCPServerStdio(...) ]
)
```

**Your Code**  
```python
self.agent = Agent(
    model=self.model,
    system_prompt=config.rag_system_prompt
    # MCP servers attached at runtime
)
```

| Difference                                  | Guide Says                                  | Your Code                                  | Which Is Correct?                                                                                                   |
|---------------------------------------------|----------------------------------------------|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **MCP registration**                        | Static in constructor via `mcp_servers` list | Dynamically via `async with self.agent.run_mcp_servers([…])` | Both patterns are supported. PydanticAI v0.4.2 lets you pass `mcp_servers` up front or defer attachment at runtime. |
| **System prompt location**                  | Registered on `Agent()` call                 | You pass `system_prompt` separately         | Both valid. Docs show `Agent(system_prompt=…)` is correct.                                                           |
| **Naming**                                  | `UnifiedAgent`                               | `Context7Agent`                             | Naming is arbitrary.                                                                                                 |

---

## 3. The `anyio` CLI Pattern

**Guide CLI Pattern**  
```python
async with agent.agent.run_mcp_servers():
    while True:
        user_input = await anyio.to_thread.run_sync(...)
        reply = await agent.chat(...)
```

**Your Usage**  
```python
async with self.agent.run_mcp_servers([mcp_server]):
    result = await self.agent.run(...)
```

| Difference                  | Guide Pattern                                            | Your Code                                                 | Verdict                                                                                                 |
|-----------------------------|----------------------------------------------------------|-----------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Scope of `run_mcp_servers`** | Wrap entire session loop                                 | Wrap each `chat()` or `chat_stream()` call individually    | Both work. Wrapping once reduces overhead; per-call context manager is simpler and functionally valid. |
| **Server list argument**    | `run_mcp_servers()` without args (server list in constructor) | `run_mcp_servers([mcp_server])` at call site               | Both are supported. PydanticAI API accepts servers at init or runtime.                                   |

---

## 4. Pre-Flight Checklist & Commands

**Guide**  
```bash
pip install "pydantic-ai>=0.5,<1.0" anyio openai rich
```

**Your Environment**  
```
pydantic-ai               0.4.2
anyio                     4.9.0
openai                    1.95.1
rich                      14.0.0
```

| Item                             | Guide Recommendation                     | Your Installed Versions         | Verdict                                                                                       |
|----------------------------------|------------------------------------------|---------------------------------|-----------------------------------------------------------------------------------------------|
| **PydanticAI version**           | `>=0.5,<1.0`                             | `0.4.2`                         | Code pins to v0.4.2. Guide is forward-looking; your code is correct for your locked environment. |
| **anyio**                        | anyio (compat v3+)                       | 4.9.0                           | ✔ Compatible.                                                                                |
| **openai**                       | openai latest                            | 1.95.1                          | ✔ Compatible.                                                                                |
| **rich**                         | rich                                     | 14.0.0                          | ✔ Compatible.                                                                                |

---

## 5. Emergency Bypass

**Guide** offers a fallback direct OpenAI call for debugging. Your code has no fallback.  
- **Verdict:** Not required in production agent class. It’s an optional debugging recipe, so omission is acceptable.

---

## 6. TL;DR Pocket Reference

| Task                          | Guide Snippet                                              | Your Code                                          | Verdict                                                                                   |
|-------------------------------|------------------------------------------------------------|----------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Create Agent**              | `Agent(model=OpenAIModel(...), mcp_servers=[…])`            | `Agent(model=OpenAIModel(...), system_prompt=…)`   | Both valid instantiations; M C P can be static or deferred.                               |
| **Run Agent with MCP**        | `async with agent.run_mcp_servers(): await agent.run(...)` | `async with agent.run_mcp_servers([…]): await run` | Guides differ in server list injection but both match the API.                           |
| **CLI Event Loop**            | `anyio.run(main_function)`                                 | N/A (handled by caller)                            | CLI runner layer remains outside core agent.                                             |
| **Threaded Input**            | `await anyio.to_thread.run_sync(...)`                     | N/A                                                | Not part of agent class.                                                                  |
| **Graceful Exit**             | `try/except KeyboardInterrupt`                             | N/A                                                | Handled in CLI.                                                                           |
| **Message History**           | Pass as `message_history=[{"role":…, "content":…}]`        | `await agent.run(user_text, message_history=…)`    | ✔ Compliant.                                                                              |

---

# Summary of Findings

- All **core API usages** in `src/agent.py` align with the installed PydanticAI v0.4.2 signatures and documented patterns.
- The cheat-sheet guide targets the upcoming **v0.5+** behaviors (notably streaming API changes and default MCP registration) whereas your code pins v0.4.2.  
- Discrepancies primarily stem from version drift between the guide (v0.5+) and your running environment (v0.4.2). In every case the actual code is correct for v0.4.2’s API; the guide’s patterns will apply once you upgrade to 0.5+.
- Both **static** and **dynamic** MCP server registration patterns are supported; your choice of per-call context management is valid and documented.
- Library code appropriately leaves **event-loop orchestration**, **`anyio`** usage, and **graceful shutdown** to the CLI layer, as recommended.

All deviations have been verified against source and docs. No breaking errors or unsupported patterns were found in your `Context7Agent` implementation.  
