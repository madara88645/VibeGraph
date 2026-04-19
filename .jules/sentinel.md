## 2024-05-24 - Information Disclosure via Absolute File Paths
**Vulnerability:** Backend API error handlers and data payload extractors were directly embedding full system file paths into error messages (e.g., `SyntaxError` extractions, `Path not found` errors).
**Learning:** Returning full file paths in exceptions or string formats exposes sensitive infrastructure and directory structures to the client, providing attackers with insights into the backend file layout which can be chained for further exploitation.
**Prevention:** Always wrap reflected paths in `os.path.basename()` before formatting them into user-facing output or API responses.
