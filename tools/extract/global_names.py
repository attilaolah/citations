"""Extract global names from source documents using gnfinder."""

import json
import re
import tempfile
import unicodedata
from os import EX_OK
from pathlib import Path

from pydantic import BaseModel, FilePath, TypeAdapter

from tools.extract.process import run_json_tool
from tools.settings import IOSettings


class GNFinderCompactResult(BaseModel):
    """Subset of compact gnfinder output needed by the repository."""

    names: list[dict[str, object]]


class _Settings(IOSettings):
    gnfinder: FilePath


GLOBAL_NAMES_ADAPTER = TypeAdapter(list[dict[str, object]])
GNPFINDER_COMPACT_ADAPTER = TypeAdapter(GNFinderCompactResult)
GNFINDER_BOUNDARY_PUNCTUATION = str.maketrans(
    {
        "{": " ",
        "}": " ",
        "[": " ",
        "]": " ",
        "(": " ",
        ")": " ",
        "/": " ",
        ",": " ",
    },
)
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", flags=re.IGNORECASE | re.DOTALL)
ASCII_UPPER_WORD_RE = re.compile(r"[A-Z][A-Za-z-]+")
ASCII_LOWER_WORD_RE = re.compile(r"[a-z][a-z-]*")
LATIN_RANK_MARKERS = {"subsp", "subsp.", "ssp", "ssp.", "var", "var.", "f", "f.", "cf", "cf."}
NON_ORGANISM_SUFFIXES = {"anthodium", "flos", "fructus", "herba", "radix", "semen", "semina"}
NON_LATIN_EPITHET_TOKENS = {"kinai", "mezei"}
MIN_LATIN_PARTS = 2


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _is_scientific_name(value: str) -> bool:
    candidate = " ".join(value.split())
    if not candidate:
        return False

    parts = candidate.split()
    if len(parts) < MIN_LATIN_PARTS:
        return False
    if ASCII_UPPER_WORD_RE.fullmatch(parts[0]) is None:
        return False

    valid = True
    for part in parts[1:]:
        part_folded = part.casefold()
        if part_folded in NON_ORGANISM_SUFFIXES or part_folded in NON_LATIN_EPITHET_TOKENS:
            valid = False
            break
        if part_folded in LATIN_RANK_MARKERS:
            continue
        part_ascii = _strip_diacritics(part_folded)
        if ASCII_LOWER_WORD_RE.fullmatch(part_ascii) is None:
            valid = False
            break
    return valid


def _main() -> int:
    settings = _Settings.from_args()
    src_text = settings.input.read_text(encoding="utf-8", errors="replace")
    src_text = REF_RE.sub(" ", src_text)
    normalized_text = src_text.translate(GNFINDER_BOUNDARY_PUNCTUATION)

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
            adapter=GNPFINDER_COMPACT_ADAPTER,
        )
    finally:
        Path(normalized_input_path).unlink(missing_ok=True)

    filtered_names = [entry for entry in parsed.names if _is_scientific_name(str(entry.get("name", "")))]
    names = GLOBAL_NAMES_ADAPTER.validate_python(filtered_names)
    settings.output.write_text(
        json.dumps(names, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(_main())
