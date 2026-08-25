# 🔊 text2audio

Convert Markdown text to speech (MP3) using **gTTS** — tuned for Indonesian (`lang="id"`).

Currently reads [`almatsurat.md`](./almatsurat.md) and writes `output.mp3`.

## ⚙️ Requirements

- Python ≥ 3.13, [uv](https://github.com/astral-sh/uv)

## ⚡ Usage

```bash
cd ai/text2audio
uv sync
uv run main.py
```

To narrate a different text, edit the input path in [`main.py`](./main.py) (or swap the file) — language code `id` can be changed for other gTTS-supported languages.
