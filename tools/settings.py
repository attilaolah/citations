"""Shared CLI settings models for tools."""

from pathlib import Path  # NOQA: TC003

from pydantic import FilePath  # NOQA: TC002
from pydantic_settings import BaseSettings, SettingsConfigDict


class IOSettings(BaseSettings):
    """Base CLI settings with standard input/output flags."""

    input: FilePath
    output: Path

    model_config = SettingsConfigDict(cli_parse_args=True)
