---
type: Quickstart
title: media-tools — Quickstart
description: "Getting started with media-tools: a Python MCP server and CLI providing 37+ multimedia processing tools across PDF, image, audio, video, and Office document categories."
resource: /pyproject.toml
tags: [overview, getting-started, MCP, CLI, multimedia]
---

## What Is media-tools?

`media-tools` is a Python package that exposes **37+ multimedia processing tools** via two interfaces:

1. **MCP Server** — a FastMCP-based server running on `streamable-http` (default port 8020), designed for browser-based AI assistants (e.g., OpenWebUI).
2. **CLI** — an agent-native command-line interface for direct shell/script invocation.

The project was built to provide a TinyWow/ILovePDF-like experience powered by conversational AI, integrating with OpenWebUI and LiteLLM for Gemini/Mistral model access.

## Tool Categories

| Category | MCP Tools | CLI Commands | Key Dependencies |
|----------|-----------|--------------|-----------------|
| [PDF](/openwiki/tools/pdf.md) | 21 | 17 | pypdf, pdfplumber, pypdfium2, liteparse, Ghostscript |
| [Image](/openwiki/tools/image.md) | 6 | 12 | Pillow, pillow-heif, pytesseract, rembg |
| [Audio](/openwiki/tools/audio.md) | 5 | 5 | pydub |
| [Video](/openwiki/tools/video.md) | 6 | 5 | ffmpeg |
| [Office](/openwiki/tools/office.md) | 2 | 2 | markitdown, LibreOffice |

## Quick Start

### Install

```bash
cd /Users/jrodeiro/dev/infra/media-tools
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Run the MCP Server

```bash
# Default: streamable-http on port 8020
media-tools-server

# Custom port
PORT=9090 media-tools-server
```

The server exposes all 37+ tools via `http://127.0.0.1:8020/mcp`.

### Use the CLI

```bash
# PDF
media-tools pdf merge --input f1.pdf f2.pdf --output merged.pdf
media-tools pdf split --input doc.pdf --output out/ --pages "1-3,5,7-9"

# Image
media-tools image convert --input photo.jpg --output photo.png
media-tools image ocr --input scan.png

# Audio
media-tools audio convert --input song.mp3 --output song.wav

# Video
media-tools video convert --input clip.mp4 --output clip.webm

# Office
media-tools office to-markdown --input report.docx
media-tools office to-pdf --input report.docx --output report.pdf
```

## Architecture Overview

- **Server**: `src/media_tools/server.py` — FastMCP server with 37+ `@mcp.tool` registrations.
- **CLI**: `src/media_tools/cli.py` — Command dispatcher with 37 handlers across 5 categories.
- **Toolkits**: `src/media_tools/tools/{pdf,image,audio,video,office}.py` — Pure static-method classes.
- **Utilities**: `src/media_tools/utils.py` — Shared validation, logging, subprocess helpers.

See [Architecture Overview](/openwiki/architecture/overview.md) for full details.

## Deployment

- **Transport**: `streamable-http` (required for browser-based clients; `stdio` only works for local CLI agents).
- **Port**: configurable via `PORT` env var (default 8020).
- **Logging**: configurable via `LOG_LEVEL` env var (default INFO).
- **Dev tooling**: ruff, bandit, mypy, semgrep, vulture, radon (configured in `pyproject.toml`).
- **CI/CD**: GitHub Actions workflow at `.github/workflows/openwiki-update.yml` runs scheduled OpenWiki updates.

See [Operations & Deployment](/openwiki/operations/deployment.md) for full details.

## Backlog

The following areas were identified but deferred from this initial documentation pass:

| Area | Source Anchor | Reason Deferred |
|------|---------------|-----------------|
| `convert_pdf.py` standalone script | `/convert_pdf.py` | One-off DeepSeek OCR pipeline with LaTeX cleanup; not part of the main package API |
| `STAR_REPORT.md` project retrospective | `/STAR_REPORT.md` | Historical context; not runtime-relevant |
| GitNexus integration details | `/AGENTS.md`, `/CLAUDE.md` | Code intelligence layer; documented separately via GitNexus MCP tools |
| OpenWebUI integration guide | `/STAR_REPORT.md` | Infrastructure-specific; out of scope for the library itself |
| LiteParse structured extraction internals | `/src/media_tools/tools/pdf.py` (lines 16-20) | Optional dependency; low usage frequency |
