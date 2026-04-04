# Agent Rules

## Formatting

- Format all Nix files with `alejandra`.
- Check all Bazel files with `buildifier --warnings=all`, then fix issues with `buildifier --warnings=all --lint=fix`.
- Format Markdown files with `prettier`.

## Bazel

- Prefer native Starlark rules over `genrule`.
- Keep publication-specific targets in `//publications`.
- Keep Bazel tooling in `//tools` and Nix tooling in `//nix`.
