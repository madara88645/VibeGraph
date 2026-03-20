## 2026-03-17 - Custom Tab Accessibility
**Learning:** Custom tab implementations without standard ARIA attributes (like role='tablist' and 'aria-selected') are completely inaccessible to screen reader users, appearing merely as unstructured buttons.
**Action:** Always explicitly use WAI-ARIA tab semantics (`role='tablist'`, `role='tab'`, `role='tabpanel'`, and `aria-selected`) when building custom tab navigation instead of relying solely on visual styling.
