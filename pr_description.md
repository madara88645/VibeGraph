💡 What: Added visual loading spinner to the chat drawer's Send button and wrapped the disabled button in a `span` with an inline-flex display. Updated tests to use `getByRole('button', ...)` for proper targeting.

🎯 Why: To improve visual feedback and accessibility. Mouse users hovering over the disabled Send button will now see the informative tooltip explaining why it's disabled. The loading spinner provides immediate feedback that the chat input is processing.

📸 Before/After: Before, hovering the disabled send button showed no tooltip, and clicking send showed no explicit visual loading indicator on the button. After, the button correctly displays its tooltip context when disabled, and shows a clean spinner while awaiting the AI response.

♿ Accessibility: The wrapper ensures the tooltip functions for mouse users on a disabled button while preserving the explicit `aria-label` for screen reader users via the original button structure.
