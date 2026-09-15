import datetime

entry = f"""## {datetime.date.today().strftime('%Y-%m-%d')} - Add explicit type to action buttons
**Learning:** Generic action buttons in React components (such as file upload triggers) should explicitly declare `type="button"`. If they omit it, they default to `type="submit"`. If the component containing them is ever wrapped in a `<form>`, clicking these buttons will inadvertently trigger a form submission or page reload instead of the intended JavaScript action.
**Action:** Always explicitly specify `type="button"` on non-submit buttons in React to prevent unintended default form submissions and ensure robust behavior in any context.
"""

with open('.jules/palette.md', 'a') as f:
    f.write('\n' + entry)
