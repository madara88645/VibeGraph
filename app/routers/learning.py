"""Routes for AI-suggested learning paths."""

import os

from fastapi import APIRouter, HTTPException

from app.models import LearningPathRequest
from app.utils.security import is_safe_path
from analyst.analyzer import CodeAnalyzer
import app.dependencies as deps

router = APIRouter(prefix="/api", tags=["learning"])


@router.post("/learning-path")
def suggest_learning_path(request: LearningPathRequest):
    """
    Analyzes *file_path*, extracts its nodes/edges, and asks the LLM
    to suggest the best order to study them.
    """
    if not is_safe_path(request.file_path):
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
    edges_summary = ", ".join(f"{u} \u2192 {v}" for u, v in graph.edges())

    steps = deps.teacher.suggest_learning_path(
        nodes_summary=nodes_summary,
        edges_summary=edges_summary,
        file_path=request.file_path,
    )

    return {"file_path": request.file_path, "steps": steps}
