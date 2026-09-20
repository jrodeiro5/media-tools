---
name: media-tools
description: "Use when the user wants to process PDF, image, audio, video or Office files with the media-tools MCP server. Examples: 'merge these PDFs', 'transcribe this clip', 'what can you do with this file', 'remove the background', 'scan for Spanish ID numbers'"
---

# media-tools — local-first multimedia MCP server

104 tools. Files never leave the machine (except `url_to_markdown`, which uses Firecrawl cloud).

## Connect

Full server: `http://localhost:8020/mcp` (`uv run media-tools-server`).
Low-context mode: `MEDIA_TOOLS_SEARCH=1` exposes only `search_tools` + `call_tool` (~330 tokens instead of ~13.7k) — prefer it when the task needs few tools.
Docker: `docker run -p 8020:8020 ghcr.io/jrodeiro5/media-tools` (full binaries inside: ffmpeg with libass, tesseract, ghostscript, LibreOffice).

## Start every task with media_probe

Don't guess tool names. Call `media_probe(path)` first: it sniffs the file (magic bytes + metadata) and returns a ranked list of applicable tools with one-line reasons. Scanned PDF → OCR tools first; corrupt PDF → `pdf_repair`; GIF → `gif_to_mp4`.

## Hard conventions (the server enforces them)

- **Never in place.** Every tool writes to a new output path and refuses colliding ones (you'll get `E_OVERWRITE_BLOCKED` with a suggested path — use it).
- **Errors are structured.** Failures return `Error: ...` strings; common ones carry machine-readable tickets (`E_MISSING_BINARY` names the binary + install hint, `E_ENCRYPTED_PDF`, `E_OVERWRITE_BLOCKED`). Match on the prefix, show the hint, don't retry blindly.
- **Optionals change behavior.** Without extras: `pdf_to_docx` falls back to LibreOffice (text in boxes, layout lost), `pii_scan`/`pii_redact` fail (need `pii` extra + Presidio), `pdf_to_docx` layout reconstruction needs the `docx` extra. Ask the user before assuming an extra is installed.
- **Missing system binaries degrade gracefully:** no `gs` → `pdf_to_a` errors; Homebrew ffmpeg without libass → `video_subtitle_burn` errors (Debian/docker ffmpeg is fine); no onnxruntime → `image_remove_background` errors. Each message says what to install.

## Family skills (load the one that fits)

- PDF jobs (extract/OCR/repair/fill/convert): `media-pdf`
- Video jobs (transcode/subtitles/faces/social): `media-video`
- Single-shot image/audio/office jobs usually need no extra skill — `media_probe` + the tool description suffice.
