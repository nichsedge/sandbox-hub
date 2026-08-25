# 🧪 sandbox-hub

A personal sandbox of Python scripts, notebooks, dbt projects, and infrastructure configs spanning **data engineering**, **AI/GenAI**, **speech processing**, **web scraping**, and **data analysis** — with an Indonesian context.

Repository layout: [`analysis/`](./analysis) · [`ai/`](./ai) · [`tools/`](./tools) · [`study/`](./study) · [`infra/`](./infra) · [`career/`](./career)

---

## 📊 Data Engineering & Analysis (`analysis/`)

| Project | Description |
|---|---|
| [`dbt-bq/sharia_banking_dw/`](./analysis/dbt-bq/sharia_banking_dw) | Indonesian Sharia banking data warehouse simulation: dbt-duckdb Medallion models (staging → intermediate → marts) covering Nisbah profit-sharing, financing portfolio quality (OJK), Zakat & purification; orchestrated via Astronomer Cosmos on Airflow |
| [`dbt-bq/bigquery_experiments/`](./analysis/dbt-bq/bigquery_experiments) | dbt-BigQuery research sandbox — dynamic vs static partition insert-overwrite and indirect test selection, with write-ups in [`docs/`](./analysis/dbt-bq/bigquery_experiments/docs) |
| [`crypto-data/`](./analysis/crypto-data) | Fetch crypto data from Binance (CSV export parser) and CoinGecko API; query Solana token balances by wallet (Alchemy) |
| [`finance/`](./analysis/finance) | Notebooks: recession indicators (`recession.ipynb`), Forbes wealth data (`forbes.ipynb`), Taleb-style fat-tails explorations (`taleb.ipynb`) |
| [`indonesia-elections/`](./analysis/indonesia-elections) | Analysis of the 2024 Indonesian General Election |
| [`religious-diversity-analysis/`](./analysis/religious-diversity-analysis) | Religious diversity across Indonesian organizations |

## 🤖 AI / GenAI (`ai/`)

| Project | Description |
|---|---|
| [`genai-demo/`](./ai/genai-demo) | LangChain, LlamaIndex, OpenAI, Gemini, OpenRouter, LangSmith, and Ollama local-LLM demos |
| [`video2text/`](./ai/video2text) | Transcribe `.mkv` video files to text using OpenAI Whisper (FFmpeg + GPU support) |
| [`text2audio/`](./ai/text2audio) | Convert Markdown text to speech (MP3) using gTTS — supports Indonesian |
| [`computer-vision/compress_images_in_current_folder.py`](./ai/computer-vision/compress_images_in_current_folder.py) | Batch-compress all images in a directory |

## 🕷️ Web Scraping

