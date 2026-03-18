## 2024-05-18 - Adding Explicit ARIA Tab Semantics for Screen Readers
**Learning:** Custom tab navigations without native HTML semantic tab roles (`role="tablist"`, `role="tab"`, `role="tabpanel"`) are unreadable and inaccessible to screen readers, causing critical navigation blocks.
**Action:** When creating or modifying custom tab navigation in React components, always explicitly add WAI-ARIA tab semantics to ensure screen reader accessibility rather than relying on visual styling.
