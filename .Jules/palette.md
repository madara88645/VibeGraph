## 2024-07-23 - Wrapping disabled buttons for tooltip accessibility
**Learning:** Disabled HTML buttons do not trigger mouse events, preventing `title` tooltips from rendering on hover.
**Action:** To ensure users receive adequate feedback for why an action is unavailable (e.g., 'Export in progress...'), wrap the disabled button in a standard DOM element (like `<span style={{ display: 'inline-flex' }}>`) and apply the `title` attribute to the wrapper.
