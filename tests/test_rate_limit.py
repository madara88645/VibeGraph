"""Tests for app/rate_limit.py — rate limiting configuration."""

import re

from app.rate_limit import (
    CHAT_LIMIT,
    EXPLAIN_LIMIT,
    GHOST_NARRATION_LIMIT,
    LEARNING_LIMIT,
    UPLOAD_LIMIT,
    limiter,
    _running_under_pytest,
)
from slowapi import Limiter


_RATE_PATTERN = re.compile(r"^\d+/\w+$")


class TestLimiterInstance:
    def test_limiter_is_slowapi_instance(self):
        assert isinstance(limiter, Limiter)

    def test_rate_limiting_disabled_under_pytest(self):
        assert _running_under_pytest is True


class TestLimitConstants:
    def test_chat_limit(self):
        assert CHAT_LIMIT == "10/minute"

    def test_upload_limit(self):
        assert UPLOAD_LIMIT == "5/minute"

    def test_explain_limit(self):
        assert EXPLAIN_LIMIT == "20/minute"

    def test_learning_limit(self):
        assert LEARNING_LIMIT == "10/minute"

    def test_ghost_narration_limit(self):
        assert GHOST_NARRATION_LIMIT == "60/minute"

    def test_all_limits_match_rate_format(self):
        for name, value in [
            ("CHAT_LIMIT", CHAT_LIMIT),
            ("UPLOAD_LIMIT", UPLOAD_LIMIT),
            ("EXPLAIN_LIMIT", EXPLAIN_LIMIT),
            ("LEARNING_LIMIT", LEARNING_LIMIT),
            ("GHOST_NARRATION_LIMIT", GHOST_NARRATION_LIMIT),
        ]:
            assert _RATE_PATTERN.match(value), f"{name}={value!r} does not match N/unit"
