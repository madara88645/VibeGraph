"""Direct unit tests for the private path-safety helpers in
app/utils/security.py.

tests/test_security.py exercises `_contains_sensitive_segment` and
`_is_within_path` thoroughly, but only indirectly through `is_safe_path`
and `normalize_uploaded_filename`, and only for the segment kinds those
call sites happen to write test fixtures for (.env variants, .git, .ssh,
.aws, .npmrc). Two `_contains_sensitive_segment` branches are never
exercised by any existing test: the `.pem` / `.key` suffix check, and a
bare SSH private key filename (e.g. `id_rsa`, `identity`) that isn't
nested inside a `.ssh` directory (in the existing fixtures `id_rsa` is
always under `.ssh/`, so `.ssh` -- not the filename check -- is what trips
the existing assertions). This file targets those helpers directly.
"""

from app.utils.security import _contains_sensitive_segment, _is_within_path


# ---------------------------------------------------------------------------
# _contains_sensitive_segment
# ---------------------------------------------------------------------------
class TestContainsSensitiveSegment:
    def test_ordinary_path_is_not_sensitive(self):
        assert _contains_sensitive_segment("normal/file.py") is False
        assert _contains_sensitive_segment("src/app.py") is False

    def test_dotenv_and_variants(self):
        assert _contains_sensitive_segment(".env") is True
        assert _contains_sensitive_segment("sub/.env.local") is True

    def test_hidden_segment_set_membership(self):
        assert _contains_sensitive_segment(".git") is True
        assert _contains_sensitive_segment("sub/.git/config") is True
        assert _contains_sensitive_segment(".aws") is True

    def test_bare_ssh_key_filename_without_ssh_directory(self):
        # Not nested under `.ssh/` -- only the SENSITIVE_KEY_FILENAMES
        # membership check (not the `.ssh` segment check) can catch this.
        assert _contains_sensitive_segment("keys/id_rsa") is True
        assert _contains_sensitive_segment("backup/identity") is True
        assert _contains_sensitive_segment("id_ed25519") is True

    def test_pem_and_key_suffix(self):
        assert _contains_sensitive_segment("certs/server.pem") is True
        assert _contains_sensitive_segment("certs/private.key") is True

    def test_similar_looking_suffix_is_not_a_false_positive(self):
        # ".keychain" does not end with ".key" -- must not be flagged.
        assert _contains_sensitive_segment("notes/normal.keychain") is False

    def test_case_insensitive(self):
        assert _contains_sensitive_segment("SUB/.ENV") is True
        assert _contains_sensitive_segment("Certs/Server.PEM") is True

    def test_backslash_separators_are_normalized(self):
        assert _contains_sensitive_segment("sub\\.env") is True


# ---------------------------------------------------------------------------
# _is_within_path
# ---------------------------------------------------------------------------
class TestIsWithinPath:
    def test_path_equal_to_root_is_within(self):
        assert _is_within_path("/tmp/foo", "/tmp/foo") is True

    def test_nested_path_is_within(self):
        assert _is_within_path("/tmp/foo/bar", "/tmp/foo") is True

    def test_sibling_path_is_not_within(self):
        assert _is_within_path("/tmp/other", "/tmp/foo") is False

    def test_prefix_lookalike_is_not_within(self):
        # "/tmp/foobar" merely starts with "/tmp/foo" as a string, but it is
        # not a path *inside* "/tmp/foo" -- commonpath must reject it.
        assert _is_within_path("/tmp/foobar", "/tmp/foo") is False

    def test_mixed_absolute_and_relative_paths_return_false(self):
        # os.path.commonpath raises ValueError when mixing absolute and
        # relative paths; the helper must swallow it and return False
        # rather than propagate.
        assert _is_within_path("relative/path", "/abs/root") is False
