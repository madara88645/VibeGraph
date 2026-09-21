
## 2024-09-22 - Explicit type="button" on Generic Action Buttons
**Learning:** When adding generic action buttons in React components (such as file upload triggers), omitting the `type` attribute defaults them to `type="submit"`. If these are ever wrapped in a `<form>`, they will cause accidental form submissions and page reloads.
**Action:** Always explicitly specify `type="button"` on generic interactive action buttons to prevent accidental default form submissions.
