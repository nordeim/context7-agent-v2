# Context7 Agent

**An immersive, conversational AI agent for contextual document discovery, powered by Pydantic AI and deeply integrated with Context7 MCP.**

![Context7 ASCII Art](docs/theme-ascii/cyberpunk.txt)

---

## 🚀 Features

- **Stunning Terminal UI** with 4 beautiful themes (Cyberpunk, Ocean, Forest, Sunset), glowing text, gradient headers, and animated ASCII art.
- **Conversational Chat** powered by OpenAI with robust intent detection.
- **Context7 MCP Integration:** AI-powered, real-time document search, analysis, and management.
- **Dynamic TUI Layout:** Split-screen, live streaming, bookmarks, analytics, hotkeys.
- **Smart Document Management:** Syntax-highlighted previews, bookmarks, session restore, search history.
- **Performance Optimizations:** Async operations, smooth typing and loading animations.
- **JSON Persistence:** Your search history, bookmarks, and sessions are saved automatically.

---

## 🧩 Project Structure

```
context7-agent/
├── src/
│   ├── agent.py       # The Unified Pydantic AI Agent
│   ├── cli.py         # CLI interface (Rich TUI)
│   ├── config.py      # Config loader (env, themes, keys)
│   ├── history.py     # Conversation & session management
│   ├── themes.py      # Theme definitions & ASCII art
│   └── utils.py       # Utility functions
├── tests/
│   ├── test_agent.py
│   └── test_history.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── pyproject.toml
```

---

## ⚡️ Prerequisites

- **Python 3.11+**
- **Node.js** (for Context7 MCP server)
- **OpenAI API Key** (or compatible endpoint)
- `pip install "pydantic-ai>=0.5,<1.0" anyio openai rich`

---

## ✨ Installation

```bash
git clone https://github.com/your-org/context7-agent.git
cd context7-agent
cp .env.example .env
# Edit .env to set your OpenAI key and base URL if needed
pip install -r requirements.txt
npm install -g @upstash/context7-mcp
```

---

## ⚙️ Configuration

- Set your OpenAI API key and model in `.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

- MCP server config (JSON for Pydantic AI):
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

---

## 🎨 Themes & Visuals

- Switch themes with `/theme`, e.g., `/theme cyberpunk`
- Enjoy animated ASCII art at startup
- Hotkeys: `/help`, `/bookmark`, `/preview 1`, `/exit`, `/analytics`

---

## 🕹️ Usage

Run the agent in your terminal:

```bash
python -m src.cli
```

**You’ll see:**
- Animated welcome screen
- Prompt to chat (try: `Tell me about quantum computing`)
- Live, streaming document results
- Inline previews: `/preview 1`
- Bookmark docs: `/bookmark 1`
- Switch themes: `/theme forest`
- Exit: `/exit`

---

## 🛠️ Development & Testing

- Tests: `pytest tests/`
- Edit themes in `src/themes.py`
- Add new filters/commands in `src/cli.py` and `src/agent.py`
- For advanced MCP customization, see [Context7 MCP docs](https://github.com/upstash/context7-mcp)

---

## 🏗️ Architecture

- **Unified Pydantic AI Agent:** All chat and tool-calling via `agent.run()`
- **MCPServerStdio:** Streams search results from Context7 knowledge base
- **Rich TUI:** Dynamic, animated terminal UI
- **HistoryManager:** Persists chat, bookmarks, and sessions in JSON

---

## 🧑‍💻 Example CLI Session

```
~$ python -m src.cli

[Cyberpunk ASCII Art]
Welcome to Context7 Agent! (Theme: Cyberpunk)
Type '/help' for commands.

You: Tell me about quantum computing
[Animated loader] ...
Agent: [Document summary + source links]

You: /preview 1
[Syntax-highlighted preview of doc 1]

You: /bookmark 1
[Bookmarked!]

You: /theme sunset
[Sunset ASCII Art, new theme applied!]

You: /exit
Goodbye!
```

---

## 📂 Persistence

- Conversations, sessions, bookmarks, and history are stored as JSON in your user data directory.

---

## 🛡️ Security

- Never commit your real `.env` file or API keys to git!
- `.gitignore` ensures secrets and compiled files are not tracked.

---

## 🤖 Credits

- Context7 MCP by Upstash
- Pydantic AI by Pydantic/AI
- OpenAI API for chat completion
- Rich for terminal UI

---

## 📄 License

MIT
