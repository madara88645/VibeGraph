"""Routes for AI-suggested learning paths."""

import os

from fastapi import APIRouter, HTTPException, Request

import app.dependencies as deps
from analyst.analyzer import CodeAnalyzer
from app.models import LearningPathRequest, LearningPathResponse
from app.rate_limit import LEARNING_LIMIT, limiter
from app.utils.security import is_safe_path

router = APIRouter(prefix="/api", tags=["learning"])


@router.post(
    "/learning-path",
    response_model=LearningPathResponse,
    summary="AI-suggested learning order for a file",
)
@limiter.limit(LEARNING_LIMIT)
def suggest_learning_path(request: Request, path_request: LearningPathRequest):
    """
    Analyzes *file_path*, extracts its nodes/edges, and asks the LLM
    to suggest the best order to study them.
    """
    if not is_safe_path(path_request.file_path):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.isfile(path_request.file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {path_request.file_path}",
        )

    result = CodeAnalyzer().analyze_file(path_request.file_path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    graph = result["graph"]

    nodes_summary = ", ".join(
        f"{nid} ({data.get('type', '?')})" for nid, data in graph.nodes(data=True)
    )
    edges_summary = ", ".join(f"{u} \u2192 {v}" for u, v in graph.edges())

    teacher = deps.get_teacher_for_request(request, path_request.model)

    steps = teacher.suggest_learning_path(
        nodes_summary=nodes_summary,
        edges_summary=edges_summary,
        file_path=path_request.file_path,
    )

    return {"file_path": path_request.file_path, "steps": steps}
