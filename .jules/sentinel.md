## 2024-05-14 - Security Headers Added to FastAPI Backend
**Vulnerability:** The FastAPI backend (`serve.py`) was serving all responses without fundamental security headers (like `X-Frame-Options`, `X-Content-Type-Options`, and `Strict-Transport-Security`). While CORS was configured, other web vulnerabilities (clickjacking, MIME sniffing, legacy XSS vectors) were exposed.
**Learning:** In minimal fast-prototyping codebases (like this React+FastAPI project), default configurations omit basic security headers. It's a common oversight since the focus is usually on logic and cross-origin setup.
**Prevention:** Implementing a global `@app.middleware("http")` function in FastAPI to attach baseline headers ensures that all existing and future endpoints inherit standard protections by default.
