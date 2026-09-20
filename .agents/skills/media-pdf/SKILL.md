---
name: media-pdf
description: "Use for PDF workflows via media-tools: text/OCR extraction, format conversion, repair, forms, tables, redaction. Examples: 'OCR this scan', 'PDF to Word', 'fix this corrupt PDF', 'extract the tables as CSV', 'fill this form', 'redact the IBANs'"
---

# PDF workflows (media-tools)

Start with `media_probe(path)` to confirm kind (digital vs scanned vs corrupt) and get the ranked tool list.

## Read first: pick the right extractor

| Situation | Tool | Notes |
|---|---|---|
| Born-digital PDF | `pdf_extract_text` | Embedded text, instant |
| Scan or mixed (some pages images) | `pdf_extract_text` with `ocr_mode=auto` (default) | Embedded text kept; only empty pages go through tesseract. `page_sources` map tells you which pages were OCR'd |
| Force full OCR / never OCR | `ocr_mode=force` / `never` | `never` returns embedded text only, no tesseract spawn |
| Tables | `pdf_extract_tables` (per-table CSVs) or `pdf_tables_to_csv` (one combined `page,table,row,col*` CSV) | pdfplumber under the hood; blank spacer rows are preserved faithfully |
| Images/screenshots | `pdf_extract_images` / `pdf_extract_screenshots` | Render at 150+ dpi for reuse |

## Corrupt PDF: repair vs salvage

- `pdf_repair` → returns a **viewable PDF** (rebuilds xref, drops broken objects, reports `{pages_kept, pages_dropped}`). Try first.
- `pdf_salvage` → **extract-only** (txt/png per page + manifest). Use when repair reports too little survives, or when you only need the content, not a file.
- Neither is magic: xref-truncated and EOF-cut files usually recover; garbage-encrypted or 0-parseable-page files return an `Error:` suggesting salvage.

## Convert out

- `pdf_to_markdown` (anydoc, local), `pdf_to_docx` (LibreOffice fallback = text boxes; real layout needs the `docx` extra), `html_to_pdf` (local `.html` file only — URLs are rejected, use `url_to_markdown` for web), `md_to_branded_pdf`, `pdf_to_a` (needs `gs` binary).
- **No PDF→PPTX/XLSX tool exists.** Workaround: `pdf_tables_to_csv` for table data; slides have no local path (LibreOffice can't export Draw→Impress headless).

## Modify

`pdf_merge/split/reorder_pages/delete_pages` (deletes stash the original → `returns_reclaim` restores by ticket), `pdf_compress`, `pdf_rotate`, `pdf_watermark`, `pdf_page_numbers`, `pdf_protect/unlock`, `pdf_sign`, `pdf_fill_form` (needs real AcroForm fields — check `pdf_info` first), `pdf_redact` (burns text out of the file, pages lose selectability — stash + reclaim available), `pdf_compare`.

## PII (Spanish/EU)

`pii_scan` (masked previews, needs `pii` extra) → `pii_redact`. Matches DNI/NIF/NIE/passport/IBAN/email/phone by pattern + checksum. Names and addresses are NOT detected — say so when asked.
