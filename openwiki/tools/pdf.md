---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Tool Reference
title: PDF Toolkit
description: "26 PDF processing methods in PDFToolkit — 21 exposed via the CLI and 20 via the MCP server, with ocr and crop implemented but not wired to either interface. Covers merge, split, compress, text/image/structured/screenshots extraction, rotate, info, watermark, page numbers, protect/unlock, sign, fill form, compare, PDF/A, reorder/delete, Markdown export, PDF-to-DOCX, and redaction."
resource: /src/media_tools/tools/pdf.py
tags: [pdf, tools, pypdf, pdfplumber, pypdfium2, liteparse, pdf2docx, reportlab, Ghostscript, firecrawl, redaction]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-19T19:14:37.934Z
sources:
  - id: openwiki-source-f24618d3fb91081293690cc3
    resource: repo://src/media_tools/cli.py
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-f1f4e4d9d900b12b94ee3c47
    resource: repo://src/media_tools/tools/pdf.py
  - id: openwiki-source-f7be093be4a966caaa381229
    resource: repo://src/media_tools/utils.py
  - id: openwiki-source-0f45531f40d627881b1ab052
    resource: repo://tests/check_redact.py
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
---

## Overview

`PDFToolkit` (defined in `src/media_tools/tools/pdf.py`) provides 26 PDF processing methods as a pure
static-method class with no shared mutable state. Every method follows the same contract: it calls
`validate_input` then `validate_output_dir` (see the cross-cutting pipeline in
`src/media_tools/utils.py`), then performs the operation and returns a human-readable string —
surfaces failures as `"Error: …"` and **never raises**.

The methods are exposed through two presentation layers that delegate to the same class:

- **CLI** (`src/media_tools/cli.py`) — 21 `pdf` subcommands.
- **MCP server** (`src/media_tools/server.py`) — 20 `pdf`-tagged tools, plus a scoped entry point
  (`main_pdf`) that enables only the `pdf` tag.

Two methods — `PDFToolkit.ocr` and `PDFToolkit.crop` — are implemented in `pdf.py` but are **not**
wired to either the CLI or the MCP server. All other 24 methods are exposed at least once.

## Tool List

### Core page operations — `pypdf`

| MCP Name | CLI Command | Description |
|----------|-------------|-------------|
| `pdf_merge` | `pdf merge` | Merge multiple PDFs into one (`pypdf.PdfWriter.append`). |
| `pdf_split` | `pdf split` | Split by ranges like `"1-3,5,7-9"` (1-indexed). |
| `pdf_compress` | `pdf compress` | `compress_content_streams()` on each page. |
| `pdf_rotate` | `pdf rotate` | Rotate all pages by angle (default 90°). |
| `pdf_info` | `pdf info` | Page count, title, author, encryption status. |
| `pdf_reorder_pages` | `pdf reorder` | Reorder by 1-indexed list. |
| `pdf_delete_pages` | `pdf delete` | Remove specific pages. |

`pypdf` (`PdfReader` / `PdfWriter`) is the workhorse for page-level operations: merging, splitting,
compressing, rotating, reordering, deleting, protecting, unlocking, and building overlays. Page
indices are **1-indexed** in the public argument (`pages` / `--pages`); the implementation subtracts 1
before indexing `reader.pages`. `reorder_pages` and `delete_pages` validate each requested page is in
range (`1..total`) and return a `"Error: page N out of range"` string otherwise.

### Text & image extraction — `pdfplumber` + `pypdfium2` + `liteparse`

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `pdf_extract_text` | `pdf extract-text` | Extract text (saves to file if `output` provided). | pdfplumber |
| `pdf_extract_images` | `pdf extract-images` | Render pages as PNG images at configurable DPI. | pypdfium2 |
| `pdf_extract_structured` | *(none)* | Structured JSON with bounding boxes (x, y, width, height, font, confidence). | liteparse (optional) |
| `pdf_extract_screenshots` | *(none)* | Render pages as PNG screenshots; optional `page_numbers` filter. | liteparse (optional) |
| `pdf_to_markdown` | `pdf to-markdown` | Convert PDF/DOCX/HTML/XLSX to Markdown via Firecrawl CLI. | firecrawl CLI (external) |
| `pdf_ocr` *(not exposed)* | *(none)* | OCR scanned/image pages at configurable DPI. | pytesseract (optional) |

