"""Shared subprocess helpers for JSON-emitting extraction tools."""

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import TypeAdapter


class JsonToolError(RuntimeError):
    """Raised when a subprocess JSON tool fails or emits invalid JSON."""

    def __init__(self, *, context: str, detail: str) -> None:
        """Initialise the error with context and detailed failure reason."""
        message = f"{context}: {detail}"
        super().__init__(message)


def run_json_tool[T](*, argv: list[str], context: str, adapter: TypeAdapter[T]) -> T:
    """Run a subprocess and validate JSON output with a provided adapter.

    Returns:
        Parsed JSON payload validated by `adapter`.

    Raises:
        JsonToolError: The subprocess exits non-zero.
    """
    proc = subprocess.run(
        argv,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"exit code {proc.returncode}"
        raise JsonToolError(context=context, detail=detail)

    return adapter.validate_json(proc.stdout)
