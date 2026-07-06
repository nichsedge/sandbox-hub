#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["deep-translator>=1.11.4"]
# ///
"""Translate an SRT subtitle file while preserving cue timing."""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from deep_translator import GoogleTranslator


TIMING_RE = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}")
MARKER_RE = re.compile(r"@@\s*SRT\s*(\d{6})\s*@@")


@dataclass
class Cue:
    number: str
    timing: str
    text: str


def read_text(path: Path, encoding: str) -> str:
    return path.read_text(encoding=encoding).replace("\r\n", "\n").replace("\r", "\n")


def parse_srt(content: str) -> list[Cue]:
    cues: list[Cue] = []
    for block in re.split(r"\n{2,}", content.strip()):
        lines = block.splitlines()
        if len(lines) < 2:
            continue

        if TIMING_RE.match(lines[0]):
            number = str(len(cues) + 1)
            timing = lines[0]
            text_lines = lines[1:]
        else:
            number = lines[0]
            timing = lines[1]
            text_lines = lines[2:]

        if not TIMING_RE.match(timing):
            raise ValueError(f"Could not parse timing line near cue {number!r}: {timing!r}")

        cues.append(Cue(number=number, timing=timing, text="\n".join(text_lines)))
    return cues


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cache_key(cue: Cue) -> str:
    return f"{cue.number}|{cue.timing}|{cue.text}"


def build_chunks(cues: list[Cue], max_chars: int) -> list[list[Cue]]:
    chunks: list[list[Cue]] = []
    current: list[Cue] = []
    current_size = 0

    for cue in cues:
        piece_size = len(cue.text) + 20
        if current and current_size + piece_size > max_chars:
            chunks.append(current)
            current = []
            current_size = 0
        current.append(cue)
        current_size += piece_size

    if current:
        chunks.append(current)
    return chunks


def split_translated_chunk(translated: str) -> dict[int, str]:
    matches = list(MARKER_RE.finditer(translated))
    result: dict[int, str] = {}
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(translated)
        result[int(match.group(1))] = translated[start:end].strip()
    return result


def translate_one(translator: GoogleTranslator, text: str, delay: float) -> str:
    if not text.strip():
        return text
    translated = translator.translate(text)
    if delay:
        time.sleep(delay)
    return translated


def translate_cues(
    cues: list[Cue],
    source: str,
    target: str,
    cache_path: Path,
    max_chars: int,
    delay: float,
) -> dict[str, str]:
    translator = GoogleTranslator(source=source, target=target)
    cache = load_cache(cache_path)
    missing = [cue for cue in cues if cue.text.strip() and cache_key(cue) not in cache]
    chunks = build_chunks(missing, max_chars)

    for chunk_index, chunk in enumerate(chunks, start=1):
        payload = "\n".join(f"@@SRT{int(cue.number):06d}@@\n{cue.text}" for cue in chunk)
        try:
            translated = translator.translate(payload)
            pieces = split_translated_chunk(translated)
            if len(pieces) != len(chunk):
                raise RuntimeError(
                    f"expected {len(chunk)} translated cues, got {len(pieces)} markers"
                )
            for cue in chunk:
                cache[cache_key(cue)] = pieces[int(cue.number)]
        except Exception as exc:
            print(f"Chunk {chunk_index}/{len(chunks)} failed ({exc}); retrying cue by cue.")
            for cue in chunk:
                cache[cache_key(cue)] = translate_one(translator, cue.text, delay)

        save_cache(cache_path, cache)
        print(f"Translated chunk {chunk_index}/{len(chunks)} ({len(cache)}/{len(missing)} cached)")
        if delay:
            time.sleep(delay)

    return cache


def write_srt(cues: list[Cue], translations: dict[str, str], output: Path) -> None:
    blocks: list[str] = []
    for cue in cues:
        text = translations.get(cache_key(cue), cue.text)
        blocks.append(f"{cue.number}\n{cue.timing}\n{text}".rstrip())
    output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--source", default="pt", help="Source language code, default: pt")
    parser.add_argument("--target", default="en", help="Target language code, default: en")
    parser.add_argument("--encoding", default="cp1252", help="Input encoding, default: cp1252")
    parser.add_argument("--cache", type=Path, help="Translation cache JSON path")
    parser.add_argument("--max-chars", type=int, default=4200)
    parser.add_argument("--delay", type=float, default=0.15)
    args = parser.parse_args()

    output = args.output or args.input.with_name(args.input.stem + ".english.srt")
    cache_path = args.cache or output.with_suffix(output.suffix + ".cache.json")

    cues = parse_srt(read_text(args.input, args.encoding))
    translations = translate_cues(
        cues=cues,
        source=args.source,
        target=args.target,
        cache_path=cache_path,
        max_chars=args.max_chars,
        delay=args.delay,
    )
    write_srt(cues, translations, output)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
