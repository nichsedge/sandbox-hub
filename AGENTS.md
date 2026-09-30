# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this repo is

Personal sandbox: loose scripts, notebooks, dbt projects, and infra configs. Six domains:

- `analysis/` — data engineering & analysis (dbt-BigQuery/DuckDB projects, crypto fetchers, analysis scripts)
- `ai/` — GenAI demos, Whisper transcription, gTTS text-to-audio
- `tools/` — standalone utilities (`automation/`, `email-py/`, `social/reddit.py`)
- `study/` — coursework scripts
- `infra/` — Airflow setup and Docker Compose stacks
- `career/` — course work and recruitment take-homes (historical; don't refactor)

## Package management

- **uv only.** Never pip/conda/poetry. No root pyproject.toml — each sub-project manages itself.
- Two patterns coexist:
  1. **PEP 723 inline-dependency scripts** (~10 under `tools/` and `analysis/crypto-data/`): deps declared in a `# /// script` block at the top → just `uv run <script.py>`. Don't extract them into pyprojects unless asked.
  2. **Sub-projects** (`pyproject.toml` + `uv.lock`, e.g. `analysis/dbt-bq`, `ai/video2text`, `tools/email-py`): `uv sync` then `uv run …`.
- Per-project Python pins differ intentionally (`.python-version`: 3.11–3.13). Don't unify them.

## Running / verifying

- No test suite, no CI. Verify changes by running the changed script/command (smoke run), not by adding tests.
- Sharia banking DW end-to-end: `cd analysis/dbt-bq && uv run sharia_banking_dw/scripts/run_sharia_dw.py`
- dbt commands there need profiles next to the project: `cd sharia_banking_dw/dbt_project && uv run dbt build --profiles-dir .`
- Airflow: `cd infra/airflow && bash install.sh && bash start.sh`

## Secrets & config

- Never hardcode credentials or commit `.env` files. Pattern: `<name>.env-template` committed, real `.env` gitignored (see `tools/social/`).
- `.envrc` sources secrets from outside this repo (`~/Projects/dotfiles-private/env/sandbox-hub.env`) — keep it that way.
- Local-dev defaults in `infra/` compose files (e.g. `password: postgres`) are intentional; leave them.

## Repo hygiene

- Generated artifacts stay uncommitted: `*.duckdb`, `airflow.db`, `.venv/` (e.g. `analysis/dbt-bq/.venv`), dataset outputs.
- Python scripts over notebooks: Active domains (`analysis/`, `study/`, `tools/`) use pure `.py` scripts for AI agent friendliness and clean diffs. Convert new notebooks via `uv run tools/automation/ipynb_to_py.py`. Historical `career/` notebooks retain `.ipynb`; clear outputs before committing (`uv run tools/automation/reset_ipynb.py`).
- Commits follow Conventional Commits (`feat:`, `fix:`, `docs:`), one concern per commit.
