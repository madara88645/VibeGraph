"""Routes for AI chat conversations about code."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models import ChatRequest
from app.utils.snippet import extract_snippet
import app.dependencies as deps

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
def chat_with_node(request: ChatRequest):
    """
    Free-form conversation about the code behind *node_id*.
    Supports multi-turn via *history*.
    """
    snippet, _, _, _ = extract_snippet(request.file_path, request.node_id)

    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    answer = deps.teacher.chat(
        code_snippet=snippet,
        project_context=request.project_context or "",
        question=request.question,
        history=history_dicts,
    )

    return {"answer": answer, "node_id": request.node_id}


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """
    Streaming version of /api/chat. Returns Server-Sent Events
    with token-by-token output for real-time UI updates.
    """
    snippet, _, _, _ = extract_snippet(request.file_path, request.node_id)
    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    def event_generator():
        for token in deps.teacher.stream_chat(
            code_snippet=snippet,
            project_context=request.project_context or "",
            question=request.question,
            history=history_dicts,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
