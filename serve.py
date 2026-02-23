import os
import ast
import shutil
import tempfile
import uvicorn
import zipfile
from typing import List
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from teacher.groq_agent import GroqTeacher
from analyst.analyzer import CodeAnalyzer
from analyst.exporter import GraphExporter

app = FastAPI(title="Vibe Learning System API")

# Enable CORS for development (allowing frontend on 5173 to talk to backend on 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

teacher = GroqTeacher()
analyzer = CodeAnalyzer()
exporter = GraphExporter()


class ExplainRequest(BaseModel):
    file_path: str | None = None
    node_id: str
    level: str = "intermediate"


# ---------------------------------------------------------------------------
# Snippet extraction utility
# ---------------------------------------------------------------------------

def _extract_snippet(file_path: str, node_id: str) -> str:
    """
    Robustly extracts the source code of a function/class from *file_path*
    whose name matches the last segment of *node_id* (e.g. "MyClass.my_func"
    \u2192 looks for "my_func").

    Returns the code string, or a descriptive fallback message.
    """
    if not file_path:
        return (
            f"# External or Built-in: {node_id}\n"
            "# (No source code available, please explain based on name/context.)"
        )

    resolved = os.path.abspath(file_path)
    if not os.path.isfile(resolved):
        return f"# File not found: {file_path}"

    try:
        with open(resolved, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        return f"# Error reading file: {e}"

    try:
        tree = ast.parse(source, filename=resolved)
    except SyntaxError as e:
        return f"# Syntax error in {file_path}: {e}"

    target_name = node_id.split(".")[-1]
    lines = source.splitlines()

    # Walk the AST looking for FunctionDef / AsyncFunctionDef / ClassDef
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == target_name:
                start = node.lineno - 1          # 0-indexed
                end = node.end_lineno or len(lines)
                return "\n".join(lines[start:end])

    return f"# Code for '{node_id}' not found in {file_path} (analysis mismatch)."


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class SnippetRequest(BaseModel):
    file_path: str | None = None
    node_id: str


@app.post("/api/snippet")
def get_snippet(request: SnippetRequest):
    """
    Returns just the code snippet for a given node, without AI explanation.
    Lightweight endpoint for the Code Follow panel.
    """
    snippet = _extract_snippet(request.file_path, request.node_id)

    # Also find the line range for highlighting
    start_line = None
    end_line = None
    full_source = None

    if request.file_path:
        resolved = os.path.abspath(request.file_path)
        if os.path.isfile(resolved):
            try:
                with open(resolved, "r", encoding="utf-8") as f:
                    full_source = f.read()
                tree = ast.parse(full_source, filename=resolved)
                target_name = request.node_id.split(".")[-1]
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if node.name == target_name:
                            start_line = node.lineno
                            end_line = node.end_lineno
                            break
            except Exception:
                pass

    return {
        "node_id": request.node_id,
        "snippet": snippet,
        "file_path": request.file_path,
        "start_line": start_line,
        "end_line": end_line,
        "full_source": full_source,
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "vibe": "checked"}


@app.post("/api/explain")
def explain_node(request: ExplainRequest):
    """
    Finds the source code for *node_id* in the given file and asks the
    Groq teacher to explain it at the requested difficulty level.
    """
    snippet = _extract_snippet(request.file_path, request.node_id)

    explanation = teacher.explain_code(
        snippet,
        context="External Library / Built-in" if not request.file_path else "",
        level=request.level,
    )

    return {
        "node_id": request.node_id,
        "explanation": explanation,
        "snippet": snippet,
    }


# ---------------------------------------------------------------------------
# POST /api/chat \u2013 Free-form AI conversation about a node
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    node_id: str
    file_path: str | None = None
    question: str
    history: list[ChatMessage] = []


@app.post("/api/chat")
def chat_with_node(request: ChatRequest):
    """
    Free-form conversation about the code behind *node_id*.
    Supports multi-turn via *history*.
    """
    snippet = _extract_snippet(request.file_path, request.node_id)

    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    answer = teacher.chat(
        code_snippet=snippet,
        question=request.question,
        history=history_dicts,
    )

    return {"answer": answer, "node_id": request.node_id}


# ---------------------------------------------------------------------------
# POST /api/learning-path \u2013 Suggested learning order for a file
# ---------------------------------------------------------------------------


class LearningPathRequest(BaseModel):
    file_path: str


@app.post("/api/learning-path")
def suggest_learning_path(request: LearningPathRequest):
    """
    Analyzes *file_path*, extracts its nodes/edges, and asks the LLM
    to suggest the best order to study them.
    """
    if not os.path.isfile(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    result = analyzer.analyze_file(request.file_path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    graph = result["graph"]

    nodes_summary = ", ".join(
        f"{nid} ({data.get('type', '?')})"
        for nid, data in graph.nodes(data=True)
    )
    edges_summary = ", ".join(f"{u} → {v}" for u, v in graph.edges())

    steps = teacher.suggest_learning_path(
        nodes_summary=nodes_summary,
        edges_summary=edges_summary,
        file_path=request.file_path,
    )

    return {"file_path": request.file_path, "steps": steps}


# ---------------------------------------------------------------------------
# POST /api/upload-project \u2013 Receive files, analyze, and return graph
# ---------------------------------------------------------------------------

def cleanup_tmp_dir(path: str):
    """Background task to remove temp directory."""
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

@app.post("/api/upload-project")
async def upload_project(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Receives dynamic uploads (single .py, multiple files, or .zip), saves to a 
    temporary folder, runs analysis, and returns the graph data directly.
    """
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_upload_")
    
    try:
        for file in files:
            file_path = os.path.join(tmp_dir, file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # If it's a zip file, extract it
            if file.filename.endswith(".zip"):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                os.remove(file_path) # Remove zip after extraction
        
        # Run analysis on the directory
        result = analyzer.analyze_file(tmp_dir)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
            
        if result.get("errors") and result["graph"].number_of_nodes() == 0:
            # If all files had errors, return the first error
            raise HTTPException(status_code=400, detail=result["errors"][0])

        graph = result["graph"]
        
        # Use GraphExporter for consistent React Flow JSON format
        # We don't provide an output_path because we want the dict returned
        response_data = exporter.export_to_react_flow(graph)
        
        # Attach tmp_dir root to help frontend know where files are (optional)
        response_data["upload_root"] = tmp_dir
        
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload/Analysis failed: {str(e)}")
    finally:
        if 'tmp_dir' in locals() and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)


# Mount static files (Frontend build)
# Only mounts if the build directory exists
static_dir = os.path.join("explorer", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
