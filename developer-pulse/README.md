# Developer Pulse

A zero-build, interactive dashboard for exploring the public repository portfolio of [Husnain192](https://github.com/Husnain192).

Unlike conventional GitHub profile cards, Developer Pulse emphasizes:

- repository freshness and maintenance signals
- original-work versus fork composition
- technology breadth across original projects
- searchable, filterable repository context

## Run locally

Open `index.html` in a browser. No dependencies, build step, token, or environment variables are required.

The dashboard uses GitHub's public REST API and caches responses in the browser for 15 minutes. Unauthenticated GitHub API rate limits apply.

## Deployment

The included GitHub Actions workflow deploys this directory to GitHub Pages after changes reach `main`.