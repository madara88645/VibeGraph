## 2024-09-06 - Disabled state UX for file uploads
**Learning:** Disabled file upload buttons (like Browse Folder) require wrappers for tooltip visibility to prevent user confusion during async analysis operations, and they should explicitly define `type="button"`.
**Action:** Always wrap disabled upload action buttons in a `<span>` with a descriptive `title` to maintain context when the button is inactive.
