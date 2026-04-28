"""Routes for AI-suggested learning paths."""

import os

from fastapi import APIRouter, HTTPException, Request

import app.dependencies as deps
from analyst.analyzer import CodeAnalyzer
from app.models import LearningPathRequest, LearningPathResponse
from app.rate_limit import LEARNING_LIMIT, limiter
from app.services.learning_path import build_learning_path, refine_learning_path_with_ai
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
    Builds a repo-wide learning path from submitted graph data. Legacy
    file_path-only requests still use the original single-file AI flow.
    """
    if path_request.nodes:
        steps = build_learning_path(path_request.nodes, path_request.edges)

        has_ai_key = bool(request.headers.get("Authorization", "").strip()) or (
            deps.is_server_fallback_enabled()
        )
        if has_ai_key and steps:
            teacher = deps.get_teacher_for_request(request, path_request.model)

            def refine(window):
                return teacher.refine_learning_path(
                    window,
                    allowed_node_ids=[step["node_id"] for step in window],
                )

            steps = refine_learning_path_with_ai(steps, refine)

        return {
            "file_path": path_request.selected_file,
            "selected_file": path_request.selected_file,
            "steps": steps,
        }

    if not path_request.file_path:
        raise HTTPException(status_code=400, detail="Graph nodes or file_path required")

    if not is_safe_path(path_request.file_path):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.isfile(path_request.file_path):
        safe_path = os.path.basename(path_request.file_path)
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {safe_path}",
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
