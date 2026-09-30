# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Convert Jupyter Notebooks (.ipynb) to clean, plain Python (.py) scripts.
Strips markdown cells and cell delimiters, comments out IPython magics / shell commands,
validates syntax via ast.parse, and removes the original .ipynb file upon successful conversion.
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path


def convert_notebook_to_plain_py(nb_path: Path) -> str:
    """Read a notebook and extract code cells as plain Python code."""
    with open(nb_path, "r", encoding="utf-8", errors="ignore") as f:
        nb_data = json.load(f)

    code_blocks = []
    for cell in nb_data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue

        source = cell.get("source", [])
        if isinstance(source, str):
            source_lines = source.splitlines(keepends=True)
        else:
            source_lines = source

        cleaned_lines = []
        for line in source_lines:
            stripped = line.strip()
            # Comment out ipython magics, shell escapes, or bare shell commands in notebooks
            if stripped.startswith(("%", "!", "?", "pip ", "conda ", "python -m ")):
                indent = line[: len(line) - len(line.lstrip())]
                rest = line.lstrip()
                cleaned_lines.append(f"{indent}# {rest}")
            else:
                cleaned_lines.append(line)

        block = "".join(cleaned_lines).rstrip()
        if block.strip():
            code_blocks.append(block)

    if not code_blocks:
        return ""

    return "\n\n".join(code_blocks) + "\n"


def process_notebook(nb_path: Path, keep_original: bool = False) -> bool:
    """Converts a single notebook to .py and optionally deletes the notebook."""
    py_path = nb_path.with_suffix(".py")

    # If the target .py file already exists (e.g. tools/social/reddit.py alongside reddit.ipynb)
    if py_path.exists() and py_path.resolve() != nb_path.resolve():
        print(f"Target already exists: {py_path}. Removing original notebook: {nb_path}")
        if not keep_original:
            nb_path.unlink()
        return True

    py_content = convert_notebook_to_plain_py(nb_path)

    # Validate syntax if there is code
    if py_content:
        try:
            ast.parse(py_content, filename=str(py_path))
        except SyntaxError as e:
            print(f"SyntaxError converting {nb_path}: {e}", file=sys.stderr)
            return False

    with open(py_path, "w", encoding="utf-8") as f:
        f.write(py_content)

    print(f"Converted: {nb_path} -> {py_path}")
    if not keep_original:
        nb_path.unlink()
        print(f"Deleted: {nb_path}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Convert .ipynb files to plain .py and remove .ipynb."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["analysis", "study", "tools"],
        help="Directories or files to process (default: analysis study tools)",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        help="Keep the original .ipynb files instead of deleting them.",
    )
    args = parser.parse_args()

    root_dir = Path.cwd()
    success = True

    for p in args.paths:
        target = Path(p)
        if not target.is_absolute():
            target = root_dir / target

        if not target.exists():
            print(f"Path not found: {target}", file=sys.stderr)
            continue

        if target.is_file() and target.suffix == ".ipynb":
            if not process_notebook(target, keep_original=args.keep_original):
                success = False
        elif target.is_dir():
            for root, _, files in os.walk(target):
                for file in files:
                    if file.endswith(".ipynb"):
                        nb_file = Path(root) / file
                        if not process_notebook(nb_file, keep_original=args.keep_original):
                            success = False

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
