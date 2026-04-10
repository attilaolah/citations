"""Extract scientific names from source documents using gnfinder."""

import json
import re
import tempfile
import unicodedata
from os import EX_OK
from pathlib import Path

from pydantic import BaseModel, FilePath, TypeAdapter

from tools.extract.process import run_json_tool
from tools.settings import IOSettings

_SCIENTIFIC_NAMES_ADAPTER = TypeAdapter(list[dict[str, object]])
_GNFINDER_BOUNDARY_PUNCTUATION = str.maketrans(dict.fromkeys("{}[]()/,|", " "))
_REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", flags=re.IGNORECASE | re.DOTALL)
_DOUBLE_SINGLE_QUOTES_RE = re.compile(r"''")
_MULTISPACE_RE = re.compile(r"\s+")
_ASCII_UPPER_WORD_RE = re.compile(r"[A-Z][A-Za-z-]+")
_ASCII_LOWER_WORD_RE = re.compile(r"[a-z][a-z-]*")
_LATIN_RANK_MARKERS = {"subsp", "subsp.", "ssp", "ssp.", "var", "var.", "f", "f.", "cf", "cf."}
_NON_ORGANISM_SUFFIXES = {"anthodium", "flos", "fructus", "herba", "radix", "semen", "semina"}
_NON_LATIN_EPITHET_TOKENS = {"kinai", "mezei"}
_MIN_LATIN_PARTS = 2


def _main() -> int:
    settings = _Settings.from_args()
    src_text = settings.input.read_text(encoding="utf-8", errors="replace")
    normalized_text = _normalize_gnfinder_input(src_text)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="gnfinder_input_",
        suffix=".txt",
        delete=False,
    ) as temp_file:
        temp_file.write(normalized_text)
        normalized_input_path = temp_file.name

    try:
        parsed = run_json_tool(
            argv=[str(settings.gnfinder), "--format", "compact", "--utf8-input", normalized_input_path],
            context=f"gnfinder failed for input {settings.input}",
            adapter=TypeAdapter(_GNFinderCompactResult),
        )
    finally:
        Path(normalized_input_path).unlink(missing_ok=True)

    filtered_names = [entry for entry in parsed.names if _is_scientific_name(str(entry.get("name", "")))]
    names = _SCIENTIFIC_NAMES_ADAPTER.validate_python(filtered_names)
    settings.output.write_text(
        json.dumps(names, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return EX_OK


class _Settings(IOSettings):
    gnfinder: FilePath


class _GNFinderCompactResult(BaseModel):
    """Subset of compact gnfinder output needed by this extractor."""

    names: list[dict[str, object]]


def _normalize_gnfinder_input(text: str) -> str:
    text = _REF_RE.sub(" ", text)
    text = _DOUBLE_SINGLE_QUOTES_RE.sub(" ", text)
    text = text.translate(_GNFINDER_BOUNDARY_PUNCTUATION)
    return _MULTISPACE_RE.sub(" ", text).strip()


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _is_scientific_name(value: str) -> bool:
    candidate = " ".join(value.split())
    if not candidate:
        return False

    parts = candidate.split()
    if len(parts) < _MIN_LATIN_PARTS:
        return False
    if _ASCII_UPPER_WORD_RE.fullmatch(parts[0]) is None:
        return False

    valid = True
    for part in parts[1:]:
        part_folded = part.casefold()
        if part_folded in _NON_ORGANISM_SUFFIXES or part_folded in _NON_LATIN_EPITHET_TOKENS:
            valid = False
            break
        if part_folded in _LATIN_RANK_MARKERS:
            continue
        part_ascii = _strip_diacritics(part_folded)
        if _ASCII_LOWER_WORD_RE.fullmatch(part_ascii) is None:
            valid = False
            break
    return valid


if __name__ == "__main__":
    raise SystemExit(_main())
