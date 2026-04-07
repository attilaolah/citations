"""Extract global names from source documents using gnfinder."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, TypeAdapter


class GNFinderCompactResult(BaseModel):
    """Subset of compact gnfinder output needed by the repository."""

    names: list[dict[str, object]]


GLOBAL_NAMES_ADAPTER = TypeAdapter(list[dict[str, object]])
GNPFINDER_COMPACT_ADAPTER = TypeAdapter(GNFinderCompactResult)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gnfinder", required=True)
    return parser.parse_args(argv)


def _main(argv: list[str]) -> int:
    args = _parse_args(argv)

    proc = subprocess.run(
        [args.gnfinder, "--format", "compact", args.input],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = f"gnfinder failed for input {args.input}: {proc.stderr.strip()}"
        raise RuntimeError(msg)

    parsed = GNPFINDER_COMPACT_ADAPTER.validate_json(proc.stdout)
    names = GLOBAL_NAMES_ADAPTER.validate_python(parsed.names)
    Path(args.output).write_text(
        json.dumps(names, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
