# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
import argparse
import os
import re
from pathlib import Path


def natural_sort_key(filename):
    return [
        int(part) if part.isdigit() else part for part in re.split(r"(\d+)", filename)
    ]


def merge_txt_to_md(directory=".", output_file="merged_output.md"):
    dir_path = Path(directory)
    txt_files = [f for f in os.listdir(dir_path) if f.endswith(".txt")]
    txt_files.sort(key=natural_sort_key)

    out_path = Path(output_file)
    with open(out_path, "w", encoding="utf-8") as md_file:
        for txt_file in txt_files:
            file_path = dir_path / txt_file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
                md_file.write(f"# {txt_file}\n\n")
                md_file.write(content + "\n\n")

    print(f"Merged {len(txt_files)} files into {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple .txt files into a single Markdown (.md) file."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=".",
        help="Directory containing .txt files (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="merged_output.md",
        help="Output markdown file path (default: merged_output.md)",
    )
    args = parser.parse_args()
    merge_txt_to_md(args.directory, args.output)


if __name__ == "__main__":
    main()
