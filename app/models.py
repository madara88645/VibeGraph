"""Pydantic request/response models for the VibeGraph API."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.sanitize import sanitize_llm_input


MAX_FILE_PATH_LENGTH = 1000
MAX_NODE_ID_LENGTH = 255
MAX_PROJECT_CONTEXT_LENGTH = 4000
MAX_QUESTION_LENGTH = 2000
MAX_CONTENT_LENGTH = 4000
MAX_HISTORY_LENGTH = 100
MAX_MODEL_NAME_LENGTH = 120


def _normalize_model_name(value: str | None) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return value


class ExplainRequest(BaseModel):
    file_path: str | None = Field(default=None, max_length=MAX_FILE_PATH_LENGTH)
    node_id: str = Field(max_length=MAX_NODE_ID_LENGTH)
    level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    model: str | None = Field(default=None, max_length=MAX_MODEL_NAME_LENGTH)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "file_path": "my_project/app.py",
                    "node_id": "main",
                    "level": "beginner",
                    "model": "anthropic/claude-haiku-4.5",
                }
            ]
        }
    }

    @field_validator("model", mode="before")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        return _normalize_model_name(value)


class SnippetRequest(BaseModel):
    file_path: str | None = Field(default=None, max_length=MAX_FILE_PATH_LENGTH)
    node_id: str = Field(max_length=MAX_NODE_ID_LENGTH)

    model_config = {
        "json_schema_extra": {
            "examples": [{"file_path": "my_project/app.py", "node_id": "main"}]
        }
    }


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_CONTENT_LENGTH)

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, value: str) -> str:
        if isinstance(value, str):
            if len(value) > MAX_CONTENT_LENGTH:
                raise ValueError(
                    f"String should have at most {MAX_CONTENT_LENGTH} characters"
                )
            return sanitize_llm_input(value, truncate=False)
        return value


class ChatRequest(BaseModel):
    node_id: str | None = Field(default=None, max_length=MAX_NODE_ID_LENGTH)
    file_path: str | None = Field(default=None, max_length=MAX_FILE_PATH_LENGTH)
    project_context: str | None = Field(
        default=None,
        max_length=MAX_PROJECT_CONTEXT_LENGTH,
    )
    question: str = Field(max_length=MAX_QUESTION_LENGTH)
    model: str | None = Field(default=None, max_length=MAX_MODEL_NAME_LENGTH)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_LENGTH,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "node_id": "main",
                    "file_path": "my_project/app.py",
                    "question": "What does this function do?",
                    "model": "anthropic/claude-haiku-4.5",
                    "history": [],
                }
            ]
        }
    }

    @field_validator("model", mode="before")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        return _normalize_model_name(value)

    @field_validator("question", mode="before")
    @classmethod
    def sanitize_question(cls, value: str) -> str:
        if isinstance(value, str):
            if len(value) > MAX_QUESTION_LENGTH:
                raise ValueError(
                    f"String should have at most {MAX_QUESTION_LENGTH} characters"
                )
            return sanitize_llm_input(value, truncate=False)
        return value

    @field_validator("project_context", mode="before")
    @classmethod
    def sanitize_project_context(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            if len(value) > MAX_PROJECT_CONTEXT_LENGTH:
                raise ValueError(
                    f"String should have at most {MAX_PROJECT_CONTEXT_LENGTH} characters"
                )
            return sanitize_llm_input(value, truncate=False)
        return value


class LearningPathRequest(BaseModel):
    file_path: str = Field(max_length=MAX_FILE_PATH_LENGTH)
    model: str | None = Field(default=None, max_length=MAX_MODEL_NAME_LENGTH)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "file_path": "my_project/app.py",
                    "model": "anthropic/claude-haiku-4.5",
                }
            ]
        }
    }

    @field_validator("model", mode="before")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        return _normalize_model_name(value)


class GhostNarrateRequest(BaseModel):
    node_id: str = Field(max_length=MAX_NODE_ID_LENGTH)
    file_path: str | None = Field(default=None, max_length=MAX_FILE_PATH_LENGTH)
    previous_node_id: str | None = Field(
        default=None,
        max_length=MAX_NODE_ID_LENGTH,
    )
    strategy: str = Field(default="smart", max_length=50)
    model: str | None = Field(default=None, max_length=MAX_MODEL_NAME_LENGTH)
    context_nodes: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("context_nodes")
    @classmethod
    def validate_context_nodes(cls, v: list[str]) -> list[str]:
        for node in v:
            if not node.strip():
                raise ValueError("context node must not be empty")
            if len(node) > MAX_NODE_ID_LENGTH:
                raise ValueError(
                    f"context node length cannot exceed {MAX_NODE_ID_LENGTH}"
                )
        return v

    @field_validator("strategy", mode="before")
    @classmethod
    def sanitize_strategy(cls, value: str) -> str:
        if isinstance(value, str):
            if len(value) > 50:
                raise ValueError("String should have at most 50 characters")
            return sanitize_llm_input(value, truncate=False)
        return value

    @field_validator("model", mode="before")
    @classmethod
    def normalize_model(cls, value: str | None) -> str | None:
        return _normalize_model_name(value)


class ExplanationDetail(BaseModel):
    analogy: str
    technical: str
    key_takeaway: str


class ExplainResponse(BaseModel):
    node_id: str
    explanation: ExplanationDetail
    snippet: str


class SnippetResponse(BaseModel):
    node_id: str
    snippet: str
    file_path: str | None
    start_line: int | None
    end_line: int | None
    full_source: str | None


class ChatResponse(BaseModel):
    node_id: str | None
    answer: str


class LearningStep(BaseModel):
    step: int
    node_id: str
    reason: str


class LearningPathResponse(BaseModel):
    file_path: str
    steps: list[LearningStep]


class UploadResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    file_dependencies: list[dict[str, Any]] | None = None
    project_context: str | None = None
    warnings: list[str] | None = None
