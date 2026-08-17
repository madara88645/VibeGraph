"""Direct unit tests for app/services/learning_path.py's _basename helper.

_basename feeds `_is_entry_point`'s filename-based fallback heuristic
(cli.py / __main__.py / main.py / serve.py -> treated as an entry point).
The existing tests/test_learning_path_helpers.py only exercises it through
forward-slash paths (e.g. "src/pkg/cli.py"); the backslash-normalization
branch -- needed for graphs built from Windows-style file paths -- was
never exercised directly. This file covers that gap plus the surrounding
edge cases (None, empty string, mixed separators, no separator).

Pure function, no I/O.
"""

from app.services.learning_path import _basename, _is_entry_point


class TestBasenamePosixPaths:
    def test_simple_forward_slash_path(self):
        assert _basename("src/pkg/cli.py") == "cli.py"

    def test_no_separator_returns_input_unchanged(self):
        assert _basename("cli.py") == "cli.py"

    def test_trailing_slash_yields_empty_basename(self):
        assert _basename("src/pkg/") == ""


class TestBasenameWindowsPaths:
    def test_simple_backslash_path(self):
        assert _basename("src\\pkg\\cli.py") == "cli.py"

    def test_windows_drive_letter_path(self):
        assert _basename("C:\\Users\\dev\\project\\main.py") == "main.py"

    def test_backslash_only_no_forward_slash(self):
        assert _basename("a\\b\\c\\serve.py") == "serve.py"

    def test_trailing_backslash_yields_empty_basename(self):
        assert _basename("src\\pkg\\") == ""


class TestBasenameMixedSeparators:
    def test_mixed_forward_and_backslash_takes_last_segment(self):
        # A path like "src/pkg\\sub/cli.py" (mixed separators, which can
        # show up in graphs merged from different OS sources) should still
        # resolve to the final path component.
        assert _basename("src/pkg\\sub/cli.py") == "cli.py"

    def test_mixed_separators_backslash_last(self):
        assert _basename("src/pkg/sub\\main.py") == "main.py"


class TestBasenameNoneAndEmpty:
    def test_none_returns_empty_string(self):
        assert _basename(None) == ""

    def test_empty_string_returns_empty_string(self):
        assert _basename("") == ""


class TestBasenameFeedsEntryPointHeuristic:
    """Integration-flavored checks confirming the backslash-normalization
    branch actually changes _is_entry_point's outcome, not just _basename
    in isolation."""

    def test_windows_style_cli_path_is_detected_as_entry_point(self):
        data = {"label": "helper", "file": "src\\pkg\\cli.py"}
        assert _is_entry_point("n", data) is True

    def test_windows_style_main_path_is_detected_as_entry_point(self):
        data = {"label": "helper", "file": "C:\\repo\\main.py"}
        assert _is_entry_point("n", data) is True

    def test_windows_style_non_entry_filename_is_not_entry_point(self):
        data = {"label": "helper", "file": "src\\pkg\\utils.py"}
        assert _is_entry_point("n", data) is False
