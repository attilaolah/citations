"""Extract Latin/Hungarian name pairs from ENFO arthropod gallery pages via XPath."""

import argparse
import json
import re
from pathlib import Path

from lxml import html

ANCHOR_XPATH = "//a[@hreflang='hu' and starts-with(@href, '/node/')]"
PAIR_RE = re.compile(r"^(?P<hungarian>.+?)\s*\((?P<latin>[^()]+)\)\s*$")
LATIN_RE = re.compile(r"[A-Z][a-z-]+(?: [a-z][a-z-]+){0,3}")


def _extract_pairs(content: bytes) -> dict[str, set[str]]:
    document = html.fromstring(content)
    mapping: dict[str, set[str]] = {}

    for anchor in document.xpath(ANCHOR_XPATH):
        text = " ".join(anchor.text_content().split())
        match = PAIR_RE.fullmatch(text)
        if match is None:
            continue

        hungarian = match.group("hungarian").strip()
        latin = " ".join(match.group("latin").split())
        if not hungarian:
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
