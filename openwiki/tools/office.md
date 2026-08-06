---
type: Tool Reference
title: Office Tools
description: "2 Office document processing tools: convert to Markdown (via MarkItDown) and convert to PDF (via LibreOffice)."
resource: /src/media_tools/tools/office.py
tags: [office, tools, markitdown, LibreOffice]
---

## Overview

The `OfficeToolkit` class provides 2 Office document processing operations accessible via both the MCP server and CLI.

## Tool List

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `office_to_markdown` | `office to-markdown` | Convert .docx, .pptx, .xlsx to Markdown | markitdown |
| `office_to_pdf` | `office to-pdf` | Convert Office documents to PDF | LibreOffice |

## Implementation Details

### Dependencies

**Required:**
- `markitdown >= 0.1` — Office-to-Markdown conversion (requires `[docx]` extra for .docx support)
- `LibreOffice` — System installation required (macOS binary: `soffice`)

### Key Implementation Notes

- **MarkItDown**: Converts .docx, .pptx, .xlsx to Markdown text. If `output` parameter provided, saves to file; otherwise returns text string.
- **LibreOffice**: Uses `soffice --headless --convert-to pdf` on macOS. Output filename may differ from requested (uses stem of input file).
- **File support**: .docx, .pptx, .xlsx for Markdown; any Office format for PDF.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how Office tools are exposed via MCP/CLI
