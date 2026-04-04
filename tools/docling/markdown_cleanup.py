"""Conservative post-processing for Docling-generated Markdown."""

import argparse
import re
from pathlib import Path

IMAGE_PLACEHOLDER_RE = re.compile(r"\s*<!--\s*image\s*-->\s*")
HEADING_RE = re.compile(r"^\s*#{1,6}\s")
LEADING_MIDDOT_RE = re.compile(r"^(\s*)·\s*(\S.*)$")
DOUBLE_DASH_BULLET_RE = re.compile(r"^(\s*)-\s*-\s*(\S.*)$")
EMPTY_BULLET_RE = re.compile(r"^\s*-\s*$")
SINGLE_NON_ASCII_RE = re.compile(r"^\s*([^\x00-\x7F])\s*$")
THREE_PLUS_NEWLINES_RE = re.compile(r"\n{3,}")


def clean_line(line: str) -> str | None:
    """Normalize one line of extracted Markdown, or drop it.

    Returns:
        The cleaned line, or `None` if the line should be removed.
    """
    line = IMAGE_PLACEHOLDER_RE.sub("", line)

    if EMPTY_BULLET_RE.match(line):
        return None

    if SINGLE_NON_ASCII_RE.match(line):
        return None

    if not HEADING_RE.match(line):
        middot_match = LEADING_MIDDOT_RE.match(line)
        if middot_match:
            indent, text = middot_match.groups()
            line = f"{indent}- {text}"

    double_dash_match = DOUBLE_DASH_BULLET_RE.match(line)
    if double_dash_match:
        indent, text = double_dash_match.groups()
        line = f"{indent}  - {text}"

    return line.rstrip()


def clean_markdown(text: str) -> str:
    """Apply conservative Markdown cleanup transforms to a whole document.

    Returns:
        The cleaned Markdown document.
    """
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        cleaned_line = clean_line(raw_line)
        if cleaned_line is not None:
            cleaned_lines.append(cleaned_line)

    out = "\n".join(cleaned_lines)
    out = THREE_PLUS_NEWLINES_RE.sub("\n\n", out)
    return out.strip() + "\n"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    """Run the Markdown cleanup CLI.

    Returns:
        Process exit code.
    """
    args = parse_args()
    src = Path(args.input)
    dst = Path(args.output)
    dst.write_text(clean_markdown(src.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
