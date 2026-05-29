> **Read first:** [instructions.md](./instructions.md). Past learnings only — do not apply repo-wide without a task-specific reason.

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

## 2024-05-02 - Mirror Dynamic Tooltips to Aria-Labels
**Learning:** When dynamic buttons in lists use `title` for rich contextual information (like full file paths), screen reader users are excluded if that context isn't mapped to ARIA attributes.
**Action:** Always mirror complex dynamic `title` attributes into `aria-label` directly on the `<button>` element to ensure consistent descriptive context for all users.

## 2024-05-23 - Context-Rich Buttons in Lists
**Learning:** When rendering dynamic buttons in lists or maps that utilize complex `title` attributes for rich context (like hint descriptions), screen reader users are excluded if the text isn't mirrored into `aria-label`.
**Action:** Always mirror dynamic or context-rich `title` strings directly into `aria-label` attributes for list-generated interactive elements to guarantee equivalent descriptive context for all users.

## 2024-05-30 - Context-Rich Buttons with Nested Elements
**Learning:** When rendering buttons that contain multiple text elements (e.g., an icon, a label, and a filename) and utilize complex `title` attributes for rich context, a screen reader may read the internal spans in a disjointed way while missing the combined context of the tooltip.
**Action:** Assign an explicit, combined `aria-label` to the parent button that mirrors the rich context of the `title` attributes. This creates a natural, consolidated sentence for screen readers and ensures parity with the descriptive context sighted users receive via tooltips.
## 2024-05-19 - Screen Readers Announcing Inline Text Emojis
**Learning:** Decorative text emojis placed directly inline within labels or buttons are announced by screen readers (e.g., "document icon filename"), causing a confusing auditory experience that disrupts the natural reading flow of the context.
**Action:** Always wrap decorative inline emojis in a `<span>` element with `aria-hidden="true"` to hide them from screen readers while preserving visual layout.

## 2024-05-24 - Dynamic Context Hidden by Static aria-label
**Learning:** When using static `aria-label`s on buttons (like `aria-label={file}` or `aria-label="Choose traversal strategy"`), any visually nested elements containing dynamic context (such as node counts, types, or current state hints) are overridden and hidden from screen readers. Screen reader users receive less context than sighted users.
**Action:** Always dynamically build `aria-label` strings to include all the relevant information that is visually nested within the component or implicitly conveyed by its state, ensuring parity between visual and auditory context.


## 2024-05-13 - [Explicit Visually Hidden Labels Improve Screen Reader Compatibility]
**Learning:** While `aria-label` provides accessible names to inputs, explicitly adding a visually hidden `<label>` element with an `htmlFor` attribute linking to the input's `id` provides more robust backwards compatibility across a wider array of older screen readers and voice navigation tools, ensuring the accessible name is never missed.
**Action:** When creating text inputs (`<textarea>`, `<input type="text">`, or even hidden `<input type="file">` triggered via other elements), default to adding an explicitly linked, visually hidden `<label>` rather than relying exclusively on `aria-label`.
## 2026-05-18 - Add keyboard shortcuts to Ghost Choices

**Learning:** When attaching a global keyboard shortcut event listener (e.g., `window.addEventListener('keydown', ...)`) in React components to improve interaction speed, explicitly ignore interactions where modifier keys are active (`e.ctrlKey || e.metaKey || e.altKey`) and where the active element is an input or textarea (`['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)`) to prevent interfering with default browser behaviors and text entry.
**Action:** Always wrap `keydown` event listener logic in React components with a guard clause that checks the `e` object for modifiers and the `document.activeElement.tagName` to prevent unintended UI triggering.

