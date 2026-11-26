# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pypdf>=6.9.2",
#     "python-dotenv>=1.2.2",
# ]
# ///
"""
Remove password protection from PDF files (single file, multiple files, or directory).

Usage:
  # Unlock all PDFs in a folder (saves as <filename>-unlocked.pdf in that folder)
  uv run tools/automation/rm_pw_pdf.py tools/automation/ -p secret

  # Unlock multiple files or folders
  uv run tools/automation/rm_pw_pdf.py file1.pdf file2.pdf -p secret

  # Unlock a single file
  uv run tools/automation/rm_pw_pdf.py file.pdf -p secret

  # Using environment variables / .env
  INPUT_PDF_PATH="tools/automation/" PASSWORD="secret" uv run tools/automation/rm_pw_pdf.py
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PasswordType, PdfReader, PdfWriter


def unlock_pdf(input_path: Path, output_path: Path, password: str | None) -> None:
    reader = PdfReader(str(input_path))
    was_encrypted = reader.is_encrypted

    if was_encrypted:
        if not password:
            raise ValueError(
                f"'{input_path.name}' is password-protected, but no password was provided."
            )
        result = reader.decrypt(password)
        if result == PasswordType.NOT_DECRYPTED:
            raise ValueError(f"Failed to decrypt '{input_path.name}': Incorrect password.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    if was_encrypted:
        print(f"Unlocked: {input_path} -> {output_path}")
    else:
        print(f"Copied (unencrypted): {input_path} -> {output_path}")


def collect_pdf_files(paths: list[Path], recursive: bool = False) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Input path does not exist: {path}")

        if path.is_file():
            if path.suffix.lower() == ".pdf":
                resolved = path.resolve()
                if resolved not in seen:
                    collected.append(path)
                    seen.add(resolved)
        elif path.is_dir():
            pattern = "**/*.pdf" if recursive else "*.pdf"
            for pdf_file in sorted(path.glob(pattern, case_sensitive=False)):
                # Skip already unlocked files when scanning directory
                if pdf_file.stem.endswith("-unlocked"):
                    continue
                resolved = pdf_file.resolve()
                if resolved not in seen:
                    collected.append(pdf_file)
                    seen.add(resolved)

    return collected


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Remove password protection from PDF files (single file, list of files, or directory)."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="Input PDF file(s) or folder(s). If omitted, falls back to INPUT_PDF_PATH env var.",
    )
    parser.add_argument(
        "-p",
        "--password",
        type=str,
        default=None,
        help="Password to decrypt PDFs (defaults to PASSWORD env var if omitted).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Custom output file or directory (only valid for single file or directory target).",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search directories recursively for PDF files.",
    )

    args = parser.parse_args()

    input_paths = args.inputs
    if not input_paths:
        env_input = os.getenv("INPUT_PDF_PATH")
        if env_input:
            input_paths = [Path(env_input)]
        else:
            parser.error("No input specified. Provide file/directory arguments or set INPUT_PDF_PATH.")

    password = args.password or os.getenv("PASSWORD")

    output_override = args.output
    if output_override is None:
        env_output = os.getenv("OUTPUT_PDF_PATH")
        if env_output:
            output_override = Path(env_output)

    pdf_files = collect_pdf_files(input_paths, recursive=args.recursive)
    if not pdf_files:
        print("No PDF files found to process.")
        return

    if (
        len(pdf_files) > 1
        and output_override
        and not output_override.is_dir()
        and output_override.suffix.lower() == ".pdf"
    ):
        raise ValueError(
            "Cannot specify a single PDF output file when processing multiple input files."
        )

    print(f"Found {len(pdf_files)} PDF file(s) to process.")

    for pdf_file in pdf_files:
        if output_override:
            if output_override.is_dir() or not output_override.suffix:
                dest = output_override / f"{pdf_file.stem}-unlocked.pdf"
            else:
                dest = output_override
        else:
            dest = pdf_file.parent / f"{pdf_file.stem}-unlocked.pdf"

        unlock_pdf(pdf_file, dest, password)

    print("All done.")


if __name__ == "__main__":
    main()
