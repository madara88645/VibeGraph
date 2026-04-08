"""Backward-compatible imports for the old Groq teacher module path."""

from teacher.openrouter_teacher import (
    NarrateStepContext,
    OpenRouterTeacher,
    _MAX_CACHE_SIZE,
    _try_parse_json,
)


GroqTeacher = OpenRouterTeacher

__all__ = [
    "GroqTeacher",
    "NarrateStepContext",
    "OpenRouterTeacher",
    "_MAX_CACHE_SIZE",
    "_try_parse_json",
]
