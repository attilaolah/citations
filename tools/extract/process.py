"""Shared subprocess helpers for JSON-emitting extraction tools."""

import subprocess

from pydantic import BaseModel


class JsonToolError(RuntimeError):
    """Raised when a subprocess JSON tool fails or emits invalid JSON."""

    def __init__(self, *, context: str, detail: str) -> None:
        """Initialise the error with context and detailed failure reason."""
        message = f"{context}: {detail}"
        super().__init__(message)


def run_json_tool[T: BaseModel](*, argv: list[str], context: str, model: type[T]) -> T:
    """Run a subprocess and validate JSON output with a provided model.

    Returns:
        Parsed JSON payload validated by `model`.

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

    return model.model_validate_json(proc.stdout)
