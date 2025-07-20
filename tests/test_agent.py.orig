import pytest
import anyio
import os

from src.agent import UnifiedAgent

@pytest.fixture
def openai_key():
    # Use test key or env; do NOT hardcode real keys
    return os.environ.get("OPENAI_API_KEY", "sk-test-123")

@pytest.mark.anyio
async def test_agent_init_and_basic_chat(openai_key):
    agent = UnifiedAgent(api_key=openai_key)
    # Simple smoke test: the agent should initialize
    assert agent.llm is not None
    assert agent.agent is not None

@pytest.mark.anyio
async def test_agent_chat_returns_string(monkeypatch, openai_key):
    agent = UnifiedAgent(api_key=openai_key)
    
    # Patch agent.agent.run to return a dummy result
    class DummyResult:
        data = "This is a test answer."

    async def dummy_run(*args, **kwargs):
        return DummyResult()
    
    monkeypatch.setattr(agent.agent, "run", dummy_run)

    result = await agent.chat("What is quantum computing?")
    assert isinstance(result, str)
    assert "test answer" in result

@pytest.mark.anyio
async def test_agent_handles_history(monkeypatch, openai_key):
    agent = UnifiedAgent(api_key=openai_key)

    # Patch run
    class DummyResult:
        data = "History test OK."

    async def dummy_run(*args, **kwargs):
        # Make sure history is passed through
        assert "message_history" in kwargs
        return DummyResult()

    monkeypatch.setattr(agent.agent, "run", dummy_run)
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]
    response = await agent.chat("Continue", history)
    assert "OK" in response
