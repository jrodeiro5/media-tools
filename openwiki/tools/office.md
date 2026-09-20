---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Tool Reference
title: Office Tools
description: "2 Office document tools exposed via the MCP server and CLI: office_to_markdown (converts 14 Office/text formats to Markdown via firecrawl-anydoc) and office_to_pdf (converts Office documents to PDF via LibreOffice soffice headless)."
resource: /src/media_tools/tools/office.py
tags: [office, tools, anydoc, firecrawl-anydoc, LibreOffice, soffice]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-19T19:14:37.934Z
sources:
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-f24618d3fb91081293690cc3
    resource: repo://src/media_tools/cli.py
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-b635fea87ca1e53077f6aba1
    resource: repo://src/media_tools/tools/__init__.py
  - id: openwiki-source-a3224bb41cc4d6a3c172db92
    resource: repo://src/media_tools/tools/office.py
  - id: openwiki-source-f7be093be4a966caaa381229
    resource: repo://src/media_tools/utils.py
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
---

## Overview

The `OfficeToolkit` class provides 2 Office document operations exposed **only** through the
MCP server (`office_to_markdown`, `office_to_pdf`) and the CLI (`office to-markdown`,
`office to-pdf`). Both are thin static methods that gate on input/output validation and then
delegate to an external converter — firecrawl-anydoc for Markdown, LibreOffice (`soffice`) for
PDF. They share the error convention of every other tool in the package: each method returns a
string and **never raises**, surfacing failures as `"Error: …"` results.

## Tool List

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `office_to_markdown` | `office to-markdown` | Convert Office/text files (14 formats) to Markdown | firecrawl-anydoc (`anydoc`) |
| `office_to_pdf` | `office to-pdf` | Convert Office documents to PDF | LibreOffice (`soffice`) |

Both are registered in `server.py` under the `office` tag and wired in `cli.py` under the
`office` category. There is **no AI integration layer** for these tools — unlike `AIToolkit`,
they perform a direct format conversion rather than reading a document to Markdown and calling an
LLM.

## Implementation Details

### Dependencies

**Required:**
- `firecrawl-anydoc >= 0.1.0` (imported as `anydoc`) — Office-to-Markdown conversion. Rust-based,
  ~5 ms/doc, supports 14 formats.
- `LibreOffice` — system installation required (the macOS binary is `soffice`).

### Supported formats

`to_markdown` converts **14 formats**: `.docx, .pptx, .xlsx, .odt, .odp, .rtf, .epub, .csv, .pdf`
(plus the remaining Office/text formats firecrawl-anydoc recognizes). The old documentation's
"`MarkItDown` / .docx, .pptx, .xlsx" description has been replaced by firecrawl-anydoc.

### `to_markdown`

```
input_path
    │
    ├─ validate_input(path)  (rejects empty / traversal / missing / unreadable; allows URLs)
    │
    └─ anydoc.to_markdown(path)  → text
            ├─ output given? → validate_output_dir(output) + write_text(text, utf-8) → "Converted to markdown → {output}"
            └─ no output → return text
    anydoc errors (EncryptedError / UnsupportedError / ConvertError) / any Exception → "Error: {exc}"
```

`to_markdown(input_path, output=None)` (office.py):

1. **Validate** — `validate_input(input_path)` rejects empty paths, `..` traversal, missing files,
   and unreadable files (URLs pass through). A failed check returns its error string and aborts.
2. **Convert** — `anydoc.to_markdown(input_path)` materializes the document to Markdown text.
3. **Output** — when `output` is provided, `validate_output_dir(output)` creates/validates the
   directory and the text is written with `Path(output).write_text(text, encoding="utf-8")`,
   returning `"Converted to markdown → {output}"`; otherwise the text string is returned directly.
4. **Errors** — `anydoc.EncryptedError`, `anydoc.UnsupportedError`, and `anydoc.ConvertError` are
   caught (the first two grouped, `ConvertError` separately) and fall through to a broad
   `Exception` handler; all return `"Error: {exc}"`.

### `to_pdf`

`to_pdf(input_path, output)` (office.py):

1. **Validate** — runs `validate_input(input_path)` **and** `validate_output_dir(output)` (output
   is required, unlike Markdown).
2. **Convert** — runs LibreOffice headless:
   `soffice --headless --convert-to pdf --outdir <output's parent> <input_path>`, via
   `_subprocess_with_logging`. A non-zero return code yields `"Error: <stderr>"`.
3. **Rename** — `soffice` writes `<stem of input>.pdf` into the output's parent directory, which
   may differ from the requested `output`. When `Path(parent) / f"{stem}.pdf" != output`, the
   code renames the generated file to the requested path, **silently ignoring an `OSError`** (the
   files may already match). The original `desc` string is returned.

<!-- openwiki: mermaid parse failed and this diagram was converted to a text fence so it does not break rendering. Fix the diagram source and restore the mermaid fence. Parser error: Heuristic: an unescaped angle bracket inside a label breaks rendering; rephrase the label. -->
```text
flowchart TD
    PDF["to_pdf(input, output)"] --> V1["validate_input(input)"]
    V1 -->|invalid| E1["return error string"]
    V1 -->|ok| V2["validate_output_dir(output)"]
    V2 -->|invalid| E2["return error string"]
    V2 -->|ok| RUN["run soffice --headless --convert-to pdf --outdir <parent> <input>"]
    RUN -->|rc != 0| E3["return 'Error: <stderr>'"]
    RUN -->|ok| GEN["generate <stem>.pdf in parent dir"]
    GEN --> DIFF{"generated path != output?"}
    DIFF -->|yes| RENAME["try actual.rename(output) — ignore OSError"]
    DIFF -->|no| RET["return success string"]
    RENAME --> RET
```

### Key Implementation Notes

- **No raising**: every method returns a result or `"Error: …"` string; failures never propagate
  as exceptions.
- **PDF output filename**: LibreOffice names the file after the *input* file's stem, not the
  requested output. The tool renames the generated `<stem>.pdf` to the requested `output` when the
  two differ, swallowing an `OSError` so a mismatching final filename does not surface.
- **Output required for PDF**: `to_pdf` requires an `output` argument, whereas `to_markdown`'s is
  optional (text is returned when no output is given).

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how Office tools are exposed via MCP/CLI
- [Server vs. CLI Entry Points](/openwiki/architecture/server-and-cli.md) — the office console script and CLI wiring
- [PDF Tools](/openwiki/tools/pdf.md) — the 23 standalone PDF processing tools
- [AI Document Tools](/openwiki/tools/ai.md) — the tools that read a document via anydoc and call an LLM (no CLI commands)
