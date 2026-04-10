# Agent Rules

## Formatting

- Format all Nix files with `alejandra`.
- Check all `.bzl`/`.bazel` files with `buildifier --lint=warn --warnings=all`, then fix issues with `buildifier --warnings=all --lint=fix`.
- Format Markdown files with `prettier`.
- Format Python files with `black` (not `ruff format`).

## Bazel

- Prefer native Starlark rules over `genrule`.
- Prefer `build_file` over `build_file_content`.
- Prefer strict visibility over `//visibility:public`.
- Keep publication-specific targets in `//external_sources/publications`.
- Keep Bazel tooling in `//tools` and Nix tooling in `//nix`.

## Python

- Use Python `3.14`.
- **Do not add** `noqa` pragmas.
- Dynamic imports are not allowed.
- Lint with `ruff check --target-version py314`; apply `--fix --unsafe-fixes` when needed.
- Run `pyright` on changed Python code.
- Run `pyupgrade` to adopt the newest syntax it supports.
- Keep definition order as: public first, then private helpers; start with the main entry point (for example `main()`).

## Environment

- You might be running inside a `nix develop` shell, try using the tools directly.
- If that fails, e.g. if Python modules or other tools are not visible, wrap the command with `nix develop -c ...`.
