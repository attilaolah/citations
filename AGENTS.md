# Agent Rules

## Formatting

- Format all Nix files with `alejandra`.
- Check all Bazel files with `buildifier --warnings=all`, then fix issues with `buildifier --warnings=all --lint=fix`.
- Format Markdown files with `prettier`.
- Format Python files with `black` (not `ruff format`).

## Bazel

- Prefer native Starlark rules over `genrule`.
- Prefer `build_file` over `build_file_content`.
- Keep publication-specific targets in `//external_sources/publications`.
- Keep Bazel tooling in `//tools` and Nix tooling in `//nix`.

## Python

- Use Python `3.14`.
- Dynamic imports are not allowed.
- Lint with `ruff check --target-version py314`; apply `--fix --unsafe-fixes` when needed.
- Run `pyright` on changed Python code.
- Run `pyupgrade` to adopt the newest syntax it supports.
- Do not add `noqa` pragmas.
