## 2024-05-15 - ARIA Labels on Icon Buttons
**Learning:** Decorative text elements inside buttons (like `{'<>'}` or `📁`) can confuse screen readers if an `aria-label` is added to the parent button but the child element is not hidden.
**Action:** Always add `aria-hidden="true"` to decorative symbols or emojis when wrapping them in a button that receives a descriptive `aria-label`.

## 2024-05-16 - Tooltips on Disabled Buttons
**Learning:** Native `title` tooltips do not appear on standard browsers when placed directly on a `disabled` HTML element, which degrades UX by removing explanatory context.
**Action:** Always wrap `disabled` buttons or inputs in a container element (like a `<span>` with `display: 'inline-flex'`) and apply the `title` attribute to the wrapper instead of the interactive element itself.

## 2024-04-07 - Accessibility of State Indicators and Decorative Elements
**Learning:** In highly interactive React applications like VibeGraph, relying solely on visual cues (like CSS classes for selection) leaves screen reader users without critical state information. Embellishing UI with inline emojis (e.g. ⚡, 📄, 🎯) creates disruptive and noisy voiceover experiences if not explicitly hidden.
**Action:** Always use `aria-current="true"` on the currently selected item within a list or sidebar. Always wrap decorative or inline emojis in a `<span>` with `aria-hidden="true"`.
