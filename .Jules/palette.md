## 2024-06-26 - Loading states for async actions
**Learning:** Loading states for async actions (like fetching a demo project) are critical to prevent users from spam-clicking CTA buttons when the result is not instantaneous.
**Action:** Always verify that components handling async logic reflect an active loading state. If the async action is passed down as a prop (e.g. `onLoadDemo`), ensure that a loading flag (e.g. `isDemoLoading`) is also passed down and wired into the disabled state and UI of the interactive element.
