import os
import sys
import ast
import shutil
import tempfile
import uvicorn
import zipfile
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from teacher.groq_agent import GroqTeacher
from analyst.analyzer import CodeAnalyzer
from analyst.exporter import GraphExporter
import json as _agent_json
import time as _agent_time

# region agent log
def _agent_debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: dict | None = None) -> None:
    """
    Lightweight debug logger for the AI agent.
    Writes NDJSON lines to debug-0b7624.log for this session.
    """
    try:
        payload = {
            "sessionId": "0b7624",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(_agent_time.time() * 1000),
        }
        with open("debug-0b7624.log", "a", encoding="utf-8") as f:
            f.write(_agent_json.dumps(payload) + "\n")
    except Exception as e:
        # Never let logging break the main flow, but at least report the error
        print(f"DEBUG LOG ERROR: {e}", file=sys.stderr)
# endregion

app = FastAPI(title="Vibe Learning System API")

UPLOAD_RETENTION_SECONDS = int(os.getenv("VIBEGRAPH_UPLOAD_RETENTION_SECONDS", "3600"))
UPLOAD_PREFIX = "vibegraph_upload_"

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


def _is_safe_path(file_path: str) -> bool:
    """
    Validates that a file_path is safe to read.
    It must be within the current working directory or the OS temp directory.
    """
    try:
        resolved = os.path.abspath(file_path)
        cwd = os.path.abspath(os.getcwd())
        if os.path.commonpath([cwd, resolved]) == cwd:
            return True
        tmp_dir = os.path.abspath(tempfile.gettempdir())
        if os.path.commonpath([tmp_dir, resolved]) == tmp_dir:
            # Must specifically be within one of our upload directories
            # to prevent reading arbitrary files from /tmp
            rel_path = os.path.relpath(resolved, tmp_dir)
            if rel_path.startswith(UPLOAD_PREFIX) or rel_path.startswith("vibegraph_test_"):
                return True
        return False
    except ValueError:
        return False

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

    if not _is_safe_path(file_path):
        return f"# Error: Access to {file_path} is denied."

    resolved = os.path.abspath(file_path)
    if not os.path.isfile(resolved):
        return f"# Source for {node_id} (External/Built-in)"

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
        if not _is_safe_path(request.file_path):
            return {"error": "Access denied"}
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
    if not _is_safe_path(request.file_path):
        raise HTTPException(status_code=403, detail="Access denied")

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


def cleanup_expired_upload_dirs(retention_seconds: int = UPLOAD_RETENTION_SECONDS) -> None:
    """Remove old upload temp folders, keeping recent uploads available."""
    now = _agent_time.time()
    temp_root = Path(tempfile.gettempdir())
    for candidate in temp_root.glob(f"{UPLOAD_PREFIX}*"):
        try:
            if not candidate.is_dir():
                continue
            age = now - candidate.stat().st_mtime
            if age > retention_seconds:
                shutil.rmtree(candidate, ignore_errors=True)
        except Exception:
            continue


def _normalize_uploaded_filename(raw_name: str) -> str:
    """Normalize upload path and block path traversal / absolute paths."""
    if not raw_name:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")

    normalized = raw_name.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if not parts:
        raise HTTPException(status_code=400, detail=f"Invalid upload path: {raw_name}")

    if any(part == ".." for part in parts):
        raise HTTPException(status_code=400, detail=f"Unsafe upload path: {raw_name}")

    safe_rel = os.path.join(*parts)
    if os.path.isabs(safe_rel):
        raise HTTPException(status_code=400, detail=f"Unsafe upload path: {raw_name}")

    return safe_rel

