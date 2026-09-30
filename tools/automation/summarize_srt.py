# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ollama>=0.4.0",
#     "srt>=3.5.3",
# ]
# ///
import argparse
import datetime
import sys
import ollama
import srt


def load_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        subtitles = list(srt.parse(f.read()))
    return subtitles


def split_subtitles(subtitles, interval_minutes=15):
    parts = []
    current_part = []
    if not subtitles:
        return []

    start_time = subtitles[0].start
    end_time = start_time + datetime.timedelta(minutes=interval_minutes)

    for sub in subtitles:
        if sub.start >= end_time:
            parts.append(current_part)
            current_part = []
            start_time = sub.start
            end_time = start_time + datetime.timedelta(minutes=interval_minutes)
        current_part.append(sub)

    if current_part:
        parts.append(current_part)

    return parts


def summarize_with_ollama(content, model="llama3.2:1b"):
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"Summarize the following text:\n\n{content}",
            },
        ],
    )
    return response["message"]["content"].strip()


def summarize_parts(parts, model="llama3.2:1b"):
    summaries = []
    for i, part in enumerate(parts):
        part_text = " ".join(sub.content for sub in part)
        print(f"Summarizing part {i + 1} ({len(part_text)} chars)...")
        summary = summarize_with_ollama(part_text, model=model)
        summaries.append((i + 1, summary))
    return summaries


def main():
    parser = argparse.ArgumentParser(
        description="Chunk and summarize SRT subtitle files using local Ollama models."
    )
    parser.add_argument("srt_file", help="Path to SRT subtitle file.")
    parser.add_argument(
        "-m",
        "--model",
        default="llama3.2:1b",
        help="Ollama model name (default: llama3.2:1b)",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=15,
        help="Chunk interval in minutes (default: 15)",
    )
    args = parser.parse_args()

    subtitles = load_srt(args.srt_file)
    parts = split_subtitles(subtitles, interval_minutes=args.interval)
    summaries = summarize_parts(parts, model=args.model)

    print("\n=== Summaries ===")
    for idx, summary in summaries:
        print(f"\n--- Part {idx} ---\n{summary}\n")


if __name__ == "__main__":
    main()
