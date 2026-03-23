"""Pydantic request/response models for the VibeGraph API."""

from typing import Literal
from pydantic import BaseModel


class ExplainRequest(BaseModel):
    file_path: str | None = None
    node_id: str
    level: Literal["beginner", "intermediate", "advanced"] = "intermediate"


class SnippetRequest(BaseModel):
    file_path: str | None = None
    node_id: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    node_id: str | None = None
    file_path: str | None = None
    project_context: str | None = None
    question: str
    history: list[ChatMessage] = []


class LearningPathRequest(BaseModel):
    file_path: str
