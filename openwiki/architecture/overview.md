---
type: Architecture
title: Architecture Overview
description: "How media-tools is structured: FastMCP server, CLI dispatcher, seven toolkit modules, shared utilities, tag-based server selection, and the relationship between MCP and CLI entry points."
resource: /src/media_tools/server.py
tags: [architecture, server, CLI, FastMCP, entry-points, tags]
generated: { by: openwiki/local-ornith-35b, at: 2026-08-22T14:25:15.555Z }
---

## High-Level Design

media-tools is a **dual-interface** Python package. The same underlying toolkits are exposed through both an MCP server (for AI agents) and a CLI (for scripts/operators).

The package ships **49 MCP tools** and **42 CLI commands** across seven toolkit modules: PDF, image, audio, video, office, AI, and TTS.

```
src/media_tools/
├── server.py          # FastMCP server — 49 MCP tool registrations + 8 console scripts
├── cli.py             # CLI dispatcher — 42 command handlers
├── utils.py           # Shared: logging, validation, subprocess helpers
└── tools/
    ├── __init__.py    # Re-exports all 7 toolkits
    ├── pdf.py         # PDFToolkit (25 methods, 23 MCP tools)
    ├── image.py       # ImageToolkit (14 methods)
    ├── audio.py       # AudioToolkit (7 methods)
    ├── video.py       # VideoToolkit (17 methods)
    ├── office.py      # OfficeToolkit (2 methods)
    ├── ai.py          # AIToolkit (3 MCP tools — summarize, qa, translate)
    └── tts.py         # TTSToolkit (1 MCP tool — text_to_speech)
```

## Entry Points

Eight console scripts are defined in `pyproject.toml`. The first is the full server; the remaining seven are **category-scoped** servers that expose only one toolset via FastMCP's tag filtering.

| Script | Module | Purpose |
|--------|--------|---------|
| `media-tools` | `media_tools.cli:main` | CLI dispatcher (agent-native) — 42 commands |
| `media-tools-server` | `media_tools.server:main` | Full MCP server (all 49 tools) |
| `media-tools-server-pdf` | `media_tools.server:main_pdf` | PDF-only server (tag `pdf`) |
| `media-tools-server-image` | `media_tools.server:main_image` | Image-only server (tag `image`) |
| `media-tools-server-audio` | `media_tools.server:main_audio` | Audio-only server (tag `audio`) |
| `media-tools-server-video` | `media_tools.server:main_video` | Video-only server (tag `video`) |
| `media-tools-server-office` | `media_tools.server:main_office` | Office-only server (tag `office`) |
| `media-tools-server-ai` | `media_tools.server:main_ai` | AI document tools server (tag `ai`) |
| `media-tools-server-tts` | `media_tools.server:main_tts` | Text-to-speech server (tag `tts`) |

### MCP Server (`server.py`)

The server is built on [FastMCP](https://github.com/structuredlabs/fastmcp). It creates a single `FastMCP` instance named "Media Tools" and registers each tool as a `@mcp.tool` decorator. Every tool now carries a `tags={...}` value (`pdf`, `image`, `audio`, `video`, `office`, `ai`, `tts`) that scopes it to a category.

```python
mcp = FastMCP("Media Tools", instructions="...")

@mcp.tool(name="pdf_merge", tags={"pdf"})
def pdf_merge(files: list[str], output: str) -> str:
    return PDFToolkit.merge(files, output)
```

**Key design decisions:**
- **Transport**: `streamable-http` (not `stdio`). This is required for browser-based clients like OpenWebUI. The `stdio` transport only works for local CLI agents.
- **Port**: Configurable via `PORT` env var (default 8020).
- **Tool registration**: Each `@mcp.tool` function is a thin wrapper that delegates to the corresponding `ToolkitClass.method()`.

### Category-scoped servers (`main_*`)

Each category script calls `_run_scoped(tag)`, which enables **only** the tools tagged with that category via `mcp.enable(tags={tag}, only=True)` before starting the server:

```python
def _run_scoped(tag: str):
    mcp.enable(tags={tag}, only=True)
    port = int(os.environ.get("PORT", "8020"))
    mcp.run(transport="streamable-http", port=port)


def main_pdf():
    _run_scoped("pdf")


def main_ai():
    _run_scoped("ai")


def main_tts():
    _run_scoped("tts")
```

This lets an operator run a lean server exposing a single category (e.g. `media-tools-server-ai`) instead of all 49 tools, without maintaining separate server code.

### CLI (`cli.py`)

The CLI uses an `argparse`-based parser with a two-level structure: `category` (pdf, image, audio, video, office) → `command`. Handlers are plain functions taking a parsed namespace (`ns`), and the `add()` helper registers each command with its flags:

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="media-tools")
    categories = parser.add_subparsers(dest="category", required=True)

    def add(cat_parsers, name, handler, *arg_specs):
        sub = cat_parsers.add_parser(name)
        for flags, kwargs in arg_specs:
            sub.add_argument(*flags, **kwargs)
        sub.set_defaults(handler=handler)

    pdf = categories.add_parser("pdf").add_subparsers(dest="command", required=True)
    add(pdf, "merge", _pdf_merge, IN_MANY, REQ_OUT)
    # ... 42 commands total across 5 categories ...
