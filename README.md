# 🧬 VibeGraph

> Turn "vibe coding" into real learning. Analyze any Python project, visualize it as an interactive call graph, and let AI teach you how it works — node by node.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Groq](https://img.shields.io/badge/LLM-Groq-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧬 **Interactive Call Graph** | Visualize functions, classes, and their relationships as a navigable graph |
| 👻 **Ghost Runner** | Watch an AI "ghost" traverse the execution path in real-time |
| 🔍 **Node Search** | Fuzzy search across all nodes with `Ctrl+K`, instantly zoom to results |
| 💬 **AI Chat** | Ask questions about any node — multi-turn conversation with code context |
| 🎯 **Learning Path** | AI-generated step-by-step learning order for any file |
| 📊 **Dependency Map** | See imports and dependencies per file at a glance |
| 📝 **Code Panel** | View source code with syntax highlighting for any selected node |
| 💡 **AI Explanations** | Get analogies, technical breakdowns, and key takeaways for each node |

---

## 🏗️ Architecture

```
VibeGraph/
├── analyst/          # Python AST analyzer & graph exporter
│   ├── analyzer.py   # Parses Python files → nodes + edges + dependencies
│   └── exporter.py   # Converts networkx graph → React Flow JSON
├── teacher/          # AI teaching engine
│   ├── groq_agent.py # Groq LLM: explain, chat, suggest learning paths
│   └── basic_reporter.py
├── explorer/         # React frontend (Vite + React Flow)
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── GraphViewer.jsx
│           ├── SearchBar.jsx
│           ├── ChatDrawer.jsx
│           ├── LearningPath.jsx
│           ├── ExplanationPanel.jsx
│           ├── CodePanel.jsx
│           ├── FileSidebar.jsx
│           ├── SimulationControls.jsx
│           └── CustomNode.jsx
├── serve.py          # FastAPI backend (all API endpoints)
├── main.py           # CLI: analyze files & generate graph JSON
└── tests/            # Pytest test suite (24 tests)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Groq API Key](https://console.groq.com/) (free tier available)

### 1. Clone & Install

```bash
git clone https://github.com/madara88645/VibeGraph.git
cd VibeGraph

# Python dependencies
pip install -r requirements.txt
pip install fastapi uvicorn groq

# Frontend dependencies
cd explorer
npm install
cd ..
```

### 2. Configure

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Analyze a Project

```bash
# Analyze a single Python file
python main.py analyze path/to/your_file.py

# Analyze an entire directory
python main.py analyze path/to/your_project/
```

This generates `explorer/public/graph_data.json`.

### 4. Build & Run

```bash
# Build the frontend
cd explorer
npm run build
cd ..

# Start the server
python serve.py
```

Open **http://localhost:8000** in your browser. 🎉

### Development Mode (hot reload)

```bash
# Terminal 1: Backend
python serve.py

# Terminal 2: Frontend dev server
cd explorer
npm run dev
```

Frontend runs on `http://localhost:5173`, proxied to the backend on port `8000`.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/explain` | AI explanation for a node |
| `POST` | `/api/snippet` | Source code extraction |
| `POST` | `/api/chat` | Multi-turn AI conversation |
| `POST` | `/api/learning-path` | AI-suggested learning order |

---

## 🧪 Testing

```bash
pytest tests/ -v
```

All 24 tests cover: Node Search, AI Chat, Learning Path, Dependency Map, and regression checks.

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, NetworkX, AST
- **AI:** Groq (Llama 3), structured JSON outputs
- **Frontend:** React 19, React Flow, Vite
- **Styling:** Custom CSS with glassmorphism, dark theme

---

## 📄 License

MIT
