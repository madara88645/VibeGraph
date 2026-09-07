
## 2026-09-07 - Prevent Accidental Form Submissions
**Learning:** When adding generic action buttons in React components (such as file upload triggers), they may act as submit buttons if ever wrapped in a `<form>`.
**Action:** Always explicitly specify `type="button"` to prevent accidental default form submissions.
