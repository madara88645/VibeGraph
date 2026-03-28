"""Input sanitization utilities for LLM-bound text."""
import re

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions",
    r"(?i)ignore\s+(all\s+)?above\s+instructions",
    r"(?i)disregard\s+(all\s+)?previous",
    r"(?i)you\s+are\s+now\s+a",
    r"(?i)new\s+instructions?\s*:",
    r"(?i)override\s+(system|previous)\s+(prompt|instructions?)",
    r"(?i)forget\s+(everything|all|your)\s+(previous|above)",
    r"(?i)\bsystem\s*:\s*you\s+are\b",
    r"(?i)act\s+as\s+(if\s+)?you\s+(are|were)\s+a",
    r"(?i)pretend\s+(to\s+be|you\s+are)",
]

_compiled_patterns = [re.compile(p) for p in _INJECTION_PATTERNS]


def sanitize_llm_input(text: str, max_length: int = 4000, truncate: bool = True) -> str:
    """Sanitize user input before sending to LLM.

    Truncates to max_length and strips common injection patterns.
    Preserves benign code references (e.g., variable named 'system').
    """
    if not isinstance(text, str):
        return ""

    if truncate:
        text = text[:max_length]

    # Strip injection patterns
    for pattern in _compiled_patterns:
        text = pattern.sub("[filtered]", text)

    return text.strip()
