# Commit graph

Run `python3 scripts/update_commits.py` from the repository root (Python 3.10+, standard library only). Optional `GH_TOKEN` enables authenticated requests; the workflow uses its built-in GitHub token and requires no personal token.

The line chart plots monthly authored commit counts for the latest twelve calendar months, including the partial current month. It queries GitHub commit search with `author:Husnain192 is:public author-date:START..END`. Merge commits are included. GitHub searches default branches only; private repositories, other branches, and commits not linked to the author account are outside this view. Search indexing may lag. These are commit-search totals, not contribution-calendar totals.

One small search response per month supplies `total_count`; totals are not computed from a truncated page of results. Twelve requests run once daily, with pacing. Profile views load a committed SVG and make no API calls. The graph avoids shared card-service quotas, but its daily updater remains subject to GitHub's API availability and limits.

The workflow runs at 02:23 UTC daily and can also be triggered under Actions → Update commit graph → Run workflow. Failed requests or incomplete search results fail before replacing the last graph. GitHub may delay schedules or disable them after prolonged repository inactivity.

`assets/commits.json` records the monthly counts. Re-render without networking using `python3 scripts/update_commits.py --input assets/commits.json`. Styling is in `render()`.
