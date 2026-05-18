# 🧪 sandbox-hub

A personal sandbox of Python scripts and notebooks spanning **data engineering**, **AI/GenAI**, **speech processing**, **web scraping**, and **data analysis** — with an Indonesian context.

---

## 📁 Projects

### 🔄 Data Engineering

| Project | Description |
|---|---|
| [`airflow/`](./airflow) | Apache Airflow setup with DAGs for weekly pipelines: CSV → PostgreSQL → BigQuery (`movie_weekly`) and web scraping (`scrape_weekly`) |
| [`crypto-data/`](./crypto-data) | Fetch crypto data from Binance (CSV export parser) and CoinGecko API; query Solana token balances by wallet |
| [`docker-compose/`](./docker-compose) | Docker Compose configs for local infrastructure |

### 🤖 AI / GenAI

| Project | Description |
|---|---|
| [`genai-demo/`](./genai-demo) | LangChain and LlamaIndex experiments; OpenAI API demo; Ollama local LLM demo |
| [`pdf2text2/`](./pdf2text2) | Extract and structure text from Indonesian LHKPN (public official wealth statement) PDFs using AI |

### 🎙️ Speech & Media

| Project | Description |
|---|---|
| [`video2text/`](./video2text) | Transcribe `.mkv` video files to text using OpenAI Whisper (FFmpeg + GPU support) |
| [`text2audio/`](./text2audio) | Convert Markdown text to speech (MP3) using gTTS — supports Indonesian |
| [`mp3_to_txt.py`](./mp3_to_txt.py) | Transcribe MP3 audio to text via OpenAI's GPT-4o transcription API, chunked for long files |

### 🕷️ Web Scraping

| Project | Description |
|---|---|
| [`reddit.py`](./reddit.py) | Scrape Reddit posts and comments across mental health subreddits using PRAW + Pushshift API |
| [`gutenberg.py`](./gutenberg.py) | Download Honoré de Balzac books from Project Gutenberg and translate them to Indonesian |
| [`asdosan_scele.py`](./asdosan_scele.py) | Scrape course/assignment data from SCELE (University of Indonesia's LMS) |

### 📊 Data Analysis & Notebooks

| Notebook | Description |
|---|---|
| [`main.ipynb`](./main.ipynb) | General-purpose analysis notebook |
| [`indonesia-elections/`](./indonesia-elections) | Analysis of the 2024 Indonesian General Election |
| [`religious-diversity-analysis/`](./religious-diversity-analysis) | Analysis of religious diversity across Indonesian organizations |
| [`recession.ipynb`](./recession.ipynb) | Recession indicators and economic data analysis |
| [`forbes.ipynb`](./forbes.ipynb) | Analysis of Forbes wealth/billionaire data |
| [`taleb.ipynb`](./taleb.ipynb) | Explorations related to Nassim Taleb's ideas (fat tails, randomness) |
| [`reddit.ipynb`](./reddit.ipynb) | Exploratory analysis of scraped Reddit data |
| [`numerical method.ipynb`](./numerical%20method.ipynb) | Numerical methods implementations |
| [`travelling-salesman-problem.ipynb`](./travelling-salesman-problem.ipynb) | TSP solver experiments |
| [`siakng_transcript_to_obsidian.ipynb`](./siakng_transcript_to_obsidian.ipynb) | Convert SIAK-NG academic transcripts to Obsidian-compatible Markdown |

### 📚 Courses & Learning

| Project | Description |
|---|---|
| [`courses/rakamin-idx/`](./courses/rakamin-idx) | Rakamin × IDX Partners virtual internship |
| [`courses/rakamin-btps/`](./courses/rakamin-btps) | Rakamin × Bank BTPN Syariah virtual internship |
| [`courses/rakamin-muamalat/`](./courses/rakamin-muamalat) | Rakamin × Bank Muamalat virtual internship |
| [`courses/forage-JPMC_quantitative-research/`](./courses/forage-JPMC_quantitative-research) | JP Morgan Chase Quantitative Research job simulation (Forage) |

### 💼 Recruitment Challenges

| Project | Description |
|---|---|
| [`recruitment/`](./recruitment) | Coding tests and take-home assignments for DE/DS roles (Bitwyre, Cadit, LinkAja, MileApp, TEL) |

### 🛠️ Utilities

| Script | Description |
|---|---|
| [`computer-vision/compress_images_in_current_folder.py`](./computer-vision/compress_images_in_current_folder.py) | Batch compress all images in a directory |
| [`reset_ipynb.py`](./reset_ipynb.py) | Clear all outputs from Jupyter notebooks |
| [`rm_pw_pdf.py`](./rm_pw_pdf.py) | Remove password protection from PDF files |
| [`speedtest_connection.py`](./speedtest_connection.py) | Run an internet speed test from the CLI |
| [`tools/automation/fatsecret_barcode.py`](./tools/automation/fatsecret_barcode.py) | Fetch food nutrition details from FatSecret by barcode (supports local .env credentials) |

---

## 🛠️ Tech Stack

- **Languages**: Python, SQL
- **AI/ML**: OpenAI API, Whisper, LangChain, LlamaIndex, Ollama
- **Data Engineering**: Apache Airflow, PostgreSQL, Google BigQuery
- **Data Analysis**: Pandas, Jupyter Notebook
- **Speech**: gTTS, pydub, FFmpeg
- **Scraping**: PRAW, Pushshift, BeautifulSoup, Requests
- **Package Manager**: [uv](https://github.com/astral-sh/uv)

---

## ⚡ Quick Start

Most standalone scripts use [uv](https://github.com/astral-sh/uv) inline dependencies:

```bash
uv run mp3_to_txt.py
```

For sub-projects with a `pyproject.toml`:

```bash
cd <project-folder>
uv sync
uv run main.py
```

For Airflow:

```bash
cd airflow
bash install.sh
bash start.sh
```
