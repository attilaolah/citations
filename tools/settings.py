"""Shared CLI settings models for tools."""

from pathlib import Path  # NOQA: TC003
from typing import Self

from pydantic import FilePath  # NOQA: TC002
from pydantic_settings import BaseSettings, SettingsConfigDict


class IOSettings(BaseSettings):
    """Base CLI settings with standard input/output flags."""

    input: FilePath
    output: Path

    model_config = SettingsConfigDict(cli_parse_args=True)

    @classmethod
    def from_args(cls) -> Self:
        """Provide an alternate constructor to make type checkers happy.

        This is the same as using the constructor, but does not require call sites to silency the PyRight finding.

        Returns:
            A newly constructed settings object.
        """
        return cls()  # pyright: ignore[reportCallIssue]
