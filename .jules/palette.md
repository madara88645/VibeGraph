## 2024-05-15 - ARIA Labels on Icon Buttons
**Learning:** Decorative text elements inside buttons (like `{'<>'}` or `📁`) can confuse screen readers if an `aria-label` is added to the parent button but the child element is not hidden.
**Action:** Always add `aria-hidden="true"` to decorative symbols or emojis when wrapping them in a button that receives a descriptive `aria-label`.

## 2024-05-16 - Tooltips on Disabled Buttons
**Learning:** Native `title` tooltips do not appear on standard browsers when placed directly on a `disabled` HTML element, which degrades UX by removing explanatory context.
**Action:** Always wrap `disabled` buttons or inputs in a container element (like a `<span>` with `display: 'inline-flex'`) and apply the `title` attribute to the wrapper instead of the interactive element itself.

## 2024-05-17 - Accessible Combobox Pattern for Search
**Learning:** When implementing a search input with auto-complete or dropdown suggestions, using standard elements like inputs and buttons is not enough for screen readers. They need to understand the relationship between the text input and the list of suggestions.
**Action:** Always apply the ARIA combobox pattern to search components. Give the input `role="combobox"`, `aria-expanded`, `aria-controls` (linking to the listbox ID), `aria-autocomplete="list"`, and `aria-activedescendant` (linking to the active option ID). The suggestion container should have `role="listbox"` and items should have `role="option"` with `aria-selected` reflecting keyboard focus.

## 2024-05-18 - Mirroring dynamic title attributes into aria-labels
**Learning:** For dynamic elements rendering within a loop, using a `title` attribute for visual hover context is common. However, screen reader users miss this dynamic context if an `aria-label` is not provided.
**Action:** When extracting complex strings for a `title` (e.g. `Go to node_name (file_name)`), compute it into a local variable and use it for both `title` and `aria-label`.

## 2024-05-02 - Empty Upload Validation
**Learning:** The native file picker handles empty directories gracefully, but drag-and-drop operations on directory dropzones can easily result in empty `files` arrays if the dropped item is not properly readable or just an empty folder.
**Action:** Always add explicit client-side validation logic (e.g. `files.length === 0`) before attempting to construct form data and making backend upload requests.

## 2024-04-24 - Disabled Buttons Tooltips
**Learning:** Browsers natively suppress pointer events (including hover) on disabled buttons, meaning `title` tooltips won't appear. Wrapping the button in a standard `<span>` doesn't always work if the wrapper collapses or loses layout flow.
**Action:** When wrapping a disabled button in a span to show a tooltip, always apply `style={{ display: 'inline-flex' }}` (or `block`/`inline-block` as appropriate) to the wrapper to ensure it perfectly hugs the button and reliably captures hover events.

## 2026-04-29 - Added title to icon-only hamburger button
**Learning:** The hamburger button in App.jsx had an `aria-label` for screen readers but lacked a native `title` attribute, leaving mouse users without a hover tooltip explaining the icon's function.
**Action:** Add a `title` attribute to all icon-only buttons to ensure they provide a tooltip for mouse users in addition to `aria-label` for screen readers.

## 2024-05-23 - Context-Rich Buttons in Lists
**Learning:** When rendering dynamic buttons in lists or maps that utilize complex `title` attributes for rich context (like hint descriptions), screen reader users are excluded if the text isn't mirrored into `aria-label`.
**Action:** Always mirror dynamic or context-rich `title` strings directly into `aria-label` attributes for list-generated interactive elements to guarantee equivalent descriptive context for all users.
