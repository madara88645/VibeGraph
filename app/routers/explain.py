"""Routes for code explanation and snippet extraction."""

from fastapi import APIRouter, Request

import app.dependencies as deps
from app.models import ExplainRequest, ExplainResponse, SnippetRequest, SnippetResponse
from app.rate_limit import EXPLAIN_LIMIT, limiter
from app.utils.snippet import extract_snippet

router = APIRouter(prefix="/api", tags=["explain"])


@router.post(
    "/snippet",
    response_model=SnippetResponse,
    summary="Get raw code snippet for a node",
)
@limiter.limit(EXPLAIN_LIMIT)
def get_snippet(request: Request, snippet_request: SnippetRequest):
    """
    Returns just the code snippet for a given node, without AI explanation.
    Lightweight endpoint for the Code Follow panel.
    """
    snippet, start_line, end_line, full_source = extract_snippet(
        snippet_request.file_path,
        snippet_request.node_id,
    )

    return {
        "node_id": snippet_request.node_id,
        "snippet": snippet,
        "file_path": snippet_request.file_path,
        "start_line": start_line,
        "end_line": end_line,
        "full_source": full_source,
    }


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="AI explanation for a code node",
)
@limiter.limit(EXPLAIN_LIMIT)
def explain_node(request: Request, explain_request: ExplainRequest):
    """
    Finds the source code for *node_id* in the given file and asks the
    Groq teacher to explain it at the requested difficulty level.
    """
    snippet, _, _, _ = extract_snippet(
        explain_request.file_path, explain_request.node_id
    )

    explanation = deps.teacher.explain_code(
        snippet,
        context="External Library / Built-in" if not explain_request.file_path else "",
        level=explain_request.level,
    )

    return {
        "node_id": explain_request.node_id,
        "explanation": explanation,
        "snippet": snippet,
    }
