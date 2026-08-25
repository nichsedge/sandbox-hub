# 🤖 genai-demo

Small, self-contained demos of LLM frameworks and providers: OpenAI, Ollama, Gemini (via LangChain and LlamaIndex), OpenRouter, and LangSmith tracing.

## 📁 Contents

| Script | What it shows |
|---|---|
| [`openai_demo.py`](./openai_demo.py) | OpenAI **Responses API** (`gpt-4.1-nano`) — single prompt → text |
| [`ollama_demo.py`](./ollama_demo.py) | Local models via the `ollama` Python client (`gemma3:1b`, `moondream`) — streaming and one-shot chat |
| [`langchain/gemini_demo.py`](./langchain/gemini_demo.py) | `ChatGoogleGenerativeAI` (`gemini-2.0-flash`) with system + human messages |
| [`langchain/openrouter_demo.py`](./langchain/openrouter_demo.py) | LangChain `ChatOpenAI` pointed at the **OpenRouter** base URL + a minimal **LangGraph** `StateGraph` |
| [`langchain/langsmith_demo.py`](./langchain/langsmith_demo.py) | **LangSmith** tracing (`@traceable`, `wrap_openai`) around an OpenRouter-backed client with a RAG-style retriever |
| [`llama_index/genai_gemini.py`](./llama_index/genai_gemini.py) | LlamaIndex `GoogleGenAI` LLM chat |
| [`llama_index/blog_explorer.py`](./llama_index/blog_explorer.py) | LlamaIndex RAG pipeline: `VectorStoreIndex` over local documents, pluggable embeddings/LLMs (OpenAI, HuggingFace, Gemini, Ollama) |

## ⚙️ Requirements

- Python ≥ 3.13
- [uv](https://github.com/astral-sh/uv)
- FFmpeg is not needed here.

## 🔑 Environment variables

| Variable | Used by |
|---|---|
| `OPENAI_API_KEY` | `openai_demo.py`, `llama_index/blog_explorer.py` (OpenAI backend) |
| `OPENROUTER_API_KEY` (+ optional `OPENROUTER_BASE_URL`) | `langchain/openrouter_demo.py`, `langchain/langsmith_demo.py` |
| `GOOGLE_API_KEY` | `langchain/gemini_demo.py`, `llama_index/genai_gemini.py`, `blog_explorer.py` (Gemini backend) |

Scripts prompt for missing keys where possible; prefer exporting them or using a `.env`.

## ⚡ Quick Start

Standalone scripts declare inline dependencies (PEP 723) — run directly:

```bash
uv run openai_demo.py
uv run ollama_demo.py
```

The `langchain/` and `llama_index/` scripts need shared deps from [`requirements.txt`](./requirements.txt):

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt python-dotenv langchain-openai langgraph langsmith
python langchain/openrouter_demo.py
python llama_index/blog_explorer.py
```
