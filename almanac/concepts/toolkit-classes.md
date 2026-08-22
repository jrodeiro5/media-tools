---
title: Toolkit classes
topics: [concepts, architecture]
sources:
  - id: cli-py
    type: file
    target: src/media_tools/cli.py
    title: "media_tools/cli.py — argparse-based CLI"
  - id: server-py
    type: file
    target: src/media_tools/server.py
    title: "media_tools/server.py — FastMCP server"
  - id: tools-init
    type: file
    target: src/media_tools/tools/__init__.py
    title: "tools/__init__.py — toolkit exports"
  - id: pyproject
    type: file
    target: pyproject.toml
    title: "pyproject.toml — entry point scripts"
---

# Toolkit classes

All media functionality in `media-tools` lives in toolkit classes under
`src/media_tools/tools/`. The `media-tools` CLI and the FastMCP server are both
thin dispatch layers over those classes rather than independent
implementations, so a tool's behavior is defined once in a `<Name>Toolkit`
class and exposed through both entrypoints.

This is the mental model the rest of the wiki assumes. The CLI maps
`media-tools <category> <command>` to a toolkit method [@cli-py], and the
server registers the same methods as `@mcp.tool` tools [@server-py]. Both
entrypoints therefore share one implementation; nothing re-implements a tool
outside a toolkit class.

## Why the model matters

Because behavior lives in the toolkit classes, adding or changing a tool
means editing one class and wiring two thin entrypoints: a CLI handler in
`cli.py` and a `@mcp.tool` decorator in `server.py`. The CLI and server never
diverge on what a tool does — they diverge only on transport (argparse vs.
MCP).

## How the two dispatch layers relate

- The CLI builds one `ArgumentParser` with subparsers per toolkit category
  (`pdf`, `image`, `audio`, `video`, `office`) and maps each command to a
  toolkit method [@cli-py].
- The server registers the same methods as MCP tools, tagging each with its
  category [@server-py].
- Scoped servers (`media-tools-server-pdf`, etc.) expose only tools whose
  category tag matches, so a deployment can run a minimal server. AI and TTS
  tools are server-only and lazy-imported.

The toolkit classes are exported from `tools/__init__.py` and named in
`pyproject.toml` entry points [@tools-init][@pyproject].

## Related pages

- [Toolkit pattern](../architecture/toolkit-pattern) — the full class list,
  method-signature convention, and per-toolkit dependency map.
- [CLI dispatch](../architecture/cli-dispatch) — how `argparse` maps commands
  to toolkit methods.
- [MCP server](../architecture/mcp-server) — how the same methods are
  registered as MCP tools and scoped servers.
