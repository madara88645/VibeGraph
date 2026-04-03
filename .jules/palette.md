## 2024-05-15 - ARIA Labels on Icon Buttons
**Learning:** Decorative text elements inside buttons (like `{'<>'}` or `📁`) can confuse screen readers if an `aria-label` is added to the parent button but the child element is not hidden.
**Action:** Always add `aria-hidden="true"` to decorative symbols or emojis when wrapping them in a button that receives a descriptive `aria-label`.
## 2024-05-24 - Add aria-hidden to decorative characters in CodeViewer
**Learning:** The CodeViewer's expand/collapse buttons used raw unicode geometric shapes (⛶ and ✕) as children. Screen readers would read the `aria-label` followed by the confusing unicode character name (e.g. "Expand code, square with corners").
**Action:** Always wrap decorative unicode icons in a `<span aria-hidden="true">` when the button already has an explicit `aria-label`, to prevent redundant and confusing screen reader announcements.