- `extract_text` opens the file with `pdfplumber` and joins each page's `extract_text()`. When
  `output` is given, the text is written as UTF-8; otherwise the raw text string is returned.
- `extract_images` iterates `pypdfium2.PdfDocument`, rendering each page at `scale = dpi / 72`
  (default 150) and saving `page_NNNN.png` files.
- `extract_structured` uses `liteparse.LiteParse(ocr_enabled, ocr_language, dpi, output_format="json")`
  and emits JSON (`num_pages`, per-page `text_items` with `x/y/width/height/font_name/font_size/confidence`).
- `extract_screenshots` calls `liteparse.LiteParse(...).screenshot(input_path, page_numbers=...)` and
  writes `s.image_bytes` to `page_{page_num:04d}.png`.
- `to_markdown` shells out to the Firecrawl CLI (`npx firecrawl parse <path> -f markdown -k <key>`),
  reading `FIRECRAWL_API_KEY` from the environment. It distinguishes 401 / rate-limit / timeout /
  missing-CLI error strings. Page filtering is accepted but not implemented by the CLI.
- `ocr` (internal only) renders each page and runs `pytesseract.image_to_string`.

### Overlays & security — `reportlab` + `pypdf`

| MCP Name | CLI Command | Description |
|----------|-------------|-------------|
| `pdf_watermark` | `pdf watermark` | Text or image watermark (opacity, angle, color, font size). |
| `pdf_page_numbers` | `pdf page-numbers` | Page numbers at 6 positions, format `"Page {page}"`. |
| `pdf_protect` | `pdf protect` | Add password protection (`writer.encrypt`). |
| `pdf_unlock` | `pdf unlock` | Remove password protection. |
| `pdf_sign` | *(none)* | Place a signature image on a specific page. |
| `pdf_fill_form` | *(none)* | Fill form fields (dict of `field_name → value`). |

Watermark, page numbers, and sign build an overlay with **reportlab** (`pdfgen.canvas`): a page-sized
`A4` packet is drawn, saved to an in-memory `BytesIO`, re-read as a `pypdf.PdfReader`, and merged onto
each content page via `page.merge_page(overlay.pages[0])` before the page is added to the writer.
`watermark` rotates the overlay by `angle` (default 45°) and applies `setFillAlpha(opacity)`;
`add_page_numbers` positions text from a fixed coordinate map (bottom-center default). `protect` calls
`writer.encrypt(password)`; `unlock` first checks `reader.is_encrypted` and returns an error if the
input is not protected, then `reader.decrypt(password)` and copies pages. `sign` validates the target
page is in range and places the signature image on exactly that page. `fill_form` requires the input
to have form fields (`reader.get_fields()`), then applies `writer.update_page_form_field_values`.

### Conversion — Ghostscript, Firecrawl, pdf2docx, `pypdfium2`

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `images_to_pdf` | `pdf images-to-pdf` | Convert one or more images to a single PDF. | pypdfium2, Pillow, reportlab |
| `pdf_to_docx` | *(none)* | Convert PDF to DOCX. | pdf2docx |
| `pdf_to_a` | `pdf to-a` | Convert to PDF/A archival format. | Ghostscript (external) |
| `pdf_redact` | *(none)* | Black out text by pattern or rectangular regions. | pypdfium2, Pillow |

- `images_to_pdf` opens each image with **Pillow**, converts `RGBA`/`P` modes to `RGB`, draws each
  onto an `A4` reportlab page, and writes a single PDF.
- `to_docx` wraps `pdf2docx.Converter` (`cv.convert()` / `cv.close()`).
- `pdf_to_a` runs Ghostscript (`gs`) with `-dPDFA=<version>`, `-sDEVICE=pdfwrite`, and
  `-sPDFCOnvertToRGB`. Supported versions are **`1a, 1b, 2a, 2b, 3a, 3b, 3u`** (default `1b`). A
  missing `gs` is reported as a specific `"Error: Ghostscript (gs) not found"` string.
- `compare` (pdfplumber-based in spirit but implemented with `pypdf`) reports page counts and
  per-page text-length differences; if page counts differ it reports that text comparison is skipped.

### Redaction semantics — `pdf_redact`

`redact` (exposed via MCP only) removes sensitive content **permanently** rather than merely covering
it. It accepts `text_patterns` (strings) and/or `rect_areas` (`{page, x, y, width, height}`) and:

