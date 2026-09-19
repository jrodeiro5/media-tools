---
type: Tool Reference
title: PDF Tools
description: "23 PDF processing tools (25 toolkit methods, 2 not yet exposed via MCP/CLI): merge, split, compress, extract text/images, rotate, watermark, page numbers, protect/unlock, sign, fill forms, compare, PDF/A conversion, reorder/delete pages, Markdown export, plus OCR, crop, PDF-to-DOCX, and redaction."
resource: /src/media_tools/tools/pdf.py
tags: [pdf, tools, pypdf, pdfplumber, pypdfium2, liteparse, pdf2docx, Ghostscript, firecrawl]
generated: { by: openwiki/local-ornith-35b, at: 2026-08-22T14:25:15.555Z }
---

## Overview

The `PDFToolkit` class provides 25 PDF processing methods — 23 exposed via the MCP server and 18 via the CLI. Two methods (`ocr`, `crop`) are implemented but not yet wired to either interface.

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
| `pdf_ocr` *(not exposed)* | *(none)* | Extract text via OCR (Tesseract) at configurable DPI | pytesseract (optional) |

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
| `pdf_crop` *(not exposed)* | *(none)* | Crop a page to pixel coordinates (left/bottom/right/top) | pypdfium2 |

### Conversion

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `images_to_pdf` | `pdf images-to-pdf` | Convert one or more images to a single PDF | pypdfium2, Pillow |
| `pdf_to_docx` | `pdf to-docx` | Convert PDF to DOCX | pdf2docx |
| `pdf_redact` | `pdf redact` | Black out sensitive text (by pattern) or rectangular regions | pypdfium2 |

## Implementation Details

### Dependencies

**Required:**
- `pypdf >= 6.15.0` — PDF reading/writing, encryption, rotation
- `pdfplumber >= 0.11` — Text extraction, form field detection
- `pypdfium2 >= 4.0` — PDF rendering to images, page manipulation
- `pdf2docx >= 0.5.13` — PDF-to-DOCX conversion

**Optional:**
- `liteparse >= 2.11.1` — Structured text extraction with bounding boxes
- `pytesseract >= 0.3.10` — OCR text extraction (requires Tesseract system installation)
- `Ghostscript` — PDF/A conversion (requires system installation)
- `firecrawl-anydoc` — Markdown export via CLI (requires `npx firecrawl` + `FIRECRAWL_API_KEY`)

### Key Implementation Notes

- **Page ranges**: Split/reorder/delete commands use 1-indexed page numbers.
- **Path validation**: All tools validate input paths (no traversal, must exist, must be readable).
- **Output directories**: Auto-created if missing; validated for writability.
- **Error handling**: All methods return error strings on failure (not exceptions).
- **Not yet exposed**: `PDFToolkit.ocr` and `PDFToolkit.crop` exist in `pdf.py` but have no `@mcp.tool` or CLI registration. Wire them through `server.py` and `cli.py` to expose them.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how PDF tools are exposed via MCP/CLI
- [Operations & Deployment](/openwiki/operations/deployment.md) — installing optional dependencies
