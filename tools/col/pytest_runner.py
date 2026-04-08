"""Run pytest with forwarded arguments."""

import sys

import pytest


def _main(argv: list[str]) -> int:
    return pytest.main(argv)


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
