---
title: MCP server
topics: [server, architecture]
sources:
  - id: server-py
    type: file
    target: src/media_tools/server.py
    title: "media_tools/server.py — FastMCP server"
  - id: pyproject
    type: file
    target: pyproject.toml
    title: "pyproject.toml — entry point scripts"
---

# MCP server

The MCP server exposes 49 multimedia processing tools through FastMCP's
streamable-HTTP transport. It is the primary integration point for MCP
clients (OpenWebUI, Claude Desktop, agent frameworks).

## Server construction

`server.py` creates a single `FastMCP("Media Tools")` instance and registers
all tools as `@mcp.tool` decorators [@server-py]. The underlying logic lives in
the [Toolkit classes](../architecture/toolkit-pattern), which the server
imports at module level. The server is configured with a
description string that clients use to display available capabilities.

The server supports **scoped execution** through `_run_scoped(tag)`. When a
scoped server starts (e.g. `media-tools-server-pdf`), only tools tagged with
that category are exposed. This lets deployments run minimal servers that
expose only the tools they need.

## Tool registration

Each tool is registered with:

```python
@mcp.tool(name="pdf_merge", tags={"pdf"})
def pdf_merge(files: list[str], output: str) -> str:
    """Merge multiple PDF files into a single output file."""
    return PDFToolkit.merge(files, output)
```

The `name` parameter controls the tool name exposed to MCP clients. The
`tags` parameter enables scoped servers. The docstring becomes the tool's
description in the MCP protocol.

## Transport

The server uses FastMCP's `streamable-http` transport on port `8020` by
default. The port is configurable via the `PORT` environment variable.

## Constraints

- The server imports 5 of 7 `Toolkit` classes at module level (PDF, Video,
  Image, Audio, Office). AI and TTS are lazy-imported inside their handler
  functions to defer dependency loading. This means PDF/Image/Audio/Video/Office
  dependencies (pypdf, Pillow, pydub, etc.) must be installed for any server
  variant, while `litellm` and `omlx` are loaded only when those tools are
  invoked.
- The `mcp` package is pinned to `<2` in `pyproject.toml` because FastMCP
  does not yet support the MCP 2.0 spec. This pin will need review when
  FastMCP ships v2 support [@pyproject].
- The server exports `main()`, `main_pdf()`, `main_image()`, etc. as entry
  points. Each scoped variant calls `_run_scoped(tag)` with the appropriate
  tag [@server-py].
