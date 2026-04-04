# Agent Rules

## Formatting

- Format all Nix files with `alejandra`.
- Check all Bazel files with `buildifier --warnings=all`, then fix issues with `buildifier --warnings=all --lint=fix`.
- Format Markdown files with `prettier`.
- Format Python files with `black` (not `ruff format`).

## Bazel

- Prefer native Starlark rules over `genrule`.
- Keep publication-specific targets in `//publications`.
- Keep Bazel tooling in `//tools` and Nix tooling in `//nix`.

## Python

- Use Python `3.15`.
- Lint with `ruff check --target-version py315`; apply `--fix --unsafe-fixes` when needed.
- Run `pyright` on changed Python code.
- Run `pyupgrade` to adopt the newest syntax it supports.
