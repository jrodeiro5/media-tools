---
type: Tool Reference
title: PDF Tools
description: "21 PDF processing tools: merge, split, compress, extract text/images, rotate, watermark, page numbers, protect/unlock, sign, fill forms, compare, PDF/A conversion, reorder/delete pages, and Markdown export."
resource: /src/media_tools/tools/pdf.py
tags: [pdf, tools, pypdf, pdfplumber, pypdfium2, liteparse, Ghostscript]
---

## Overview

The `PDFToolkit` class provides 21 PDF processing operations accessible via both the MCP server and CLI.

## Tool List

### Core PDF Operations

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `pdf_merge` | `pdf merge` | Merge multiple PDFs into one | pypdf |
| `pdf_split` | `pdf split` | Split PDF by page ranges (e.g., "1-3,5,7-9") | pypdf |
| `pdf_compress` | `pdf compress` | Compress PDF to reduce file size | pypdf |
| `pdf_rotate` | `pdf rotate` | Rotate all pages by angle (default 90°) | pypdf |
| `pdf_info` | `pdf info` | Get metadata: page count, title, author, encryption | pypdf |
| `pdf_reorder_pages` | `pdf reorder` | Reorder pages by 1-indexed list | pypdf |
| `pdf_delete_pages` | `pdf delete` | Remove specific pages | pypdf |

### Text & Image Extraction

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `pdf_extract_text` | `pdf extract-text` | Extract text content (saves to file if `output` provided) | pdfplumber, pypdfium2 |
| `pdf_extract_images` | `pdf extract-images` | Render pages as PNG images | pypdfium2 |
| `pdf_extract_structured` | `pdf extract-structured` | Extract text with bounding boxes (JSON with x, y, width, height, font, confidence) | liteparse (optional) |
| `pdf_extract_screenshots` | `pdf extract-screenshots` | Render pages as PNG screenshots | liteparse (optional) |
| `pdf_to_markdown` | `pdf to-markdown` | Convert PDF/DOCX/HTML/XLSX to Markdown via Firecrawl CLI | firecrawl (external) |

### PDF Security & Formatting

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `pdf_watermark` | `pdf watermark` | Add text or image watermark with opacity/angle | pypdfium2 |
| `pdf_page_numbers` | `pdf page-numbers` | Add page numbers (position: bottom-center, format: "Page {page}") | pypdfium2 |
| `pdf_protect` | `pdf protect` | Add password protection | pypdf |
| `pdf_unlock` | `pdf unlock` | Remove password protection | pypdf |
| `pdf_sign` | `pdf sign` | Add signature image to specific page | pypdfium2 |
| `pdf_fill_form` | `pdf fill-form` | Fill PDF form fields (dict of field_name → value) | pypdfium2 |
| `pdf_compare` | `pdf compare` | Compare two PDFs (page count + text differences) | pdfplumber |
| `pdf_to_a` | `pdf to-a` | Convert to PDF/A archival format (versions 1b, 2a, 3a) | Ghostscript (external) |

### Conversion

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `images_to_pdf` | `pdf images-to-pdf` | Convert one or more images to a single PDF | pypdfium2, Pillow |

## Implementation Details

### Dependencies

**Required:**
- `pypdf >= 5.0.0` — PDF reading/writing, encryption, rotation
- `pdfplumber >= 0.11` — Text extraction, form field detection
- `pypdfium2 >= 4.0` — PDF rendering to images, page manipulation

**Optional:**
- `liteparse >= 2.0` — Structured text extraction with bounding boxes (requires `pip install liteparse`)
- `Ghostscript` — PDF/A conversion (requires system installation)
- `firecrawl` — Markdown export via CLI (requires `npx firecrawl` + `FIRECRAWL_API_KEY`)

### Key Implementation Notes

- **Page ranges**: Split/reorder/delete commands use 1-indexed page numbers.
- **Path validation**: All tools validate input paths (no traversal, must exist, must be readable).
- **Output directories**: Auto-created if missing; validated for writability.
- **Error handling**: All methods return error strings on failure (not exceptions).

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how PDF tools are exposed via MCP/CLI
- [Operations & Deployment](/openwiki/operations/deployment.md) — installing optional dependencies
