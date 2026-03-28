"""Rate limiting configuration for VibeGraph API."""

import os
import sys
from slowapi import Limiter
from slowapi.util import get_remote_address

_running_under_pytest = "pytest" in sys.modules
_enabled = (
    os.getenv("VIBEGRAPH_RATE_LIMIT_ENABLED", "true").lower() != "false"
    and not _running_under_pytest
)
limiter = Limiter(key_func=get_remote_address, enabled=_enabled)

# Configurable limits via environment variables
CHAT_LIMIT = os.getenv("VIBEGRAPH_RATE_LIMIT_CHAT", "10/minute")
UPLOAD_LIMIT = os.getenv("VIBEGRAPH_RATE_LIMIT_UPLOAD", "5/minute")
EXPLAIN_LIMIT = os.getenv("VIBEGRAPH_RATE_LIMIT_EXPLAIN", "20/minute")
LEARNING_LIMIT = os.getenv("VIBEGRAPH_RATE_LIMIT_LEARNING", "10/minute")
GHOST_NARRATION_LIMIT = os.getenv("VIBEGRAPH_RATE_LIMIT_GHOST", "60/minute")