1. Collects per-page rectangles. For `text_patterns`, it opens the source with `pdfplumber`,
   `extract_words()`, and records the bounding box of every word containing a pattern. `rect_areas`
   contribute their boxes directly (default width/height 100/50).
2. For each page, if there are no rectangles the page is copied through untouched. Otherwise the page
   is **rasterized at 144 dpi** (`scale = 2.0`, since the source is treated as 72 dpi), a black
   rectangle is painted over each redaction region (scaled by 2.0), and the page is rewritten as an
   **image-only** PDF page.

The trade-off: because redacted pages become image-only, **those pages lose all selectable text**,
while unredacted pages keep their original content stream. The bundled test
(`tests/check_redact.py`) asserts the redacted string is absent from both `pdfplumber` extraction and
the raw PDF bytes.

**Rotation limitation:** redaction is **not supported on rotated pages**. Rectangles are placed as if
the source page were unrotated, so a page with a non-identity `/Rotate` transform will have its
redaction region misaligned.

## Implementation Details

### Dependencies

**Required (from `pyproject.toml`):** `pypdf >= 6.15.0`, `pypdfium2 >= 4.0`, `pdfplumber >= 0.11`,
`Pillow >= 12.3.0`, `reportlab >= 4.0`, `pdf2docx >= 0.5.13`, plus `firecrawl-anydoc`, `pytesseract`,
`liteparse` (all present in `pyproject.toml` but guarded at import time).

**Optional (guarded at runtime):**

- `liteparse >= 2.11.1` — structured extraction + screenshots. Imported at module load into
  `HAS_LITEPARSE`; `extract_structured` / `extract_screenshots` return `"Error: liteparse not
  installed. Run: pip install liteparse"` when absent.
- `pytesseract >= 0.3.10` — OCR (internal `ocr`). Imported inside the method; missing it returns a
  `"Error: pytesseract not installed …"` string. Requires the Tesseract system binary.
- **Ghostscript (`gs`)** — PDF/A conversion. Invoked as a subprocess; a missing binary is caught as
  `FileNotFoundError` and reported as a specific install hint.
- **Firecrawl CLI** (`npx firecrawl`) — Markdown export. Requires `FIRECRAWL_API_KEY` and, when the
  CLI is absent, a `"Error: firecrawl CLI not found. Install with: npm install -g firecrawl"` string.

### CLI vs. MCP exposure

`cli.py` registers 21 `pdf` subcommands (`merge, split, compress, rotate, extract-text,
extract-images, to-markdown, watermark, page-numbers, protect, unlock, images-to-pdf, reorder,
delete, sign, fill-form, compare, to-a`). The CLI is missing handlers for `sign`'s `--signature`
option wiring beyond the default, and has **no** `redact`, `to-docx`, `extract-structured`, or
`extract-screenshots` subcommands. `server.py` registers 20 MCP tools under the `pdf` tag and adds a
scoped entry point `main_pdf` (via `_run_scoped("pdf")`) that enables only `pdf`-tagged tools,
backed by console scripts `media-tools-server-pdf` in `pyproject.toml`.

The CLI uses different argument names than the server (`input`/`output`/`pages`/`quality`/`angle` /
`text`/`image`/`opacity`/`position`/`format`/`password`/`signature`/`page`/`pos`/`field`/`other`/
`version`), but both ultimately call the same `PDFToolkit` static methods.

### Common invariants

- **Page ranges** (split/reorder/delete) use 1-indexed page numbers.
- **Path validation**: every tool runs `validate_input` (blocks `..` traversal, requires the path to
  exist, be a file, and be readable; allows `http(s)://` URLs through for firecrawl) then
  `validate_output_dir` (auto-creates the parent, checks writability).
- **Error convention**: all methods return `"Error: …"` strings and never raise; the CLI wraps
  handler exceptions in `{"error": ...}` JSON and returns exit code 1.
- **Not yet exposed**: `PDFToolkit.ocr` and `PDFToolkit.crop` exist in `pdf.py` but have no
  `@mcp.tool` or CLI registration.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how PDF tools are exposed via MCP/CLI
- [Server vs. CLI Entry Points](/openwiki/architecture/server-and-cli.md) — the two presentation layers
- [Operations & Deployment](/openwiki/operations/deployment.md) — installing optional dependencies
