## 2026-09-10 - Added disabled states and type button to upload actions
**Learning:** Generic action buttons in forms can trigger unexpected submits if type is not set, and buttons should be disabled during async operations to prevent double submissions or invalid state.
**Action:** Always add type="button" to generic action buttons and disable interactive elements when async operations like uploads/analysis are in progress.
