GitHub Projects Dataset Sync

What this does
- Exports your GitHub repo metadata (OWNER + COLLABORATOR + ORG_MEMBER) via `gh api graphql`.
- Writes JSON, JSONL, and CSV datasets.
- Also copies the most recent outputs into ./latest/ so your website can always read stable paths.

How to run
1) Ensure `gh` is installed and authenticated:
   gh auth status

2) Run the sync:
   bash /home/al/Projects/.data/github-projects-dataset/sync.sh

Outputs
- Timestamped folder:
  /home/al/Projects/.data/github-projects-dataset/<UTC_TIMESTAMP>/

- Stable latest folder:
  /home/al/Projects/.data/github-projects-dataset/latest/

Files
- github_repos_all.json
- github_repos_all.jsonl
- github_repos_all.csv

Notes
- Topics: up to 50 per repo.
- Description/homepage may be empty depending on repo settings.
- Collaborator/org-member repos will include ones you have access to, not only your own.
