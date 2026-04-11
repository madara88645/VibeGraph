"""Input sanitization utilities for LLM-bound text."""

import re

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above\s+instructions",
    r"disregard\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a",
    r"new\s+instructions?\s*:",
    r"override\s+(system|previous)\s+(prompt|instructions?)",
    r"forget\s+(everything|all|your)\s+(previous|above)",
    r"\bsystem\s*:\s*you\s+are\b",
    r"act\s+as\s+(if\s+)?you\s+(are|were)\s+a",
    r"pretend\s+(to\s+be|you\s+are)",
]

_combined_pattern = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


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
    text = _combined_pattern.sub("[filtered]", text)

    return text.strip()
