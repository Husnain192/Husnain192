# Contribution graph

Run `python3 scripts/update_contributions.py` from the repository root (Python 3.10+; no dependencies).

The script fetches the public GitHub contribution calendar once, validates a complete consecutive year, and atomically replaces `assets/contributions.svg`. It uses no REST/GraphQL quota, personal access token, or third-party rendering service. Counts match the activity visible on the public profile; private repository details are never requested.

The workflow refreshes daily at 02:23 UTC and can be run manually from Actions → Update contribution graph → Run workflow. Scheduled runs may be delayed or disabled by GitHub after prolonged repository inactivity. A failed fetch or changed HTML format fails the job and keeps the previously committed image visible; check Actions if the displayed update date stops advancing.

Colors and layout are defined in `render()`. The GitHub HTML markup is an external dependency; if it changes, update `CalendarParser` and `parse_calendar`. To reproduce with a saved response, pass `--input calendar.html`.
