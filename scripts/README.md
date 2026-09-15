# Commit graph

Run `python3 scripts/update_commits.py` from the repository root (Python 3.10+, standard library only). Optional `GH_TOKEN` enables authenticated requests; the workflow uses its built-in GitHub token and requires no personal token.

The line chart plots monthly authored commit counts for the latest twelve calendar months, including the partial current month. By default it queries GitHub commit search with `author:Husnain192 is:public author-date:START..END`. With PROFILE_STATS_TOKEN it removes the visibility filter to combine public and accessible private commits. Merge commits are included. GitHub searches default branches only; other branches and commits not linked to the author account are outside this view. Private repositories are included when PROFILE_STATS_TOKEN is configured. Search indexing may lag. These are commit-search totals, not contribution-calendar totals.

One small search response per month supplies `total_count`; totals are not computed from a truncated page of results. Twelve requests run once daily, with pacing. Profile views load a committed SVG and make no API calls. The graph avoids shared card-service quotas, but its daily updater remains subject to GitHub's API availability and limits.

The workflow runs at 02:23 UTC daily and can also be triggered under Actions → Update commit graph → Run workflow. Failed requests or incomplete search results fail before replacing the last graph. GitHub may delay schedules or disable them after prolonged repository inactivity.

`assets/commits.json` records the monthly counts. Re-render without networking using `python3 scripts/update_commits.py --input assets/commits.json`. Styling is in `render()`.

## Enable public + private totals

Create a personal access token that can read the private repositories you want counted, then add it as the repository Actions secret `PROFILE_STATS_TOKEN` under Settings → Secrets and variables → Actions. For a fine-grained token, select the repository owner and desired private repositories, with Contents: read-only. Organization approval or SSO authorization may be required. Fine-grained tokens are scoped to one resource owner; repositories outside the token's access will not be counted.

Run Actions → Update commit graph → Run workflow, or wait for the daily run. The chart switches to “Public + accessible private” and combines the counts into one line. Without this secret it stays explicitly public-only. If a configured token expires or a request fails, the job fails and keeps the last snapshot.

Only monthly combined counts, dates, username, and scope are saved. Commit-search response items (including any private repository names, commit messages, and SHAs) are discarded and never written to the repository or logs. The token is passed only to the data-generation step; commits are pushed with the built-in workflow token.

Locally, use the `PROFILE_STATS_TOKEN` environment variable for combined mode. Do not commit the token or send it in chat.
