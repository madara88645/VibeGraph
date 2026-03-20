## 2025-03-02 - Path Traversal (Arbitrary File Read via Hidden Files)
**Vulnerability:** The `_is_safe_path` function validated paths to ensure they were within the current working directory, but failed to block access to hidden files like `.env` and directories like `.git`. This meant endpoints using `_extract_snippet` could potentially be exploited to leak sensitive info such as API keys.
**Learning:** `os.path.commonpath` only validates the root directory boundary. It does not inspect the path components themselves to ensure they follow project-level constraints like avoiding hidden configuration files.
**Prevention:** Always combine path boundary checks (`os.path.commonpath` or `startswith`) with component-level inspection (e.g., checking if any path component starts with `.`) to block access to hidden/sensitive items within an otherwise valid directory.

## 2024-03-18 - Path Traversal Vulnerability in Zip Extraction
**Vulnerability:** A zip file with absolute paths (e.g. `member.filename` starting with `/`) bypassing Python's `os.path.abspath(os.path.join(tmp_dir, member.filename))` and overwriting system files during `zip_ref.extractall()`
**Learning:** `os.path.join` replaces previous segments when encountering an absolute path, so a maliciously constructed zip containing a file named `/etc/passwd` evaluates the absolute path to `/etc/passwd`. Therefore the `startswith` validation would be skipped if not validated specifically or handled correctly.
**Prevention:** Always strip leading slashes (using `lstrip('/\\')`) from `member.filename` and directly mutate the member attribute before calling `zip_ref.extractall()` and storing safe members inside a secure array.

## 2025-03-02 - Information Exposure via Error Messages
**Vulnerability:** Unhandled exceptions and caught exceptions within API endpoints leaked raw stack traces and internal strings back to the client.
**Learning:** Broad exception blocks should catch internal details but only expose generic error strings to the outside world.
**Prevention:** Always implement global exception handlers that return generic 500 errors and avoid stringifying Exception e directly into API response objects.
