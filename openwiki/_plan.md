---
type: Plan
title: Initial Wiki Documentation Plan
description: Temporary plan for the initial media-tools wiki documentation, listing pages to create, source evidence, and relationships.
tags: [plan, internal]
---

## Pages to Create

### 1. /openwiki/quickstart.md
- **Purpose**: Entry point; overview of the project, how to get started, links to all sections.
- **Source evidence**: `pyproject.toml` (project metadata), `AGENTS.md` (OpenWiki section), `STAR_REPORT.md` (situation summary)

### 2. /openwiki/architecture/overview.md
- **Purpose**: Server architecture (FastMCP-based), CLI architecture, entry points, transport modes.
- **Source evidence**: `src/media_tools/server.py` (MCP server setup, all tool registrations), `src/media_tools/cli.py` (CLI dispatcher, COMMANDS dict), `pyproject.toml` (entry points), `STAR_REPORT.md` (streamable-http decision)

### 3. /openwiki/tools/pdf.md
- **Purpose**: All 17 PDF tools, their parameters, dependencies (pypdf, pdfplumber, pypdfium2, liteparse, Ghostscript).
- **Source evidence**: `src/media_tools/tools/pdf.py` (PDFToolkit class), `src/media_tools/server.py` (MCP registrations for PDF tools), `pyproject.toml` (dependencies)

### 4. /openwiki/tools/image.md
- **Purpose**: All 12 image tools (convert, resize, compress, crop, rotate, flip, text overlay, border, merge, blur, OCR, info), supported formats, dependencies (Pillow, pillow-heif, pytesseract, rembg).
- **Source evidence**: `src/media_tools/tools/image.py` (ImageToolkit class), `src/media_tools/server.py` (MCP registrations), `pyproject.toml`

### 5. /openwiki/tools/audio.md
- **Purpose**: All 5 audio tools (convert, trim, fade, speed, info), dependencies (pydub).
- **Source evidence**: `src/media_tools/tools/audio.py` (AudioToolkit class), `src/media_tools/server.py`

### 6. /openwiki/tools/video.md
- **Purpose**: All 5 video tools (convert, trim, compress, to_gif, probe, extract_audio), dependencies (ffmpeg).
- **Source evidence**: `src/media_tools/tools/video.py` (VideoToolkit class), `src/media_tools/server.py`

### 7. /openwiki/tools/office.md
- **Purpose**: 2 Office tools (to_markdown, to_pdf), dependencies (markitdown, LibreOffice).
- **Source evidence**: `src/media_tools/tools/office.py` (OfficeToolkit class), `src/media_tools/server.py`

### 8. /openwiki/operations/deployment.md
- **Purpose**: Server deployment (streamable-http on port 8020), CLI usage, dev tooling (ruff, bandit, mypy, semgrep), pre-commit hooks, GitHub Actions workflow.
- **Source evidence**: `src/media_tools/server.py` (main()), `src/media_tools/cli.py` (main()), `pyproject.toml` (dev deps, scripts), `.pre-commit-config.yaml`, `.semgrep.yaml`, `.github/workflows/openwiki-update.yml`

## Relationships (concept -> meaning -> concept)

- `architecture/overview` -> exposes via FastMCP -> `tools/pdf`, `tools/image`, `tools/audio`, `tools/video`, `tools/office`
- `architecture/overview` -> CLI dispatcher -> `tools/pdf`, `tools/image`, `tools/audio`, `tools/video`, `tools/office`
- `tools/pdf` -> depends on pypdf/pdfplumber/pypdfium2 -> `operations/deployment` (external deps)
- `tools/image` -> depends on Pillow/rembg/tesseract -> `operations/deployment` (external deps)
- `tools/video` -> depends on ffmpeg -> `operations/deployment` (external deps)
- `tools/office` -> depends on LibreOffice/markitdown -> `operations/deployment` (external deps)
- `tools/pdf` -> calls ImageToolkit.images_to_pdf -> `tools/image`
- `tools/video` -> calls ffmpeg to extract audio -> `tools/audio` (via pydub)
- `operations/deployment` -> GitHub Actions workflow -> `architecture/overview` (automated wiki updates)

## Remaining Questions

- `convert_pdf.py` is a standalone script (not part of the package) — used for a one-off DeepSeek OCR pipeline with LaTeX cleanup. Not documented in the main package.
- `STAR_REPORT.md` is a project retrospective — useful context but not part of the runtime.
