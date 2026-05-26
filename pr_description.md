## 🚨 Severity: MEDIUM
## 💡 Vulnerability: Missing Prompt Injection Validation
In `app/models.py`, while identifiers like `node_id` and `file_path` were properly sanitized against prompt injection, other user-provided identifiers like `previous_node_id` and `selected_file` were missing from the `@field_validator` targeting prompt injection in endpoints like `GhostNarrateRequest` and `LearningPathRequest`.

## 🎯 Impact:
Attackers could craft payloads in contextual inputs (`previous_node_id` or `selected_file`) that would bypass the LLM input filter, potentially allowing prompt injections to alter the AI narration or learning path responses.

## 🔧 Fix:
Updated the `@field_validator` in `app/models.py` to explicitly target `node_id`, `file_path`, `previous_node_id`, and `selected_file` using `check_fields=False` to safely share the validator across multiple models. Added robust test coverage in `tests/test_models.py` to guarantee behavior.

## ✅ Verification:
Run `pytest tests/test_models.py` to verify that `[filtered]` tags are correctly applied to `previous_node_id` and `selected_file`.
