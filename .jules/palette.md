
## 2024-04-16 - Add tooltips for visually truncated text
**Learning:** Using `text-overflow: ellipsis` on elements without providing a native `title` attribute creates an accessibility and usability barrier, as users cannot read the full text when it's visually truncated. This pattern was prevalent in sidebars, search results, and tool panels, especially for file paths and long node names.
**Action:** Always pair `text-overflow: ellipsis` with a `title` attribute containing the full text string to ensure native browser tooltips provide the complete content on hover.
