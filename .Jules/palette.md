## 2026-03-17 - Custom Tab Accessibility
**Learning:** Custom tab implementations without standard ARIA attributes (like role='tablist' and 'aria-selected') are completely inaccessible to screen reader users, appearing merely as unstructured buttons.
**Action:** Always explicitly use WAI-ARIA tab semantics (`role='tablist'`, `role='tab'`, `role='tabpanel'`, and `aria-selected`) when building custom tab navigation instead of relying solely on visual styling.
## 2026-03-24 - Text Inputs Need Explicit Labels
**Learning:** Interactive text inputs (like `<input>` or `<textarea>`) that rely solely on `placeholder` text are insufficient for screen readers and can create accessibility barriers. Even if a field is visually self-explanatory via its placeholder, it must be explicitly labeled.
**Action:** Always ensure any text input or textarea without an explicitly associated `<label>` element includes an `aria-label` attribute for proper screen reader announcement.
