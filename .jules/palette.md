## 2024-05-15 - ARIA Labels on Icon Buttons
**Learning:** Decorative text elements inside buttons (like `{'<>'}` or `📁`) can confuse screen readers if an `aria-label` is added to the parent button but the child element is not hidden.
**Action:** Always add `aria-hidden="true"` to decorative symbols or emojis when wrapping them in a button that receives a descriptive `aria-label`.

## 2024-05-16 - Tooltips on Disabled Buttons
**Learning:** Native `title` tooltips do not appear on standard browsers when placed directly on a `disabled` HTML element, which degrades UX by removing explanatory context.
**Action:** Always wrap `disabled` buttons or inputs in a container element (like a `<span>` with `display: 'inline-flex'`) and apply the `title` attribute to the wrapper instead of the interactive element itself.

## 2024-05-17 - Accessible Combobox Pattern for Search
**Learning:** When implementing a search input with auto-complete or dropdown suggestions, using standard elements like inputs and buttons is not enough for screen readers. They need to understand the relationship between the text input and the list of suggestions.
**Action:** Always apply the ARIA combobox pattern to search components. Give the input `role="combobox"`, `aria-expanded`, `aria-controls` (linking to the listbox ID), `aria-autocomplete="list"`, and `aria-activedescendant` (linking to the active option ID). The suggestion container should have `role="listbox"` and items should have `role="option"` with `aria-selected` reflecting keyboard focus.

## 2024-05-18 - ARIA Hidden on Decorative Button Characters
**Learning:** Decorative text characters like "x" inside buttons can confuse screen readers if an `aria-label` is already present on the parent button. The screen reader will announce both the label and the text character sequentially.
**Action:** Always add `aria-hidden="true"` to decorative characters or symbols when wrapping them in a button that receives a descriptive `aria-label`.
