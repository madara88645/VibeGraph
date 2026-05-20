💡 What: Added `aria-label` attributes to the "Explanation modes" tab buttons and the "Difficulty level" buttons in the Explanation Panel.
🎯 Why: These buttons previously relied solely on visual cues (text and active class state) to convey their purpose. Screen readers would only announce the raw text (e.g., "beginner"), leaving users without context on what the button controlled.
📸 Before/After: N/A (Visual UI is identical, changes are purely structural attributes).
♿ Accessibility: Dramatically improves screen reader navigation by providing explicit context for state toggle controls (e.g., "Set difficulty level to beginner" and "Switch to Analogy tab").
