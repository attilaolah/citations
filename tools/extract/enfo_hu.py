"""Extract Latin/Hungarian name pairs from ENFO arthropod gallery pages via XPath."""

import argparse
import json
import re
from pathlib import Path

from lxml import html

ANCHOR_XPATH = "//a[@hreflang='hu' and starts-with(@href, '/node/')]"
PAIR_RE = re.compile(r"^(?P<hungarian>.+?)\s*\((?P<latin>.+)\)\s*$")
LATIN_RE = re.compile(r"(?P<latin>[A-Z][a-z-]+(?: [a-z][a-z-]+){1,3})")
PARENS_RE = re.compile(r"\([^)]*\)")


def _extract_latin_name(raw_latin: str) -> str | None:
    normalized = " ".join(raw_latin.split())
    without_parenthetical = " ".join(PARENS_RE.sub(" ", normalized).split())
    match = LATIN_RE.search(without_parenthetical)
    if match is None:
        return None
    return match.group("latin")


def _extract_pairs(content: bytes) -> dict[str, set[str]]:
    document = html.fromstring(content)
    mapping: dict[str, set[str]] = {}

    for anchor in document.xpath(ANCHOR_XPATH):
        text = " ".join(anchor.text_content().split())
        match = PAIR_RE.fullmatch(text)
        if match is None:
            continue

        hungarian = match.group("hungarian").strip()
        latin = _extract_latin_name(match.group("latin"))
        if not hungarian:
            continue
        if latin is None:
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
