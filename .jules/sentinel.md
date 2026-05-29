## 2026-05-28 - Secure Authentication with Constant-Time Comparison

**Vulnerability:** Timing attack risk when comparing sensitive tokens, and code pollution.
**Learning:** Standard string comparisons (`==`, `!=`) for tokens can leak information about the token's characters via timing differences. Also, internal protected methods (like `_get_bearer_token`) should not be used in external files.
**Prevention:** Use `secrets.compare_digest` for secure token validation. Clean up temporary scratchpad files before creating a PR, and expose an official public interface when a function is needed across multiple modules.