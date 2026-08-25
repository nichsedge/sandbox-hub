# 🎙️ video2text

Transcribe `.mkv` video files to text using **OpenAI Whisper** (local inference).

## How it works

1. **Extract audio** from the `.mkv` with FFmpeg → 16 kHz mono WAV (`pcm_s16le`)
2. **Transcribe** the WAV with Whisper ([`openai-whisper`](https://github.com/openai/whisper), runs on GPU via PyTorch when available)

## ⚙️ Requirements

- Python ≥ 3.11, [uv](https://github.com/astral-sh/uv)
- `ffmpeg` on PATH
- Whisper model weights are downloaded automatically on first run

## ⚡ Usage

```bash
cd ai/video2text
uv sync
```

Point [`main.py`](./main.py) at your file and run:

```bash
uv run main.py
```

Output: extracted `.wav` next to the input plus the transcription printed to stdout.
