"""Unit tests for JSONFormatter.format() in app/__init__.py."""

import json
import logging

from app import JSONFormatter


def _make_record(
    msg: str = "hello",
    level: int = logging.INFO,
    name: str = "test.logger",
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )
    return record


class TestJSONFormatterRequiredFields:
    def test_output_is_valid_json(self):
        fmt = JSONFormatter()
        record = _make_record()
        output = fmt.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_timestamp_field_present(self):
        fmt = JSONFormatter()
        record = _make_record()
        parsed = json.loads(fmt.format(record))
        assert "timestamp" in parsed
        assert isinstance(parsed["timestamp"], str)
        assert parsed["timestamp"]  # non-empty

    def test_level_field_matches_level_name(self):
        for level, name in [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]:
            record = _make_record(level=level)
            parsed = json.loads(JSONFormatter().format(record))
            assert parsed["level"] == name

    def test_logger_field_matches_record_name(self):
        fmt = JSONFormatter()
        record = _make_record(name="my.module.name")
        parsed = json.loads(fmt.format(record))
        assert parsed["logger"] == "my.module.name"

    def test_message_field_matches_log_message(self):
        fmt = JSONFormatter()
        record = _make_record(msg="important event occurred")
        parsed = json.loads(fmt.format(record))
        assert parsed["message"] == "important event occurred"

    def test_message_with_printf_args_is_expanded(self):
        fmt = JSONFormatter()
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="", lineno=0,
            msg="count is %d", args=(42,), exc_info=None,
        )
        parsed = json.loads(fmt.format(record))
        assert parsed["message"] == "count is 42"


class TestJSONFormatterRequestID:
    def test_request_id_included_when_set(self):
        fmt = JSONFormatter()
        record = _make_record()
        record.request_id = "abc12345"
        parsed = json.loads(fmt.format(record))
        assert parsed.get("request_id") == "abc12345"

    def test_request_id_absent_when_not_set(self):
        fmt = JSONFormatter()
        record = _make_record()
        parsed = json.loads(fmt.format(record))
        assert "request_id" not in parsed

    def test_request_id_can_be_any_string(self):
        fmt = JSONFormatter()
        record = _make_record()
        record.request_id = "req-uuid-9f3c"
        parsed = json.loads(fmt.format(record))
        assert parsed["request_id"] == "req-uuid-9f3c"


class TestJSONFormatterException:
    def _record_with_exc(self, exc: Exception) -> logging.LogRecord:
        try:
            raise exc
        except Exception:
            import sys
            exc_info = sys.exc_info()
        record = _make_record()
        record.exc_info = exc_info
        return record

    def test_exception_included_when_exc_info_present(self):
        fmt = JSONFormatter()
        record = self._record_with_exc(ValueError("bad input"))
        parsed = json.loads(fmt.format(record))
        assert "exception" in parsed
        assert "bad input" in parsed["exception"]

    def test_exception_field_is_string_representation(self):
        fmt = JSONFormatter()
        record = self._record_with_exc(RuntimeError("oops"))
        parsed = json.loads(fmt.format(record))
        assert isinstance(parsed["exception"], str)

    def test_exception_absent_when_exc_info_is_none(self):
        fmt = JSONFormatter()
        record = _make_record()
        record.exc_info = None
        parsed = json.loads(fmt.format(record))
        assert "exception" not in parsed

    def test_exception_absent_when_exc_info_exception_is_none(self):
        fmt = JSONFormatter()
        record = _make_record()
        record.exc_info = (None, None, None)
        parsed = json.loads(fmt.format(record))
        assert "exception" not in parsed

    def test_no_extra_keys_in_minimal_record(self):
        fmt = JSONFormatter()
        record = _make_record()
        parsed = json.loads(fmt.format(record))
        assert set(parsed.keys()) == {"timestamp", "level", "logger", "message"}
