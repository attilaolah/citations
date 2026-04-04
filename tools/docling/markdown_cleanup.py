"""Conservative post-processing for Docling-generated Markdown."""

import argparse
import re
from enum import Enum
from pathlib import Path


class _Re(Enum):
    image_placeholder = re.compile(r"\s*<!--\s*image\s*-->\s*")
    heading = re.compile(r"^\s*#{1,6}\s")
    leading_middot = re.compile(r"^(\s*)·\s*(\S.*)$")
    double_dash_bullet = re.compile(r"^(\s*)-\s*-\s*(\S.*)$")
    empty_bullet = re.compile(r"^\s*-\s*$")
    single_non_ascii = re.compile(r"^\s*([^\x00-\x7F])\s*$")
    three_plus_newlines = re.compile(r"\n{3,}")


def main() -> int:
    """Run the Markdown cleanup CLI.

    Returns:
        Process exit code.
    """
    args = _parse_args()
    src = Path(args.input)
    dst = Path(args.output)
    dst.write_text(_clean_markdown(src.read_text(encoding="utf-8")), encoding="utf-8")
    return 0


def _clean_line(line: str) -> str | None:
    """Normalize one line of extracted Markdown, or drop it.

    Returns:
        The cleaned line, or `None` if the line should be removed.
    """
    line = _Re.image_placeholder.value.sub("", line)

    if _Re.empty_bullet.value.match(line) or _Re.single_non_ascii.value.match(line):
        return None

    if not _Re.heading.value.match(line):
        middot_match = _Re.leading_middot.value.match(line)
        if middot_match:
            indent, text = middot_match.groups()
            line = f"{indent}- {text}"

    double_dash_match = _Re.double_dash_bullet.value.match(line)
    if double_dash_match:
        indent, text = double_dash_match.groups()
        line = f"{indent}  - {text}"

    return line.rstrip()


def _clean_markdown(text: str) -> str:
    """Apply conservative Markdown cleanup transforms to a whole document.

    Returns:
        The cleaned Markdown document.
    """
    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        cleaned_line = _clean_line(raw_line)
        if cleaned_line is not None:
            cleaned_lines.append(cleaned_line)

    out = "\n".join(cleaned_lines)
    out = _Re.three_plus_newlines.value.sub("\n\n", out)
    return out.strip() + "\n"


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
