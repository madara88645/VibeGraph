# VibeGraph

VibeGraph is an AI-powered code visualization and learning system that analyzes Python codebases, generates interactive call graphs, and uses a large language model to explain code to beginners — making it easy for "vibe coders" to understand how any Python project actually works by seeing it move, exploring it visually, and asking an AI tutor about each piece.

## Quick Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Analyze a Python project (produces explorer/public/graph_data.json)
python main.py analyze /path/to/your/project

# 3. Export the graph data (optional, done automatically by analyze)
python main.py export

# 4. Start the web server and open the UI
python main.py start
```

## How It Works

1. **Analyze** — VibeGraph walks your Python source files with the built-in `ast` module, extracts every function, class, and call site, and builds an in-memory call graph.
2. **Export** — The call graph is converted to React Flow JSON (nodes + edges) and written to `explorer/public/graph_data.json`.
3. **Visualize** — The React/Vite frontend renders the graph with `dagre` layout and lets you pan, zoom, filter by file, and watch the *Ghost Runner* animation traverse execution paths.
4. **Explain** — Click any node to ask the Groq LLM for an explanation at beginner, intermediate, or advanced level, delivered with technical and analogy tabs.

## Environment Setup

Create a `.env` file in the project root and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

You can get a free Groq API key at <https://console.groq.com>.

## Project Structure

```
VibeGraph/
├── main.py                     # CLI entry point (analyze, export, start)
├── serve.py                    # FastAPI server (API + static file serving)
├── requirements.txt            # Python dependencies
├── .env                        # GROQ_API_KEY (not committed)
├── analyst/
│   ├── analyzer.py             # Python AST-based code analyzer
│   └── exporter.py             # Graph → React Flow JSON exporter
├── teacher/
│   ├── groq_agent.py           # Groq LLM integration for explanations
│   └── basic_reporter.py       # Offline markdown report generator
├── explorer/                   # React frontend (Vite)
│   ├── src/
│   │   ├── App.jsx             # Main app: file filtering, Ghost Runner simulation
│   │   ├── index.css           # Dark theme design system
│   │   ├── utils/layout.js     # dagre-based call graph layout
│   │   └── components/
│   │       ├── GraphViewer.jsx       # React Flow wrapper
│   │       ├── CustomNode.jsx        # Type-colored nodes (fn/class/entry)
│   │       ├── FileSidebar.jsx       # IDE-style file explorer sidebar
│   │       ├── CodePanel.jsx         # Bottom code viewer (Ghost Runner follow)
│   │       ├── SimulationControls.jsx # Play/pause/speed for Ghost Runner
│   │       └── ExplanationPanel.jsx  # AI explanation panel (tabs/levels)
│   └── public/
│       └── graph_data.json     # Generated graph data
└── tests/
    └── test_export.py
```

## Screenshots

*(Screenshots will be added after initial UI is complete.)*
