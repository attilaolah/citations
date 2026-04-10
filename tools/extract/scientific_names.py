"""Extract scientific names from source documents via gnfinder verification."""

import re
import tempfile
from os import EX_OK
from pathlib import Path
from typing import cast

from pydantic import BaseModel, FilePath

from tools.extract.json_io import write_json_file
from tools.extract.process import run_json_tool
from tools.settings import IOSettings

_GNFINDER_PIPE_BOUNDARY_RE = re.compile(r"\|+")
_GNFINDER_OTHER_BOUNDARY_PUNCTUATION = str.maketrans(dict.fromkeys("{}[]()/,", " "))
_REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", flags=re.IGNORECASE | re.DOTALL)
_DOUBLE_SINGLE_QUOTES_RE = re.compile(r"''")
_MULTISPACE_RE = re.compile(r"\s+")
_GNFINDER_SOURCES = ",".join(map(str, (1, 3, 4, 9, 11, 12, 167, 170, 172, 181)))
_GNFINDER_NO_MATCH = "NoMatch"


class _Settings(IOSettings):
    gnfinder: FilePath


class _GNFinderCompactResult(BaseModel):
    """Subset of compact gnfinder output needed by this extractor."""

    names: list[dict[str, object]]


def _main() -> int:
    settings = _Settings.from_args()
    write_json_file(settings.output, _source_names(settings))
    return EX_OK


def _source_names(settings: _Settings) -> list[dict[str, object]]:
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
        gnfinder_result = run_json_tool(
            argv=[
                str(settings.gnfinder),
                f"--sources={_GNFINDER_SOURCES}",
                "--format=compact",
                "--utf8-input",
                normalized_input_path,
            ],
            context=f"gnfinder failed for input {settings.input}",
            model=_GNFinderCompactResult,
        )
    finally:
        Path(normalized_input_path).unlink(missing_ok=True)
    return [entry for entry in gnfinder_result.names if _is_verified_match(entry)]


def _normalize_gnfinder_input(text: str) -> str:
    text = _REF_RE.sub(" ", text)
    text = _DOUBLE_SINGLE_QUOTES_RE.sub(" ", text)
    text = _GNFINDER_PIPE_BOUNDARY_RE.sub(" || ", text)
    text = text.translate(_GNFINDER_OTHER_BOUNDARY_PUNCTUATION)
    return _MULTISPACE_RE.sub(" ", text).strip()


def _is_verified_match(entry: dict[str, object]) -> bool:
    verification_raw = entry.get("verification")
    if not isinstance(verification_raw, dict):
        return False
    verification = cast("dict[str, object]", verification_raw)
    match_type = verification.get("matchType")
    return isinstance(match_type, str) and match_type != _GNFINDER_NO_MATCH


if __name__ == "__main__":
    raise SystemExit(_main())