```

**Key design decisions:**
- **No CLI framework**: Hand-rolled `argparse` keeps the package dependency-light.
- **JSON output**: All commands return JSON strings (via `_result()` / `_error()` helpers) for easy parsing by agents.
- **Category routing**: Commands are grouped by domain (pdf, image, audio, video, office).

## Toolkits

Each toolkit is a class with static methods. The MCP server and CLI both delegate to the same toolkit methods, ensuring **behavioral consistency** across interfaces. AI and TTS toolkits are exposed via the MCP server only (no CLI commands).

| Toolkit | File | Toolkit Methods | MCP Tools | CLI Commands | Dependencies |
|---------|------|-----------------|-----------|--------------|--------------|
| `PDFToolkit` | `tools/pdf.py` | 25 | 23 | 18 | pypdf, pdfplumber, pypdfium2, liteparse (optional), pdf2docx, Ghostscript (optional), firecrawl (optional) |
| `ImageToolkit` | `tools/image.py` | 14 | 7 | 12 | Pillow, pillow-heif, pytesseract (optional), rembg (optional) |
| `AudioToolkit` | `tools/audio.py` | 7 | 6 | 5 | pydub, ffmpeg |
| `VideoToolkit` | `tools/video.py` | 17 | 7 | 5 | ffmpeg, moviepy, opencv-python-headless |
| `OfficeToolkit` | `tools/office.py` | 2 | 2 | 2 | markitdown, LibreOffice (external) |
| `AIToolkit` | `tools/ai.py` | — | 3 | 0 | anydoc, litellm/openai (LiteLLM proxy) |
| `TTSToolkit` | `tools/tts.py` | — | 1 | 0 | pydub (mp3 export), LiteLLM proxy (Kokoro) |

`PDFToolkit.ocr` and `PDFToolkit.crop` are implemented but not yet exposed via MCP or CLI.

## Shared Utilities (`utils.py`)

The `utils.py` module provides shared helpers used across all toolkits:

- **`setup_logging(level)`**: Configures the `media_tools` logger with timestamped output.
- **`validate_input(path, label)`**: Validates file paths — rejects empty paths, path traversal (`..`), non-existent files, and non-readable files. Allows URLs through.
- **`validate_output_dir(path, label)`**: Ensures the output directory is writable; creates it if missing.
- **`safe_basename(path)`**: Extracts the basename for safe filename handling.
- **`_subprocess_with_logging(cmd, description)`**: Runs subprocess commands with logging, returns `(result_string, success)`.
- **`_validate_crop_bounds(...)`**: Validates crop coordinates against image dimensions.

## Cross-Toolkit Dependencies

Some tools cross toolkit boundaries:

- **`PDFToolkit.images_to_pdf`** — delegates to `ImageToolkit` for image compression before PDF assembly.
- **`VideoToolkit.extract_audio`** — delegates to `AudioToolkit` (via pydub) for audio format conversion.
- **`VideoToolkit.slideshow` / `audio_to_video`** — use MoviePy to compose image→video and audio+video.
- **`VideoToolkit.extract_frames`** — uses OpenCV to pull frames from video.

These cross-references are internal to the package and do not affect the external API.

## Data Flow

```
Client (OpenWebUI / CLI)
    │
    ├─ MCP: HTTP POST to /mcp → server.py → @mcp.tool[tags] → ToolkitClass.method
    │                                    └─ mcp.enable(tags={tag}, only=True) for scoped servers
    │
    └─ CLI: argparse (category → command) → handler(ns) → ToolkitClass.method
                                    │
                                    └─ utils.py: validate_input, validate_output_dir, _subprocess_with_logging
```

## See Also

- [PDF Tools](/openwiki/tools/pdf.md) — all 23 PDF operations
- [Image Tools](/openwiki/tools/image.md) — all 12 image operations
- [Audio Tools](/openwiki/tools/audio.md) — all 6 audio operations
- [Video Tools](/openwiki/tools/video.md) — all 7 video operations
- [Office Tools](/openwiki/tools/office.md) — both Office operations
- [AI Document Tools](/openwiki/tools/ai.md) — summarize, QA, translate via LiteLLM
- [Text-to-Speech](/openwiki/tools/tts.md) — local Kokoro TTS via LiteLLM proxy
- [Operations & Deployment](/openwiki/operations/deployment.md) — server config, dev tooling, CI/CD
