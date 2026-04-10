"""Conservative post-processing for Docling-generated Markdown."""

import re
from enum import Enum

from tools.settings import IOSettings


class _Re(Enum):
    image_placeholder = re.compile(r"\s*<!--\s*image\s*-->\s*")
    heading = re.compile(r"^\s*#{1,6}\s")
    heading_leading_middot = re.compile(r"^(\s*#{1,6}\s*)·\s*(\S.*)$")
    leading_middot = re.compile(r"^(\s*)·\s*(\S.*)$")
    double_dash_bullet = re.compile(r"^(\s*)-\s*-\s*(\S.*)$")
    empty_bullet = re.compile(r"^\s*-\s*$")
    list_line = re.compile(r"^(\s*)-\s*(.*)$")
    list_text_leading_middot = re.compile(r"^·\s*(.*)$")
    spaced_colon = re.compile(r"\s+:")
    single_non_ascii = re.compile(r"^\s*([^\x00-\x7F])\s*$")
    leading_ws = re.compile(r"^(\s*)(.*)$")
    multi_space = re.compile(r" {2,}")
    three_plus_newlines = re.compile(r"\n{3,}")


def main() -> int:
    """Run the Markdown cleanup CLI.

    Returns:
        Process exit code.
    """
    settings = IOSettings()  # pyright: ignore[reportCallIssue]
    settings.output.write_text(
        _clean_markdown(settings.input.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return 0


def _clean_line(line: str) -> str | None:
    """Normalize one line of extracted Markdown, or drop it.

    Returns:
        The cleaned line, or `None` if the line should be removed.
    """
    line = _Re.image_placeholder.value.sub("", line)

    if _Re.empty_bullet.value.match(line) or _Re.single_non_ascii.value.match(line):
        return None

    heading_middot_match = _Re.heading_leading_middot.value.match(line)
    if heading_middot_match:
        heading_prefix, text = heading_middot_match.groups()
        line = f"{heading_prefix}{text}"

    if not _Re.heading.value.match(line):
        middot_match = _Re.leading_middot.value.match(line)
        if middot_match:
            indent, text = middot_match.groups()
            line = f"{indent}- {text}"

    double_dash_match = _Re.double_dash_bullet.value.match(line)
    if double_dash_match:
        indent, text = double_dash_match.groups()
        line = f"{indent}  - {text}"

    normalized_line = _normalize_non_table_line(line)
    if normalized_line is None:
        return None
    line = normalized_line

    line = _Re.spaced_colon.value.sub(":", line)
    return line.rstrip()


def _normalize_non_table_line(line: str) -> str | None:
    """Normalize spacing for non-table lines and list markers.

    Returns:
        The normalized line, or `None` if the line should be dropped.
    """
    if "|" in line:
        return line

    list_match = _Re.list_line.value.match(line)
    if list_match:
        indent, text = list_match.groups()
        text = _collapse_spaces(text)
        list_text_middot_match = _Re.list_text_leading_middot.value.match(text)
        if list_text_middot_match:
            text = list_text_middot_match.group(1)
        if not text:
            return None
        return f"{indent}- {text}"

    leading_ws_match = _Re.leading_ws.value.match(line)
    if leading_ws_match is None:
        return line.rstrip()
    indent, text = leading_ws_match.groups()
    return f"{indent}{_collapse_spaces(text)}"


def _collapse_spaces(text: str) -> str:
    """Collapse tabs and repeated spaces to single spaces in a text fragment.

    Returns:
        The space-normalized text.
    """
    text = text.replace("\t", " ")
    return _Re.multi_space.value.sub(" ", text).strip()


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


if __name__ == "__main__":
    raise SystemExit(main())