## 2026-05-15 - Add Loading State and Disable Feedback to GraphViewer Export Buttons
**Learning:** Exporting a large react flow graph to PNG/SVG with html-to-image can be a slow, async operation. If async buttons lack a loading state (isExporting) and are not disabled during the operation, users lack visual feedback and might trigger multiple concurrent expensive operations. When adding title to a disabled button, wrapping the button in a <span style={{ display: 'inline-flex' }}> allows the title tooltip to show properly on disabled elements.
**Action:** Always add loading spinners (.vibe-spinner), a disabled state, and matching aria-labels to async action buttons. Update corresponding UI test queries to use getByRole('button') instead of getByTitle() since the title resides on the wrapper span.
## 2026-05-18 - Chat Drawer Send Button Missing Visual Disabled Feedback
**Learning:** The chat drawer "send" button lacked clear disabled feedback and lacked visual appeal when loading. Adding a loading spinner (`vibe-spinner`) and standardizing the send icon improves visual feedback. Wrapping a disabled button with a `span` containing `style={{ display: 'inline-flex' }}` ensures the tooltip functions for mouse users, and testing these requires using `getByRole` rather than `getByLabelText` to avoid conflict with the wrapper title.
**Action:** When creating async buttons like a chat send, add explicit visual loading feedback (like a spinner). Ensure tests use `getByRole('button', ...)` for proper semantic targeting and avoiding wrapper title collisions.

## 2024-05-31 - Missing Aria-Labels on State Toggle Buttons
**Learning:** Buttons that act as state toggles (like tab selectors or difficulty level choices) often rely purely on visual cues (like text and an 'active' class) to convey their purpose. Without an explicit `aria-label`, screen readers might only announce the raw text (e.g., "beginner"), leaving users without context about what the button controls.
**Action:** Always add descriptive `aria-label` attributes to state toggle buttons (e.g., `aria-label="Set difficulty level to beginner"`) to ensure screen reader users receive the same contextual understanding as sighted users.

## 2024-05-31 - Missing Aria-Labels on State Toggle Buttons
**Learning:** Buttons that act as state toggles (like difficulty level choices or speed selectors) often rely purely on visual cues (like text and an 'active' class) to convey their purpose. Without an explicit `aria-label`, screen readers might only announce the raw text (e.g., "Fast"), leaving users without context about what the button controls.
**Action:** Always add descriptive `aria-label` attributes to state toggle buttons (e.g., `aria-label="Set simulation speed to Fast"`) to ensure screen reader users receive the same contextual understanding as sighted users. Note: This does not apply to elements with `role="tab"`, as screen readers natively announce tab states implicitly.

## 2026-05-24 - Accessible Chat Conversations
**Learning:** When implementing a chat interface, sighted users rely on visual cues (like message alignment, bubble color, and animated typing dots) to understand conversational flow. Screen readers, however, will read these linearly as plain text without context of who is speaking, and might ignore or stutter on CSS-animated typing dots.
**Action:** Always add `role="log"` to the chat message container so new messages are announced automatically. Within each message, prepend a visually hidden span indicating the speaker (e.g., "You:", "AI:"). Finally, wrap typing indicators with a visually hidden "AI is typing..." and apply `aria-hidden="true"` to any decorative animated elements.
<<<<<<< Updated upstream

## 2024-05-25 - Appending keyboard shortcuts to Title and Aria-Label
**Learning:** When indicating keyboard shortcuts via visually hidden `<kbd>` tags inside interactive elements, screen readers may not announce the hidden text natively, leaving non-sighted users unaware of the keyboard shortcut options.
**Action:** When defining interactive options that have explicit keyboard shortcuts, dynamically build both the `title` and `aria-label` strings to append the shortcut hint (e.g. `(Press 1)`), ensuring screen reader users and mouse users have parity on keyboard affordances.
=======
## 2026-06-03 - Inline Text Emojis
**Learning:** Decorative text emojis (e.g. 💡, 👻) placed directly inline within labels, panels, or component text are announced by screen readers, which can disrupt the user's natural auditory reading flow.
**Action:** Always wrap decorative inline emojis in a `<span>` element with `aria-hidden="true"` to hide them from screen readers while preserving the visual layout.
>>>>>>> Stashed changes
## 2026-06-03 - Inline Text Emojis
**Learning:** Decorative text emojis (e.g. 💡, 👻) placed directly inline within labels, panels, or component text are announced by screen readers, which can disrupt the user's natural auditory reading flow.
**Action:** Always wrap decorative inline emojis in a `<span>` element with `aria-hidden="true"` to hide them from screen readers while preserving the visual layout.