@app.post("/api/upload-project")
def upload_project(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Receives dynamic uploads (single .py, multiple files, or .zip), saves to a 
    temporary folder, runs analysis, and returns the graph data directly.
    """
    cleanup_expired_upload_dirs()
    tmp_dir = tempfile.mkdtemp(prefix=UPLOAD_PREFIX)

    # region agent log
    _agent_debug_log(
        run_id="pre-fix",
        hypothesis_id="H1",
        location="serve.py:245",
        message="upload_project_called",
        data={
            "tmp_dir": tmp_dir,
            "incoming_file_count": len(files),
            "sample_filenames": [getattr(f, "filename", None) for f in list(files)[:5]],
        },
    )
    # endregion

    try:
        saved_files: list[dict] = []

        for file in files:
            safe_name = _normalize_uploaded_filename(file.filename)
            file_path = os.path.join(tmp_dir, safe_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            saved_files.append(
                {
                    "stored_path": file_path,
                    "original_name": safe_name,
                    "is_zip": safe_name.endswith(".zip"),
                }
            )

            # If it's a zip file, extract it
            if safe_name.endswith(".zip"):
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    tmp_dir_abs = os.path.abspath(tmp_dir)
                    for member in zip_ref.infolist():
                        extracted_path = os.path.abspath(os.path.join(tmp_dir_abs, member.filename))
                        if not extracted_path.startswith(tmp_dir_abs + os.sep) and extracted_path != tmp_dir_abs:
                            raise HTTPException(status_code=400, detail=f"Unsafe zip file detected: {safe_name}")
                    zip_ref.extractall(tmp_dir)
                os.remove(file_path)  # Remove zip after extraction

        # region agent log
        _agent_debug_log(
            run_id="pre-fix",
            hypothesis_id="H1",
            location="serve.py:266",
            message="before_analyze_file",
            data={
                "tmp_dir": tmp_dir,
                "saved_file_count": len(saved_files),
                "saved_files_sample": saved_files[:5],
            },
        )
        # endregion

        # Run analysis on the directory
        result = analyzer.analyze_file(tmp_dir)

        # region agent log
        _agent_debug_log(
            run_id="pre-fix",
            hypothesis_id="H1",
            location="serve.py:273",
            message="after_analyze_file",
            data={
                "has_error_key": "error" in result,
                "error_value": result.get("error"),
                "errors_count": len(result.get("errors", []))
                if isinstance(result, dict)
                else None,
                "node_count": result.get("graph").number_of_nodes()
                if isinstance(result, dict) and result.get("graph") is not None
                else None,
            },
        )
        # endregion

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        if result.get("errors") and result["graph"].number_of_nodes() == 0:
            # If all files had errors, return the first error
            raise HTTPException(status_code=400, detail=result["errors"][0])

        graph = result["graph"]

        # Use GraphExporter for consistent React Flow JSON format
        # We don't provide an output_path because we want the dict returned
        response_data = exporter.export_to_react_flow(graph)

        # Keep uploaded source available for follow-up snippet/explain calls.
        # Old upload dirs are cleaned periodically by cleanup_expired_upload_dirs().
        response_data["upload_root"] = tmp_dir
        response_data["upload_expires_in_seconds"] = UPLOAD_RETENTION_SECONDS

        # region agent log
        _agent_debug_log(
            run_id="pre-fix",
            hypothesis_id="H1",
            location="serve.py:285",
            message="upload_project_success",
            data={
                "node_count": len(response_data.get("nodes", [])),
                "edge_count": len(response_data.get("edges", [])),
            },
        )
        # endregion

        return response_data

    except HTTPException as exc:
        cleanup_tmp_dir(tmp_dir)
        # region agent log
        _agent_debug_log(
            run_id="pre-fix",
            hypothesis_id="H2",
            location="serve.py:293",
            message="upload_project_http_exception",
            data={
                "status_code": getattr(exc, "status_code", None),
                "detail": getattr(exc, "detail", None),
            },
        )
        # endregion
        raise
    except Exception as e:
        cleanup_tmp_dir(tmp_dir)
        # region agent log
        _agent_debug_log(
            run_id="pre-fix",
            hypothesis_id="H2",
            location="serve.py:302",
            message="upload_project_unexpected_exception",
            data={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        # endregion
        raise HTTPException(status_code=500, detail=f"Upload/Analysis failed: {str(e)}")


# Mount static files (Frontend build)
# Only mounts if the build directory exists
static_dir = os.path.join("explorer", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
