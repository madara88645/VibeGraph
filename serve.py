import os
import ast
import logging
import time
import shutil
import tempfile
import uvicorn
import zipfile
import functools
from pathlib import Path
from typing import List, Literal
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from teacher.groq_agent import GroqTeacher
from analyst.analyzer import CodeAnalyzer
from analyst.exporter import GraphExporter

app = FastAPI(title="Vibe Learning System API")


@app.exception_handler(Exception)
def global_exception_handler(request, exc: Exception):
    """Global catch-all to prevent stack trace leaks."""
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


UPLOAD_RETENTION_SECONDS = int(os.getenv("VIBEGRAPH_UPLOAD_RETENTION_SECONDS", "3600"))
UPLOAD_PREFIX = "vibegraph_upload_"

CORS_ORIGINS = os.getenv(
    "VIBEGRAPH_CORS_ORIGINS", "http://localhost:5173,http://localhost:8000"
)

# Enable CORS for development (allowing frontend on 5173 to talk to backend on 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent leaking stack traces and internals
    to the client. Logs the actual error and returns a generic 500 JSON response.
    """
    logger.error(
        f"Unhandled exception during {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


teacher = GroqTeacher()
exporter = GraphExporter()


class ExplainRequest(BaseModel):
    file_path: str | None = None
    node_id: str
    level: Literal["beginner", "intermediate", "advanced"] = "intermediate"


# ---------------------------------------------------------------------------
# Snippet extraction utility
# ---------------------------------------------------------------------------


def _is_safe_path(path: str) -> bool:
    """Ensure the path is either within the current working directory or a valid upload temp directory."""
    try:
        resolved = os.path.realpath(path)
        cwd = os.path.realpath(os.getcwd())

        if os.path.commonpath([resolved, cwd]) == cwd:
            rel_path = os.path.relpath(resolved, cwd)
            parts = rel_path.split(os.sep)
            # Block hidden files and directories
            if any(part.startswith(".") for part in parts if part != "."):
                return False
            return True
    except ValueError:
        pass

    tmp_dir = os.path.realpath(tempfile.gettempdir())
    try:
        if os.path.commonpath([resolved, tmp_dir]) == tmp_dir:
            rel_path = os.path.relpath(resolved, tmp_dir)
            parts = rel_path.split(os.sep)
            # Block hidden files and directories
            if any(part.startswith(".") for part in parts if part != "."):
                return False
            if parts and (
                parts[0].startswith(UPLOAD_PREFIX)
                or parts[0].startswith("vibegraph_test_")
            ):
                return True
    except ValueError:
        pass

    return False


@functools.lru_cache(maxsize=128)
def _get_parsed_ast(
    resolved_path: str, mtime: float
) -> tuple[str | None, ast.AST | None, str | None]:
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        return None, None, f"# Error reading file: {e}"

    try:
        tree = ast.parse(source, filename=resolved_path)
    except SyntaxError as e:
        return source, None, f"# Syntax error in {resolved_path}: {e}"

    return source, tree, None


def _extract_snippet(
    file_path: str, node_id: str
) -> tuple[str, int | None, int | None, str | None]:
    """
    Robustly extracts the source code of a function/class from *file_path*
    whose name matches the last segment of *node_id* (e.g. "MyClass.my_func"
    \u2192 looks for "my_func").

    Returns a tuple of:
      (code_string, start_line, end_line, full_source)
    where start_line and end_line are 1-indexed.
    """
    if not file_path:
        return (
            f"# External or Built-in: {node_id}\n"
            "# (No source code available, please explain based on name/context.)",
            None,
            None,
            None,
        )

    resolved = os.path.realpath(file_path)

    if not _is_safe_path(resolved):
        return f"# Access denied: Unsafe file path {file_path}", None, None, None

    if not os.path.isfile(resolved):
        return f"# Source for {node_id} (External/Built-in)", None, None, None

    try:
        mtime = os.path.getmtime(resolved)
    except OSError:
        mtime = 0.0

    source, tree, error = _get_parsed_ast(resolved, mtime)

    if error:
        if source is not None:
            # It was a SyntaxError where we still got the source
            return error, None, None, source
        # It was an OSError where we don't have source
        return error, None, None, None

    target_name = node_id.split(".")[-1]
    lines = source.splitlines()

    # Walk the AST looking for FunctionDef / AsyncFunctionDef / ClassDef
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == target_name:
                start = node.lineno - 1  # 0-indexed
                end = node.end_lineno or len(lines)
                return "\n".join(lines[start:end]), node.lineno, node.end_lineno, source

    return (
        f"# Code for '{node_id}' not found in {file_path} (analysis mismatch).",
        None,
        None,
        source,
    )


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
    snippet, start_line, end_line, full_source = _extract_snippet(
        request.file_path, request.node_id
    )

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
    """Basic health check."""
    return {"status": "ok", "vibe": "checked"}


@app.post("/api/explain")
def explain_node(request: ExplainRequest):
    """
    Finds the source code for *node_id* in the given file and asks the
    Groq teacher to explain it at the requested difficulty level.
    """
    snippet, _, _, _ = _extract_snippet(request.file_path, request.node_id)

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
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    node_id: str | None = None
    file_path: str | None = None
    project_context: str | None = None
    question: str
    history: list[ChatMessage] = []


@app.post("/api/chat")
def chat_with_node(request: ChatRequest):
    """
    Free-form conversation about the code behind *node_id*.
    Supports multi-turn via *history*.
    """
    snippet, _, _, _ = _extract_snippet(request.file_path, request.node_id)

    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    answer = teacher.chat(
        code_snippet=snippet,
        project_context=request.project_context or "",
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
        raise HTTPException(
            status_code=404, detail=f"File not found: {request.file_path}"
        )

    result = CodeAnalyzer().analyze_file(request.file_path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    graph = result["graph"]

    nodes_summary = ", ".join(
        f"{nid} ({data.get('type', '?')})" for nid, data in graph.nodes(data=True)
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


def cleanup_expired_upload_dirs(
    retention_seconds: int = UPLOAD_RETENTION_SECONDS,
) -> None:
    """Remove old upload temp folders, keeping recent uploads available."""
    now = time.time()
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
def upload_project(
    background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)
):
    """
    Receives dynamic uploads (single .py, multiple files, or .zip), saves to a
    temporary folder, runs analysis, and returns the graph data directly.
    """
    background_tasks.add_task(cleanup_expired_upload_dirs)
    tmp_dir = tempfile.mkdtemp(prefix=UPLOAD_PREFIX)

    MAX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024  # 100 MB

    try:
        for file in files:
            safe_name = _normalize_uploaded_filename(file.filename)
            file_path = os.path.join(tmp_dir, safe_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # If it's a zip file, validate and extract it
            if safe_name.endswith(".zip"):
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    tmp_dir_abs = os.path.abspath(tmp_dir)
                    # Check for path traversal
                    safe_members = []
                    for member in zip_ref.infolist():
                        # Prevent absolute path resolution escaping tmp_dir_abs
                        safe_filename = member.filename.lstrip("/\\")
                        extracted_path = os.path.abspath(
                            os.path.join(tmp_dir_abs, safe_filename)
                        )
                        if (
                            not extracted_path.startswith(tmp_dir_abs + os.sep)
                            and extracted_path != tmp_dir_abs
                        ):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Unsafe zip file detected: {safe_name}",
                            )
                        # Update the filename to the safe version for extractall
                        member.filename = safe_filename
                        safe_members.append(member)
                    # Check for zip bomb
                    total_size = sum(m.file_size for m in safe_members)
                    if total_size > MAX_UNCOMPRESSED_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Zip contents too large: {total_size} bytes (max {MAX_UNCOMPRESSED_SIZE})",
                        )
                    zip_ref.extractall(tmp_dir, members=safe_members)
                os.remove(file_path)  # Remove zip after extraction

        # Run analysis on the directory
        result = CodeAnalyzer().analyze_file(tmp_dir)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        if result.get("errors") and result["graph"].number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail=result["errors"][0])

        graph = result["graph"]
        response_data = exporter.export_to_react_flow(graph)

        return response_data

    except HTTPException:
        cleanup_tmp_dir(tmp_dir)
        raise
    except Exception as e:
        logging.error(f"Upload/Analysis failed: {e}", exc_info=True)
        cleanup_tmp_dir(tmp_dir)
        raise HTTPException(
            status_code=500, detail="Upload/Analysis failed due to an internal error."
        )


# Mount static files (Frontend build)
# Only mounts if the build directory exists
static_dir = os.path.join("explorer", "dist")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
