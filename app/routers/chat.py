"""Routes for AI chat conversations about code."""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

import app.dependencies as deps
from app.models import ChatRequest, ChatResponse
from app.rate_limit import CHAT_LIMIT, limiter
from app.utils.snippet import extract_snippet

router = APIRouter(prefix="/api", tags=["chat"])


def format_sse_event(data: str) -> str:
    """Encode *data* as a valid SSE event, preserving embedded newlines."""
    lines = str(data).splitlines() or [""]
    return "".join(f"data: {line}\n" for line in lines) + "\n"


@router.post("/chat", response_model=ChatResponse, summary="Chat about a code node")
@limiter.limit(CHAT_LIMIT)
def chat_with_node(request: Request, chat_request: ChatRequest):
    """
    Free-form conversation about the code behind *node_id*.
    Supports multi-turn via *history*.
    """
    snippet, _, _, _ = extract_snippet(chat_request.file_path, chat_request.node_id)

    history_dicts = [
        {"role": m.role, "content": m.content} for m in chat_request.history
    ]

    answer = deps.teacher.chat(
        code_snippet=snippet,
        project_context=chat_request.project_context or "",
        question=chat_request.question,
        history=history_dicts,
    )

    return {"answer": answer, "node_id": chat_request.node_id}


@router.post("/chat/stream", summary="Stream chat about a code node")
@limiter.limit(CHAT_LIMIT)
def chat_stream(request: Request, chat_request: ChatRequest):
    """
    Streaming version of /api/chat. Returns Server-Sent Events
    with token-by-token output for real-time UI updates.
    """
    snippet, _, _, _ = extract_snippet(chat_request.file_path, chat_request.node_id)
    history_dicts = [
        {"role": m.role, "content": m.content} for m in chat_request.history
    ]

    def event_generator():
        for token in deps.teacher.stream_chat(
            code_snippet=snippet,
            project_context=chat_request.project_context or "",
            question=chat_request.question,
            history=history_dicts,
        ):
            yield format_sse_event(token)
        yield format_sse_event("[DONE]")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
