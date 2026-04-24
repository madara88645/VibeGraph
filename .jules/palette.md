
## 2024-04-16 - Add tooltips for visually truncated text
**Learning:** Using `text-overflow: ellipsis` on elements without providing a native `title` attribute creates an accessibility and usability barrier, as users cannot read the full text when it's visually truncated. This pattern was prevalent in sidebars, search results, and tool panels, especially for file paths and long node names.
**Action:** Always pair `text-overflow: ellipsis` with a `title` attribute containing the full text string to ensure native browser tooltips provide the complete content on hover.

## 2024-04-18 - Add ARIA labels to Ghost runner choice buttons
**Learning:** Found an accessibility issue where dynamic buttons in `GhostChoices.jsx` lacked an `aria-label` but had a descriptive `title` attribute. Using dynamic attributes like node filenames/labels is necessary for screen readers to convey context dynamically, especially inside a list or mapping loop.
**Action:** When a `<button>` relies on complex dynamic `title` texts (e.g. ones that show full path + context instead of just raw internal names), mirror that text into the `aria-label` attribute to properly support screen readers.
