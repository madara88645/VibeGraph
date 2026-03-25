## 2026-03-17 - Custom Tab Accessibility
**Learning:** Custom tab implementations without standard ARIA attributes (like role='tablist' and 'aria-selected') are completely inaccessible to screen reader users, appearing merely as unstructured buttons.
**Action:** Always explicitly use WAI-ARIA tab semantics (`role='tablist'`, `role='tab'`, `role='tabpanel'`, and `aria-selected`) when building custom tab navigation instead of relying solely on visual styling.
## 2024-03-24 - Interactive Inputs Missing aria-labels
**Learning:** Found a pattern where interactive text inputs (like `<input>` in SearchBar and `<textarea>` in ChatDrawer) rely solely on `placeholder` text for context. This is insufficient for screen readers as placeholders can disappear when the user starts typing and aren't always reliably announced as labels.
**Action:** When implementing interactive text inputs that lack an explicitly associated `<label>` element, always add an `aria-label` attribute to ensure continuous screen reader accessibility.
