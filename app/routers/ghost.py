"""Routes for Ghost Runner narration."""

from fastapi import APIRouter, Request

from app.models import GhostNarrateRequest
from app.rate_limit import limiter, GHOST_NARRATION_LIMIT
from app.utils.snippet import extract_snippet
import app.dependencies as deps
from teacher.openrouter_teacher import NarrateStepContext

router = APIRouter(prefix="/api", tags=["ghost"])


@router.post("/ghost-narrate")
@limiter.limit(GHOST_NARRATION_LIMIT)
def ghost_narrate(request: Request, body: GhostNarrateRequest):
    """
    Generate a brief AI narration for a Ghost Runner traversal step.
    Returns a short explanation of what the current node does and how
    it relates to the previous node.
    """
    snippet, _, _, _ = extract_snippet(body.file_path, body.node_id)

    # Build edge context from context_nodes trail
    edge_context = ""
    if body.context_nodes:
        edge_context = f"Recent trail: {' → '.join(body.context_nodes)}"

    context = NarrateStepContext(
        code_snippet=snippet,
        node_id=body.node_id,
        file_path=body.file_path,
        previous_node_id=body.previous_node_id,
        edge_context=edge_context,
        strategy=body.strategy,
    )

    teacher = deps.get_teacher_for_request(request, body.model)
    result = teacher.narrate_step(context)

    return {
        "node_id": body.node_id,
        **result,
    }
