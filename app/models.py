"""Pydantic request/response models for the VibeGraph API."""

from typing import Any, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FILE_PATH_LENGTH = 1000
MAX_NODE_ID_LENGTH = 255
MAX_PROJECT_CONTEXT_LENGTH = 4000
MAX_QUESTION_LENGTH = 2000
MAX_CONTENT_LENGTH = 4000
MAX_HISTORY_LENGTH = 100

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ExplainRequest(BaseModel):
    file_path: str | None = Field(default=None, max_length=MAX_FILE_PATH_LENGTH)
    node_id: str = Field(max_length=MAX_NODE_ID_LENGTH)
    level: Literal["beginner", "intermediate", "advanced"] = "intermediate"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "file_path": "my_project/app.py",
                    "node_id": "main",
                    "level": "beginner",
                }
            ]
        }
    }


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


class ChatRequest(BaseModel):
    node_id: str | None = Field(default=None, max_length=MAX_NODE_ID_LENGTH)
    file_path: str | None = Field(default=None, max_length=MAX_FILE_PATH_LENGTH)
    project_context: str | None = Field(default=None, max_length=MAX_PROJECT_CONTEXT_LENGTH)
    question: str = Field(max_length=MAX_QUESTION_LENGTH)
    history: list[ChatMessage] = Field(default_factory=list, max_length=MAX_HISTORY_LENGTH)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "node_id": "main",
                    "file_path": "my_project/app.py",
                    "question": "What does this function do?",
                    "history": [],
                }
            ]
        }
    }


class LearningPathRequest(BaseModel):
    file_path: str = Field(max_length=MAX_FILE_PATH_LENGTH)

    model_config = {
        "json_schema_extra": {"examples": [{"file_path": "my_project/app.py"}]}
    }


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


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
