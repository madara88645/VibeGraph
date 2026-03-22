## 2026-03-17 - Custom Tab Accessibility
**Learning:** Custom tab implementations without standard ARIA attributes (like role='tablist' and 'aria-selected') are completely inaccessible to screen reader users, appearing merely as unstructured buttons.
**Action:** Always explicitly use WAI-ARIA tab semantics (`role='tablist'`, `role='tab'`, `role='tabpanel'`, and `aria-selected`) when building custom tab navigation instead of relying solely on visual styling.

## 2024-05-18 - Missing ARIA label on Text Inputs
**Learning:** Found interactive `<input>` and `<textarea>` elements relying solely on `placeholder` attributes for context, which is insufficient for screen readers as they may just announce "edit text".
**Action:** Always ensure interactive inputs without an associated `<label>` element include an explicit `aria-label` to provide proper context to assistive technologies.
