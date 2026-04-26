## 2024-04-24 - Disabled Buttons Tooltips
**Learning:** Browsers natively suppress pointer events (including hover) on disabled buttons, meaning `title` tooltips won't appear. Wrapping the button in a standard `<span>` doesn't always work if the wrapper collapses or loses layout flow.
**Action:** When wrapping a disabled button in a span to show a tooltip, always apply `style={{ display: 'inline-flex' }}` (or `block`/`inline-block` as appropriate) to the wrapper to ensure it perfectly hugs the button and reliably captures hover events.
