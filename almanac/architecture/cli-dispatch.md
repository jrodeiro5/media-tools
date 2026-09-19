---
title: CLI dispatch
topics: [cli, architecture]
sources:
  - id: cli-py
    type: file
    target: src/media_tools/cli.py
    title: "media_tools/cli.py — argparse-based CLI"
  - id: pyproject
    type: file
    target: pyproject.toml
    title: "pyproject.toml — entry point scripts"
---

# CLI dispatch

The CLI is a thin argparse layer that maps `media-tools <category> <command>`
invocations to `Toolkit` class methods (see [Toolkit pattern](../architecture/toolkit-pattern)).
It exists so agents can invoke tools from shell scripts, Makefiles, or other
agents without going through the MCP server (see [MCP server](../architecture/mcp-server)).

The CLI is not the source of truth for tool behavior — each `Toolkit` class is.
The CLI exists only to expose the same methods through `argparse`.

## Entry points

`pyproject.toml` declares nine console scripts [@pyproject]:

| script | purpose |
|---|---|
| `media-tools` | full CLI (all categories) |
| `media-tools-server` | full MCP server |
| `media-tools-server-pdf` | PDF-scoped MCP server |
| `media-tools-server-image` | image-scoped MCP server |
| `media-tools-server-audio` | audio-scoped MCP server |
| `media-tools-server-video` | video-scoped MCP server |
| `media-tools-server-office` | office-scoped MCP server |
| `media-tools-server-ai` | AI-scoped MCP server |
| `media-tools-server-tts` | TTS-scoped MCP server |

The scoped servers are the primary deployment surface for MCP clients. The full
CLI/server is useful for testing and ad-hoc work.

## Dispatch model

`build_parser()` constructs a single `ArgumentParser` with subparsers for each
toolkit category (`pdf`, `image`, `audio`, `video`, `office`) [@cli-py]. Each category
has its own set of subcommands.

Handlers are plain functions that take a `Namespace` and return a string:

```python
def _pdf_merge(ns): return PDFToolkit.merge(ns.input, ns.output)
```

Errors are caught in `main()` and emitted as `{"error": ...}` JSON. Successful
results are wrapped in `{"result": ...}` JSON. This uniform JSON output lets
any agent parse CLI output without understanding per-tool formats.

## Constraints

- The CLI and the MCP server share the same `Toolkit` classes. Adding a tool
  means adding it to the `Toolkit` class and wiring a handler in `cli.py`
  and/or a `@mcp.tool` decorator in `server.py` (see [MCP server](../architecture/mcp-server)).
- `argparse` is used directly (not `click` or `typer`). This is intentional:
  argparse has no third-party dependencies and works in minimal environments.
- The CLI does not validate file existence before calling the toolkit — that
  validation happens inside each `Toolkit` method via `validate_input()`.
- The CLI covers only PDF, Image, Audio, Video, and Office categories. AI and
  TTS tools are server-only (registered via `@mcp.tool` in `server.py` but
  not wired through `cli.py`).
