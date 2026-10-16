---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Quickstart
title: media-tools — Quickstart
description: "Getting started with media-tools: a Python MCP server and CLI providing 90 multimedia processing tools across PDF, image, audio, video, Office, PII, AI, Text-to-Speech, and batch categories."
tags: [overview, getting-started, MCP, CLI, multimedia]
sources:
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
  - id: openwiki-source-f24618d3fb91081293690cc3
    resource: repo://src/media_tools/cli.py
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
generated: { by: "openwiki/0.5.2", at: "2026-09-20T15:47:08.433Z" }
---

## What Is media-tools?

`media-tools` is a Python package that exposes **90 multimedia processing tools** via two interfaces:

1. **MCP Server** — a FastMCP-based server running on `streamable-http` (default port 8020), designed for browser-based AI assistants (e.g., OpenWebUI).
2. **CLI** — an agent-native command-line interface for direct shell/script invocation.

The project was built to provide a TinyWow/ILovePDF-like experience powered by conversational AI, integrating with OpenWebUI and LiteLLM for Gemini/Mistral model access.

## Tool Categories

| Category | MCP Tools | CLI Commands | Key Dependencies |
|----------|-----------|--------------|-----------------|
| [PDF](/openwiki/tools/pdf.md) | 27 | 21 | pypdf, pdfplumber, pypdfium2, liteparse, pdf2docx, Ghostscript, reportlab |
| [Image](/openwiki/tools/image.md) | 18 | 16 | Pillow, pillow-heif, pytesseract, rembg |
| [Audio](/openwiki/tools/audio.md) | 12 | 11 | pydub |
| [Video](/openwiki/tools/video.md) | 21 | 19 | ffmpeg, moviepy, opencv |
| [Office](/openwiki/tools/office.md) | 5 | 2 | markitdown, LibreOffice, OfficeCLI, Firecrawl |
<!-- openwiki: broken internal link [/openwiki/tools/pii.md] file "/openwiki/tools/pii.md" does not exist. Fix the href or restore the target, then delete this comment. -->
| [PII](/openwiki/tools/pii.md) | 2 | 2 | Presidio (optional) |
| [AI Documents](/openwiki/tools/ai.md) | 3 | 0 | anydoc, LiteLLM (Gemma 4) |
| [Text-to-Speech](/openwiki/tools/tts.md) | 1 | 0 | LiteLLM proxy (Kokoro) |
| Batch | 1 | 1 | built-in sweep module |

The 90 MCP tools are tagged (`pdf`, `image`, `audio`, `video`, `office`, `pii`, `ai`, `tts`, `batch`) so category-scoped servers can expose a single category.

## Quick Start

### Install

```bash
cd media-tools
uv sync                          # core dependencies
uv sync --extra docx             # adds pdf2docx for real-layout PDF→DOCX
uv sync --extra pii              # adds Presidio for PII scan/redact
uv sync --group dev              # ruff, bandit, mypy, semgrep, vulture, radon
```

### Run the MCP Server

```bash
# Default: streamable-http on port 8020
media-tools-server

# Custom port
PORT=9090 media-tools-server
```

The server exposes all 90 tools via `http://127.0.0.1:8020/mcp`.

To expose only one family of tools (and keep the client's context small), run a
scoped server: `media-tools-server-pdf`, `-image`, `-audio`, `-video`, `-office`,
`-ai` or `-tts`.

Set `MEDIA_TOOLS_SEARCH=1` on the full server to expose just `search_tools` +
`call_tool` (~330 tokens instead of ~13.7k) and let the agent find tools by
query.

### Use the CLI

Input files are **positional arguments**; `--output` is always an option flag:

```bash
# PDF
media-tools pdf merge a.pdf b.pdf --output merged.pdf
media-tools pdf compress merged.pdf --output small.pdf
media-tools pdf split doc.pdf --output out/ --pages "1-3,5,7-9"

# Image
media-tools image convert photo.jpg --output photo.png
media-tools image ocr scan.png

# Audio
media-tools audio convert song.mp3 --output song.wav
media-tools audio normalize song.wav --output normalized.wav

# Video
media-tools video convert clip.mp4 --output clip.webm

# Office
media-tools office to-markdown report.docx
media-tools office to-pdf report.docx --output report.pdf

# PII
media-tools pii scan document.pdf
media-tools pii redact document.pdf --output redacted.pdf

# Batch
media-tools batch sweep ./input/ --output ./output/ --op image_convert --pattern "*.png"
```

## Architecture Overview

- **Server**: `src/media_tools/server.py` — FastMCP server with 90 `@mcp.tool` registrations, each tagged (`pdf`, `image`, `audio`, `video`, `office`, `pii`, `ai`, `tts`, `batch`).
- **CLI**: `src/media_tools/cli.py` — argparse-based dispatcher with 73 commands across 8 categories (pdf, image, audio, video, office, pii, batch, returns). Input files are positional arguments.
- **Toolkits**: 8 static-method classes in `src/media_tools/tools/` — `PDFToolkit`, `ImageToolkit`, `AudioToolkit`, `VideoToolkit`, `OfficeToolkit`, `AIToolkit`, `TTSToolkit`, `PiiToolkit`. Plus the sweep module at `src/media_tools/sweep.py`.
- **Utilities**: `src/media_tools/utils.py` — Shared validation, logging, subprocess helpers.
- **Console scripts**: 9 in `pyproject.toml` — `media-tools` (CLI), `media-tools-server` (all tools), and 7 category-scoped servers (`media-tools-server-{pdf,image,audio,video,office,ai,tts}`), each `main_{x}` calling `mcp.enable(tags={tag}, only=True)` so a scoped server exposes only tools with the matching tag.

See [Architecture Overview](/openwiki/architecture/overview.md) for full details.

## Deployment

- **Transport**: `streamable-http` (required for browser-based clients; `stdio` only works for local CLI agents).
- **Port**: configurable via `PORT` env var (default 8020).
- **Logging**: configurable via `LOG_LEVEL` env var (default INFO).
- **Dev tooling**: ruff, bandit, mypy, semgrep, vulture, radon, complexipy, pyrefly, hexora (configured in `pyproject.toml`).
- **CI**: GitHub Actions workflow at `.github/workflows/ci.yml` runs ruff, mypy, bandit, semgrep, gitleaks on Python 3.11 and 3.13. Additional workflows for CodeQL, dependency review, gitleaks, Renovate validation, and zizmor.

See [Operations & Deployment](/openwiki/operations/deployment.md) for full details.
