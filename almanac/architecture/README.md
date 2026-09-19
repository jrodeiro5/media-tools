---
title: Architecture
topics: [architecture]
---

The architecture of media-tools is a dispatch-over-toolkits design: all tool
behavior lives in toolkit classes, and every entrypoint is a thin layer over
them.

The core is the toolkit classes under `src/media_tools/tools/`
([Toolkit pattern](../architecture/toolkit-pattern)). Each `<Name>Toolkit` is a
class of `@staticmethod` methods; a tool's behavior is defined exactly once
here. The two entrypoints — the CLI ([CLI dispatch](../architecture/cli-dispatch))
and the MCP server ([MCP server](../architecture/mcp-server)) — never implement
behavior. They translate a command into the same toolkit method, so they can
only diverge on transport (argparse vs. MCP), never on what a tool does. Adding
a tool means editing one class and wiring two thin entrypoints.

Every toolkit method calls the shared helpers in [Utilities](../architecture/utilities),
so changes there affect every tool in the repo.

Read in this order:

1. [Toolkit pattern](../architecture/toolkit-pattern) — the source of truth.
2. [CLI dispatch](../architecture/cli-dispatch) — one dispatch layer.
3. [MCP server](../architecture/mcp-server) — the other dispatch layer.
4. [Utilities](../architecture/utilities) — the shared base.
