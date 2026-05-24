## 🚨 Severity
Low

## 💡 Vulnerability
Missing input sanitization on Pydantic models for user-provided identifiers (`node_id`, `file_path`, `previous_node_id`, `selected_file`).

## 🎯 Impact
Without sanitization, these fields are passed to the AI models which could allow malicious users to execute prompt injection or AI string injection attacks via API endpoints (`/api/ghost-narrate` and `/api/learning-path`).

## 🔧 Fix
Added `@field_validator` with `mode="before"` to `GhostNarrateRequest` and `LearningPathRequest` that applies `sanitize_llm_input(value, truncate=False)` to all relevant string fields to prevent LLM injection.

## ✅ Verification
Automated test suite (`PYTHONPATH=. python -m pytest tests/`) passes locally with no regressions, and the new models correctly redact malicious strings.
