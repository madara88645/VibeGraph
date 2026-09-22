## 2024-03-20 - [Simulation Controls UX]
**Learning:** Found an opportunity to improve the UI of `SimulationControls.jsx` by making the controls easier to interact with and adding a tooltip explanation of disabled states when there are no totalNodes, for example by wrapping ghost runner buttons or other interactive elements in generic HTML elements to attach tooltips for disabled states.
**Action:** Implemented a UX enhancement on the `Ghost Runner` guided tour toggle button to show when it's disabled.
## 2024-03-21 - [Disabled States UX]
**Learning:** Hiding UI elements like the Guided Tour toggle when a project isn't loaded causes confusion. It's better UX to show the element in a disabled state with a tooltip explaining why it's unavailable.
**Action:** Instead of conditionally rendering empty states, I will render the element disabled and wrapped in a span with a helpful tooltip.
