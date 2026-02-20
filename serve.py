"""FastAPI server for VibeGraph.

Serves:
  - Static React build from explorer/dist/
  - REST API:
      GET  /api/graph          Return graph_data.json
      POST /api/explain        Ask Groq to explain a code node
      GET  /api/report         Generate offline markdown report
"""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from teacher.groq_agent import GroqAgent
from teacher.basic_reporter import BasicReporter

app = FastAPI(title="VibeGraph", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPH_DATA_PATH = Path("explorer/public/graph_data.json")
DIST_PATH = Path("explorer/dist")

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/graph")
async def get_graph():
    if not GRAPH_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail="graph_data.json not found. Run 'python main.py analyze <path>' first.")
    return JSONResponse(content=json.loads(GRAPH_DATA_PATH.read_text()))


class ExplainRequest(BaseModel):
    node_id: str
    node_label: str
    source_code: str
    level: str = "beginner"   # beginner | intermediate | advanced


@app.post("/api/explain")
async def explain_node(req: ExplainRequest):
    agent = GroqAgent()
    try:
        result = agent.explain(
            node_label=req.node_label,
            source_code=req.source_code,
            level=req.level,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"explanation": result}


@app.get("/api/report")
async def get_report():
    if not GRAPH_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail="graph_data.json not found. Run 'python main.py analyze <path>' first.")
    graph_data = json.loads(GRAPH_DATA_PATH.read_text())
    reporter = BasicReporter(graph_data)
    markdown = reporter.generate()
    return {"report": markdown}


# ---------------------------------------------------------------------------
# Static file serving (React build)
# ---------------------------------------------------------------------------

if DIST_PATH.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_PATH / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        file_path = DIST_PATH / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DIST_PATH / "index.html"))
