💡 **What**: Added a visual loading spinner (`vibe-spinner`) to the "Previous step" (`<`) and "Next step" (`>`) navigation buttons in the Learning Path panel when the learning path is being generated.

🎯 **Why**: When a user uploads a project or clicks to generate a new learning path, the AI-generation process can take several seconds. Without a loading state, the UI appeared frozen because the navigation buttons were disabled but otherwise looked identical to their normal state. Adding a spinner provides immediate feedback that the application is processing their request.

📸 **Before/After**:
*Before*: The `<` and `>` buttons were greyed out but showed no active status while generating.
*After*: The `<` and `>` buttons display a pulsing `vibe-spinner` to communicate async loading.

♿ **Accessibility**:
- Added `aria-hidden="true"` to the `vibe-spinner` span to prevent screen readers from redundantly announcing the visual decoration.
- The parent button natively uses a dynamic `aria-label` which clearly announces "Building learning path..." to screen reader users when loading is true, so sighted and non-sighted users receive equivalent context.
