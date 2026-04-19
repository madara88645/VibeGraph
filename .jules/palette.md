## 2024-04-18 - Integrated Canvas-Style Upload Modal
**Learning:** UX benefits from avoiding standalone, floating modal dialogs when the action spans the entire core functional area of an app. Converting a file upload modal into a deeply integrated "canvas" view with full-bleed elements, darker backgrounds, and architectural borders creates a more immersive and less interruptive user flow.
**Action:** Transformed the standard `<div className="upload-modal">` structure into a unified container spanning `max-w-4xl max-h-[600px]` with `#131313` background and subtle dashed outlines, matching industrial structural design patterns.

## 2024-04-16 - Add tooltips for visually truncated text
**Learning:** Using `text-overflow: ellipsis` on elements without providing a native `title` attribute creates an accessibility and usability barrier, as users cannot read the full text when it's visually truncated. This pattern was prevalent in sidebars, search results, and tool panels, especially for file paths and long node names.
**Action:** Always pair `text-overflow: ellipsis` with a `title` attribute containing the full text string to ensure native browser tooltips provide the complete content on hover.
