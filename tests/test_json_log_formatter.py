"""Unit tests for JSONFormatter in app/__init__.py.

JSONFormatter is the structured log formatter used by all VibeGraph workers.
Its format() method is a pure transformation: LogRecord → JSON string.
Regressions here would silently corrupt production log pipelines without
raising a type error, so the contract is worth pinning explicitly.
"""

import json
import logging

from app import JSONFormatter


def _make_record(
    msg: str = "test message",
    name: str = "test.logger",
    level: int = logging.INFO,
    *,
    request_id: str | None = None,
    exc_info=None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    if request_id is not None:
        record.request_id = request_id  # type: ignore[attr-defined]
    return record


class TestJSONFormatterFormat:
    def setup_method(self):
        self.fmt = JSONFormatter()

    def test_output_is_valid_json(self):
        record = _make_record("hello")
        output = self.fmt.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_required_keys_present(self):
        record = _make_record("hello")
        parsed = json.loads(self.fmt.format(record))
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed

    def test_level_name_matches_record(self):
        record = _make_record("oops", level=logging.ERROR)
        parsed = json.loads(self.fmt.format(record))
        assert parsed["level"] == "ERROR"

    def test_logger_name_matches_record(self):
        record = _make_record("msg", name="app.routers.upload")
        parsed = json.loads(self.fmt.format(record))
        assert parsed["logger"] == "app.routers.upload"

    def test_message_matches_record(self):
        record = _make_record("something happened")
        parsed = json.loads(self.fmt.format(record))
        assert parsed["message"] == "something happened"

    def test_request_id_included_when_present(self):
        record = _make_record("msg", request_id="abc12345")
        parsed = json.loads(self.fmt.format(record))
        assert parsed["request_id"] == "abc12345"

    def test_request_id_absent_when_not_set(self):
        record = _make_record("msg")
        parsed = json.loads(self.fmt.format(record))
        assert "request_id" not in parsed

    def test_exception_included_when_exc_info_set(self):
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = _make_record("error occurred", exc_info=exc_info)
        parsed = json.loads(self.fmt.format(record))
        assert "exception" in parsed
        assert "boom" in parsed["exception"]

    def test_exception_absent_when_no_exc_info(self):
        record = _make_record("all good")
        parsed = json.loads(self.fmt.format(record))
        assert "exception" not in parsed

    def test_timestamp_is_non_empty_string(self):
        record = _make_record("ts test")
        parsed = json.loads(self.fmt.format(record))
        assert isinstance(parsed["timestamp"], str)
        assert len(parsed["timestamp"]) > 0

    def test_info_level_record(self):
        record = _make_record("info msg", level=logging.INFO)
        parsed = json.loads(self.fmt.format(record))
        assert parsed["level"] == "INFO"

    def test_warning_level_record(self):
        record = _make_record("warn msg", level=logging.WARNING)
        parsed = json.loads(self.fmt.format(record))
        assert parsed["level"] == "WARNING"