| Script | Description |
|---|---|
| [`tools/social/reddit.py`](./tools/social/reddit.py) | Scrape Reddit posts and comments across mental health subreddits using PRAW + Pushshift API ([analysis notebook](./tools/social/reddit.ipynb)) |
| [`study/academic/asdosan_scele.py`](./study/academic/asdosan_scele.py) | Scrape course/assignment data from SCELE (University of Indonesia's LMS) |

## 🛠️ Utilities (`tools/`)

| Script / Tool | Description |
|---|---|
| [`automation/mp3_to_txt.py`](./tools/automation/mp3_to_txt.py) | Transcribe MP3 audio to text via OpenAI's GPT-4o transcription API, chunked for long files |
| [`automation/translate_srt.py`](./tools/automation/translate_srt.py) | Translate SRT subtitle files while preserving cue timing |
| [`automation/gutenberg.py`](./tools/automation/gutenberg.py) | Download Honoré de Balzac books from Project Gutenberg and translate them to Indonesian |
| [`automation/extract_amounts.py`](./tools/automation/extract_amounts.py) | Extract monetary amounts from PDF files (pdfplumber) |
| [`automation/extract_transactions.py`](./tools/automation/extract_transactions.py) | Parse transactions from HTML into CSV (BeautifulSoup) |
| [`automation/fatsecret_barcode.py`](./tools/automation/fatsecret_barcode.py) | Fetch food nutrition details from FatSecret by barcode (supports local `.env` credentials) |
| [`automation/reset_ipynb.py`](./tools/automation/reset_ipynb.py) | Clear all outputs from Jupyter notebooks |
| [`automation/rm_pw_pdf.py`](./tools/automation/rm_pw_pdf.py) | Remove password protection from PDF files |
| [`automation/speed_test.py`](./tools/automation/speed_test.py) | Run an internet speed test from the CLI |
| [`automation/extract_gh_projects/`](./tools/automation/extract_gh_projects) | Export GitHub repo metadata datasets (JSON/JSONL/CSV) via `gh api graphql` |
| [`email-py/`](./tools/email-py) | IMAP/SMTP toolkit: Ethereal test-account read/send, Gmail unread checks, email→ticket polling service |

## 📚 Study (`study/`)

| Notebook | Description |
|---|---|
| [`math/numerical_method.ipynb`](./study/math/numerical_method.ipynb) | Numerical methods implementations |
| [`math/travelling-salesman-problem.ipynb`](./study/math/travelling-salesman-problem.ipynb) | TSP solver experiments |
| [`academic/siakng_transcript_to_obsidian.ipynb`](./study/academic/siakng_transcript_to_obsidian.ipynb) | Convert SIAK-NG academic transcripts to Obsidian-compatible Markdown |

## 🏗️ Infrastructure (`infra/`)

| Path | Description |
|---|---|
| [`airflow/`](./infra/airflow) | Standalone Apache Airflow setup (`install.sh`, `start.sh`, `stop.sh`) with weekly DAGs: CSV → PostgreSQL → BigQuery (`movie_weekly`) and web scraping (`scrape_weekly`) |
| [`docker-compose/`](./infra/docker-compose) | Docker/Podman Compose configs for local stacks: PostgreSQL, MongoDB, Kafka, Redpanda, RabbitMQ, Neo4j (+ genealogy & IDX variants), Memgraph, Spark, Flink + Iceberg, Grafana, InfluxDB, Nextcloud, Odoo, Portainer, ingress, Cloudera Streaming |

## 💼 Courses (`career/courses/`)

| Project | Description |
|---|---|
| [`rakamin-idx/`](./career/courses/rakamin-idx) | Rakamin × IDX Partners virtual internship |
| [`rakamin-btps/`](./career/courses/rakamin-btps) | Rakamin × Bank BTPN Syariah virtual internship |
| [`rakamin-muamalat/`](./career/courses/rakamin-muamalat) | Rakamin × Bank Muamalat virtual internship |
| [`forage-JPMC_quantitative-research/`](./career/courses/forage-JPMC_quantitative-research) | JP Morgan Chase Quantitative Research job simulation (Forage) |

## 💼 Recruitment Challenges (`career/recruitment/`)

Coding tests and take-home assignments for DE/DS/BE roles — see [`Recruitment.md`](./career/recruitment/Recruitment.md):

[`bitwyre-be/`](./career/recruitment/bitwyre-be) (Flask + Kafka backend) · [`cadit-de/`](./career/recruitment/cadit-de) · [`linkaja-de/`](./career/recruitment/linkaja-de) · [`mileapp-ds/`](./career/recruitment/mileapp-ds) · [`tel-de/`](./career/recruitment/tel-de) (Airflow + Great Expectations pipelines)

---

## 🛠️ Tech Stack

- **Languages**: Python, SQL
- **Analytics engineering**: dbt (DuckDB & BigQuery), Astronomer Cosmos
- **Orchestration**: Apache Airflow
- **Databases / streaming**: PostgreSQL, DuckDB, Google BigQuery, Kafka / Redpanda
- **AI/ML**: OpenAI API, Whisper, LangChain, LlamaIndex, Ollama
- **Data Analysis**: Pandas, Jupyter Notebook
- **Speech & media**: gTTS, pydub, FFmpeg
- **Scraping**: PRAW, Pushshift, BeautifulSoup, Requests
- **Infrastructure**: Docker / Podman Compose
- **Package Manager**: [uv](https://github.com/astral-sh/uv)

---

## ⚡ Quick Start

Most standalone scripts use [uv](https://github.com/astral-sh/uv) inline dependencies:

```bash
uv run tools/automation/mp3_to_txt.py
```

For sub-projects with a `pyproject.toml`:

```bash
cd <project-folder>   # e.g. analysis/crypto-data
uv sync
uv run main.py        # or the script you need
```

Run the Sharia banking DW end-to-end:

```bash
cd analysis/dbt-bq
uv run python sharia_banking_dw/scripts/run_sharia_dw.py
```

For Airflow:

```bash
cd infra/airflow
bash install.sh
bash start.sh
```
