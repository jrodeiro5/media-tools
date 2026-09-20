# Changelog

## Unreleased

- `pdf2docx` (AGPL-3.0 via PyMuPDF) moved to the optional `docx` extra; `pdf_to_docx` falls back to LibreOffice without it.
- New tools (90→104): `video_mute`, `html_to_pdf`, `pdf_tables_to_csv`, `image_grayscale/sharpen/circle_crop/split_tiles`, `pdf_repair`, `audio_to_srt`, `video_transcribe`, `image_upscale` (FSRCNN), `image_blur_faces`, `video_blur_faces`, `media_probe`.
- `ocr_mode=auto|force|never` on the PDF OCR path (embedded text first, tesseract only where needed).
- Refusal-ticket prototype (`refusals.py`, string-compatible with `Error:`).
- `openai` is now a required dependency (LiteLLM proxy transport); `opencv-python-headless` swapped for `opencv-contrib-python-headless` (same 5.0.0.93, Apache-2.0) for FSRCNN/Haar.
- `returns_reclaim` exposes `search_dir`; `video_subtitle_burn` pre-checks libass; `image_remove_background` returns `Error:` instead of `sys.exit` when onnxruntime is missing.

## 0.1.0 — 2026-09-20

First tagged release.

- 90 MCP tools over PDF, image, audio, video and Office files, plus a CLI covering most of them.
- PII: `pii_scan` / `pii_redact` for Spanish and EU identifiers (DNI/NIF, NIE, passport, IBAN, email, phone) via the optional `pii` extra; `pdf_redact` removes the text from the file.
- Office: `office_inspect` / `office_edit` (OfficeCLI, edits a copy), `url_to_markdown` (Firecrawl, cloud, opt-in).
- `batch_sweep`, `returns_reclaim`, brand kit, social packs, silence chunking, audio transcription.
- `MEDIA_TOOLS_SEARCH=1` lists only `search_tools` + `call_tool` (~330 tokens instead of ~13.7k).
- CI: ruff, mypy, bandit, semgrep, gitleaks, CodeQL, zizmor, dependency review.
- Known limits: streamable-http only (no stdio); `pdf2docx` pulls PyMuPDF (AGPL-3.0); tests are assert scripts.
