<div align="center">

<img src="docs/screenshots/Bannervibe.png" alt="VibeGraph Banner" width="100%">

# VibeGraph

**Turn any Python project into an interactive, AI-powered learning experience.**

Upload your code → explore the call graph → ask AI anything about it.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM-Groq%20%2F%20Llama3-FF6B35)](https://console.groq.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-69%20passing-22C55E)](tests/)

</div>

---

## What is VibeGraph?

VibeGraph parses any Python codebase with AST analysis, renders it as an interactive graph, and lets you click any function or class to get an AI explanation, ask follow-up questions, or watch a "Ghost Runner" animate the execution flow in real time.

Built for people who learn by exploring — vibe coders, junior devs, or anyone dropped into an unfamiliar repo.

---

## Screenshots

<table>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshots/01-main-graph.png" alt="Interactive call graph" width="100%">
      <sub><b>Interactive call graph</b> — file sidebar, node type filtering</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshots/02-node-explanation.png" alt="Node selected with AI explanation and code panel" width="100%">
      <sub><b>AI explanation panel</b> — click any node, get Technical or Analogy view</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshots/03-chat-drawer.png" alt="AI chat drawer" width="100%">
      <sub><b>AI chat</b> — multi-turn conversation with full code context</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshots/04-deps-view.png" alt="Dependency map view" width="100%">
      <sub><b>Dependency map</b> — imports and relationships per file</sub>
    </td>
  </tr>
</table>

---

## Features

| | Feature | Description |
|---|---------|-------------|
| 🧬 | **Interactive Call Graph** | Functions, classes, and relationships as a zoomable, pannable graph |
| 👻 | **Ghost Runner v2** | Intelligent code traversal with 5 strategies (Smart, Entry Flow, Hub Tour, By File, Random), AI narration, Explore mode, progress tracking, and run summaries |
| 🔍 | **Node Search** | Fuzzy search across all nodes with `Ctrl+K` — instantly zooms and highlights |
| 💬 | **AI Chat** | Multi-turn conversation about any node — AI holds the full source as context |
| 🎓 | **Learning Path** | AI-suggested study order: start here, then go here, for any file |
| 📝 | **Code Panel** | Source code with line numbers for every selected node |
| 💡 | **AI Explanations** | Beginner / Intermediate / Advanced levels, Technical or Analogy mode |
| 📤 | **Upload Any Project** | Drop `.py` files or a `.zip` of your whole project — graph appears instantly |

### Ghost Runner v2

The Ghost Runner has been upgraded from a simple random walk to an intelligent, AI-powered code exploration tool:

- **5 Traversal Strategies** — **Smart** (DFS from entry points with hub pause), **Entry Flow** (follow real execution paths), **Hub Tour** (visit most-connected nodes first), **By File** (explore file by file), **Random** (classic mode)
- **AI Narration** — Each step gets a brief AI-generated explanation: what the function does and how it connects to the previous one
- **Explore Mode** — Switch from Auto to Explore to guide the ghost yourself — choose which connected node to visit next
- **Progress Tracking** — Live coverage bar showing nodes visited vs total, with visited-node highlighting
- **Run Summary** — On pause, see a summary: nodes/files covered, most connected hub, unvisited entry points

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Groq API key** — free tier at [console.groq.com](https://console.groq.com) (no credit card required)

### 1. Clone

```bash
git clone https://github.com/madara88645/VibeGraph.git
cd VibeGraph
```

### 2. Install dependencies

```bash
# Python backend
pip install -r requirements.txt

# React frontend
cd explorer && npm install && cd ..
```

### 3. Configure

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run

**Development mode** (hot reload on both sides):

```bash
# Terminal 1 — backend
python serve.py

# Terminal 2 — frontend
cd explorer && npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)**

---

**Production mode** (single port, no Node needed after build):

```bash
cd explorer && npm run build && cd ..
python serve.py
```

Open **[http://localhost:8000](http://localhost:8000)**

---

### 5. Use it

**Upload your project** — click **Upload Project** in the top bar, select `.py` files or a `.zip` archive. The graph appears automatically.

**Analyze via CLI** (optional, for local files):

```bash
python main.py analyze path/to/your_project/
```

---

## Project Structure

```
VibeGraph/
├── analyst/
│   ├── analyzer.py        # AST parser → NetworkX graph (nodes + edges)
│   └── exporter.py        # NetworkX → React Flow JSON
├── teacher/
│   └── groq_agent.py      # Groq LLM: explain / chat / learning path
├── explorer/              # React 19 + Vite frontend
│   └── src/components/    # GraphViewer, ChatDrawer, CodePanel, ...
├── tests/                 # 24 pytest tests
├── serve.py               # FastAPI backend (all API routes)
├── main.py                # CLI entry point
└── requirements.txt
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload-project` | Upload `.py`/`.zip`, returns graph JSON |
| `POST` | `/api/snippet` | Extract source code for a node |
| `POST` | `/api/explain` | AI explanation for a node |
| `POST` | `/api/chat` | Multi-turn AI conversation |
| `POST` | `/api/learning-path` | AI-suggested learning order |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, NetworkX, `ast` stdlib |
| AI | Groq API — Llama 3 (free tier) |
| Frontend | React 19, React Flow, Vite |
| Styling | Custom CSS — dark theme, glassmorphism |
| Tests | pytest, 24 tests |

---

## Tests

```bash
pytest tests/ -v
```

---

## License

GPLv3
