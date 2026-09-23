## 2026-09-23 - Added type and aria-label to upload buttons
**Learning:** Generic action buttons (like file upload triggers) missing `type="button"` and `aria-label` can cause accidental form submissions and lack full descriptive context for screen readers.
**Action:** Always explicitly specify `type="button"` on non-submit buttons and add descriptive `aria-label`s for better accessibility.
