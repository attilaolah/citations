# Markdown Cleanup Tasks

## Goals

- Remove docling image placeholders like `<!-- image -->`.
- Normalize leading middot bullets (`·`) into Markdown list bullets, except when the line is a heading.
- Normalize malformed nested bullets like `- -Foo` to proper nested list bullets.
- Remove obvious OCR artifact lines that contain only a single non-ASCII character.
- Remove empty bullet lines.
- Limit consecutive blank lines to at most two.
- Improve Hungarian OCR quality by setting Hungarian OCR language where applicable.

## Implementation Plan

- Add a Python Markdown cleanup tool under `//tools/docling`.
- Run the cleaner as a second action in `markdown_file` after docling extraction.
- Keep replacements conservative and line-anchored to avoid structural damage.
- Pass `--ocr-lang hu` for PDF inputs in the docling invocation.
