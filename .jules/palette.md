## 2024-04-24 - Disabled Buttons Tooltips
**Learning:** Browsers natively suppress pointer events (including hover) on disabled buttons, meaning `title` tooltips won't appear. Wrapping the button in a standard `<span>` doesn't always work if the wrapper collapses or loses layout flow.
**Action:** When wrapping a disabled button in a span to show a tooltip, always apply `style={{ display: 'inline-flex' }}` (or `block`/`inline-block` as appropriate) to the wrapper to ensure it perfectly hugs the button and reliably captures hover events.

## 2024-05-18 - Mirroring dynamic title attributes into aria-labels
**Learning:** For dynamic elements rendering within a loop, using a `title` attribute for visual hover context is common. However, screen reader users miss this dynamic context if an `aria-label` is not provided.
**Action:** When extracting complex strings for a `title` (e.g. `Go to node_name (file_name)`), compute it into a local variable and use it for both `title` and `aria-label`.
## 2026-04-29 - Added title to icon-only hamburger button
**Learning:** The hamburger button in App.jsx had an `aria-label` for screen readers but lacked a native `title` attribute, leaving mouse users without a hover tooltip explaining the icon's function.
**Action:** Add a `title` attribute to all icon-only buttons to ensure they provide a tooltip for mouse users in addition to `aria-label` for screen readers.
