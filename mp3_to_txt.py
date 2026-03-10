# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "openai>=2.26.0",
#     "pyaudio>=0.2.14",
#     "pydub>=0.25.1",
# ]
# ///
from openai import OpenAI
from pydub import AudioSegment
from pathlib import Path
import math

client = OpenAI()  # uses OPENAI_API_KEY

audio_path = Path("2026-03-03 17-01-25.mp3")
audio = AudioSegment.from_file(audio_path)

# Split into 10-minute chunks (adjust if needed)
chunk_ms = 10 * 60 * 1000
num_chunks = math.ceil(len(audio) / chunk_ms)

# Fixed indentation for directory naming
parts_dir = audio_path.with_suffix("").with_name(audio_path.stem + "_parts")
parts_dir.mkdir(exist_ok=True)

transcript_text = []

for i in range(num_chunks):
    start = i * chunk_ms
    end = min((i + 1) * chunk_ms, len(audio))
    chunk = audio[start:end]
    
    chunk_path = parts_dir / f"part_{i+1:03d}.mp3"
    # Fixed indentation for the export parameters
    chunk.export(chunk_path, format="mp3", bitrate="64k") 

    with open(chunk_path, "rb") as f:
        t = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe", # Note: 'whisper-1' is the standard model name
            file=f,
        )
    transcript_text.append(t.text)

full_text = "\n\n".join(transcript_text)

output_txt_path = audio_path.with_suffix(".txt")
with open(output_txt_path, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"Transcript successfully saved to {output_txt_path}")
