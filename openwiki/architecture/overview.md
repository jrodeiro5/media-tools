---
type: Architecture
title: Architecture Overview
description: "How media-tools is structured: FastMCP server, CLI dispatcher, five toolkit modules, shared utilities, and the relationship between MCP and CLI entry points."
resource: /src/media_tools/server.py
tags: [architecture, server, CLI, FastMCP, entry-points]
---

## High-Level Design

media-tools is a **dual-interface** Python package. The same underlying toolkits are exposed through both an MCP server (for AI agents) and a CLI (for scripts/operators).

```
src/media_tools/
├── server.py          # FastMCP server — 37+ MCP tool registrations
├── cli.py             # CLI dispatcher — 37 command handlers
├── utils.py           # Shared: logging, validation, subprocess helpers
└── tools/
    ├── __init__.py    # Re-exports all 5 Toolkits
    ├── pdf.py         # PDFToolkit (21 tools)
    ├── image.py       # ImageToolkit (12 tools)
    ├── audio.py       # AudioToolkit (5 tools)
    ├── video.py       # VideoToolkit (6 tools)
    └── office.py      # OfficeToolkit (2 tools)
```

## Entry Points

Two console scripts are defined in `pyproject.toml`:

| Script | Module | Purpose |
|--------|--------|---------|
| `media-tools` | `media_tools.cli:main` | CLI dispatcher (agent-native) |
| `media-tools-server` | `media_tools.server:main` | MCP server (streamable-http) |

### MCP Server (`server.py`)

The server is built on [FastMCP](https://github.com/structuredlabs/fastmcp). It creates a single `FastMCP` instance named "Media Tools" and registers each tool as a `@mcp.tool` decorator:

```python
mcp = FastMCP("Media Tools", instructions="...")

@mcp.tool(name="pdf_merge")
def pdf_merge(files: list[str], output: str) -> str:
    return PDFToolkit.merge(files, output)
```

**Key design decisions:**
- **Transport**: `streamable-http` (not `stdio`). This is required for browser-based clients like OpenWebUI. The `stdio` transport only works for local CLI agents.
- **Port**: Configurable via `PORT` env var (default 8020).
- **Tool registration**: Each `@mcp.tool` function is a thin wrapper that delegates to the corresponding `ToolkitClass.method()`.

### CLI (`cli.py`)

The CLI uses a manual argument parser (no framework dependency). It defines a `COMMANDS` dictionary mapping `(category, command_name)` tuples to handler functions:

```python
COMMANDS = {
    ("pdf", "merge"): _pdf_merge,
    ("pdf", "split"): _pdf_split,
    # ... 37 total commands ...
}

def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(HELP)
        return 0
    category = args[0].lower()
    command = args[1].lower() if len(args) > 1 else ""
    key = (category, command)
    if key not in COMMANDS:
        print(f"Unknown command: {category} {command}", file=sys.stderr)
        return 1
    cmd_args = args[2:] if len(args) > 2 else []
    result = COMMANDS[key](cmd_args)
    print(result)
    return 0
```

**Key design decisions:**
- **No CLI framework**: Hand-rolled argument parsing avoids dependencies and keeps the package lightweight.
- **JSON output**: All commands return JSON strings (via `_result()` / `_error()` helpers) for easy parsing by agents.
- **Category routing**: Commands are grouped by domain (pdf, image, audio, video, office).

## Toolkits

Each toolkit is a class with static methods. The MCP server and CLI both delegate to the same toolkit methods, ensuring **behavioral consistency** across interfaces.

| Toolkit | File | Tools | Dependencies |
|---------|------|-------|--------------|
| `PDFToolkit` | `tools/pdf.py` | 21 | pypdf, pdfplumber, pypdfium2, liteparse (optional), Ghostscript (optional) |
| `ImageToolkit` | `tools/image.py` | 12 | Pillow, pillow-heif, pytesseract (optional), rembg (optional) |
| `AudioToolkit` | `tools/audio.py` | 5 | pydub |
| `VideoToolkit` | `tools/video.py` | 6 | ffmpeg (external) |
| `OfficeToolkit` | `tools/office.py` | 2 | markitdown, LibreOffice (external) |

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

These cross-references are internal to the package and do not affect the external API.

## Data Flow

```
Client (OpenWebUI / CLI)
    │
    ├─ MCP: HTTP POST to /mcp → server.py → @mcp.tool → ToolkitClass.method
    │
    └─ CLI: argv parsing → COMMANDS dict → handler function → ToolkitClass.method
                                    │
                                    └─ utils.py: validate_input, validate_output_dir, _subprocess_with_logging
```

## See Also

- [PDF Tools](/openwiki/tools/pdf.md) — all 21 PDF operations
- [Image Tools](/openwiki/tools/image.md) — all 12 image operations
- [Audio Tools](/openwiki/tools/audio.md) — all 5 audio operations
- [Video Tools](/openwiki/tools/video.md) — all 6 video operations
- [Office Tools](/openwiki/tools/office.md) — both Office operations
- [Operations & Deployment](/openwiki/operations/deployment.md) — server config, dev tooling, CI/CD
