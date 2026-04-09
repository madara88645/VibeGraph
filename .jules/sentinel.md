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

## 2025-03-02 - Information Exposure via Unhandled LLM Parsing Errors
**Vulnerability:** When the AI's response failed to parse as valid JSON (due to formatting errors or unexpected output), the `_try_parse_json` utility raised a `ValueError`. The caller functions (`explain_code` and `suggest_learning_path`) caught this error but returned its raw string representation (`str(e)`) to the client, leaking the raw, potentially confusing, or malformed LLM output directly.
**Learning:** Even when errors are caught, returning the raw exception string—especially one containing external API output—violates the principle of failing securely by exposing internal processing details and unvalidated data.
**Prevention:** Catch parsing errors explicitly, log the raw exception internally using `logging.error(..., exc_info=True)` for observability, and always return a sanitized, context-specific fallback message to the client.

## 2025-03-02 - Missing Security Headers (HSTS & CSP)
**Vulnerability:** The `SecurityHeadersMiddleware` provided basic XSS, framing, and sniffing protection, but lacked `Strict-Transport-Security` and `Content-Security-Policy`.
**Learning:** Default security headers are often incomplete; adding HSTS forces secure connections and a basic `default-src 'self'` CSP severely limits injection capabilities (like XSS or external data exfiltration) as a defense-in-depth measure.
**Prevention:** Always verify if a standard security headers configuration covers both Transport Security (HSTS) and Content Restriction (CSP) for robust defense.

## 2025-03-02 - Asymmetric Denial of Service (DoS) via Unbounded Strings in `mode="before"` Validators
**Vulnerability:** Pydantic `max_length` constraints are evaluated *after* `mode="before"` validators. Calling regex-heavy functions like `sanitize_llm_input` with `truncate=False` inside these validators allowed attackers to submit multimegabyte strings that bypassed Pydantic's length checks, causing severe CPU exhaustion (ReDoS).
**Learning:** `mode="before"` validators process the raw, unbounded input before any built-in Pydantic length constraints are applied. Any heavy computation (like regex) performed in this phase without explicit internal bounds is a vector for Asymmetric DoS.
**Prevention:** Always enforce strict length limits natively within the `mode="before"` validator itself (e.g., passing `truncate=True` and an explicit `max_length` to the sanitizer) rather than relying on Pydantic to filter the size post-processing.

## 2024-03-20 - Zip Slip Vulnerability during Symlink Processing
**Vulnerability:** The zip extraction logic in `upload_project` used `os.path.abspath` to sanitize the `extracted_path`. An attacker could create a malicious zip file containing a symlink (e.g. `symlink -> /etc/passwd`) and subsequently write a file *into* that symlink (`symlink/malicious`), bypassing `os.path.abspath` bounds checks because `abspath` does not resolve existing symlinks on the filesystem. This leads to arbitrary file write outside the designated temporary directory.
**Learning:** `os.path.abspath` only normalizes paths lexically (e.g., removing `..` and `.`), but it does not resolve symbolic links. To safely enforce directory boundaries, the path must be resolved using `os.path.realpath`, which resolves both relative segments and symlinks, ensuring the final extraction destination is genuinely within the allowed base directory. Additionally, `os.path.commonpath` effectively validates the resolved paths against the base directory.
**Prevention:** Always use `os.path.realpath` to resolve both the target base directory and the constructed extraction path before applying boundary checks (like `os.path.commonpath([base_dir, resolved_path]) == base_dir`). Always wrap this in a `try-except ValueError` to handle cross-drive paths securely on Windows.
