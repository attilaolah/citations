"""Extract Latin/Hungarian name pairs from plant_names_in_hungarian HTML tables."""

import argparse
import json
import re
from pathlib import Path

from lxml import html

LATIN_RE = re.compile(r"[A-Z][a-z-]+(?: [a-z][a-z-]+){1,3}")
MIN_COLUMN_COUNT = 3


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _extract_pairs(content: bytes) -> dict[str, set[str]]:
    if not content.strip():
        return {}

    document = html.fromstring(content)
    mapping: dict[str, set[str]] = {}

    for row in document.xpath("//tr[td]"):
        columns = row.xpath("./td")
        if len(columns) < MIN_COLUMN_COUNT:
            continue

        hungarian = _normalized_text(columns[1].text_content())
        latin = _normalized_text(columns[2].text_content())
        if not hungarian or not latin:
            continue
        if LATIN_RE.fullmatch(latin) is None:
            continue

        mapping.setdefault(latin, set()).add(hungarian)

    return mapping


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    mapping = _extract_pairs(args.input.read_bytes())
    sorted_mapping = {
        latin: sorted(values, key=lambda value: value.casefold())
        for latin, values in sorted(mapping.items(), key=lambda item: item[0].casefold())
    }

    args.output.write_text(
        json.dumps(sorted_mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
