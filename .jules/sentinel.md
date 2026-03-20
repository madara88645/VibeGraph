## 2025-03-02 - Path Traversal (Arbitrary File Read via Hidden Files)
**Vulnerability:** The `_is_safe_path` function validated paths to ensure they were within the current working directory, but failed to block access to hidden files like `.env` and directories like `.git`. This meant endpoints using `_extract_snippet` could potentially be exploited to leak sensitive info such as API keys.
**Learning:** `os.path.commonpath` only validates the root directory boundary. It does not inspect the path components themselves to ensure they follow project-level constraints like avoiding hidden configuration files.
**Prevention:** Explicitly block access to hidden files and directories across all snippet extraction endpoints by iterating path parts and rejecting any part starting with a dot (except `.` or `..` which are handled by standard resolution).

## 2025-03-02 - Absolute Path Zip-Slip Prevention
**Vulnerability:** A zip file with absolute paths (e.g. `member.filename` starting with `/`) bypassing Python's `os.path.abspath(os.path.join(tmp_dir, member.filename))` and overwriting system files during `zip_ref.extractall()`
**Learning:** `os.path.join` replaces previous segments when encountering an absolute path, so a maliciously constructed zip containing a file named `/etc/passwd` evaluates the absolute path to `/etc/passwd`. Therefore the `startswith` validation would be skipped if not validated specifically or handled correctly.
**Prevention:** Always strip leading slashes (using `lstrip('/\\')`) from `member.filename` and directly mutate the member attribute before calling `zip_ref.extractall()` and storing safe members inside a secure array.

## 2025-02-26 - Prevent Zip-Slip Risk from extractall() in File Uploads
**Vulnerability:** The use of `zipfile.extractall()` poses a historical security risk related to arbitrary file writes during extraction. Although path traversal was checked prior, static analysis tools and defense-in-depth principles flag `extractall()` as inherently unsafe.
**Learning:** Even with robust pre-validation of zip members via `infolist()`, using `extractall()` nullifies the precision of individual file extraction, leading to implicit trust of the zip contents.
**Prevention:** Avoid `extractall()`. Instead, track validated and sanitized members explicitly in a list, then loop through this safe list to extract files individually using `zip_ref.extract(member, target_dir)`. This enforces defense in depth and appeases security scanners.
