🚨 Severity: HIGH
💡 Vulnerability: Information Disclosure (Arbitrary File Read) via `cwd` fallback in `is_safe_path`. Attackers could exploit code analysis endpoints (`/api/snippet`, `/api/explain`, `/api/learning-path`) to read the server's own internal source code, dependencies, and configuration files.
🎯 Impact: Attackers could gain deep insight into the server's environment and application logic, potentially uncovering secondary vulnerabilities or sensitive infrastructure details.
🔧 Fix: Removed the `cwd` allowance from `is_safe_path` in `app/utils/security.py`, strictly limiting read access to the designated temporary upload boundaries (`UPLOAD_PREFIX` and `vibegraph_test_`). Updated test payloads to dynamically mock files within these boundaries.
✅ Verification: Ran the full backend test suite (`pytest tests/`) to ensure no regressions. Tests asserting the block of `serve.py` confirm the vulnerability is mitigated.
