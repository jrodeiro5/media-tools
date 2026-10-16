---
title: Architecture
topics: [architecture]
---

The architecture of media-tools is a dispatch-over-toolkits design: all tool behavior lives in toolkit classes, and every entrypoint is a thin layer over them.

The core is the toolkit classes under `src/media_tools/tools/` ([Toolkit pattern](toolkit-pattern)). Each `<Name>Toolkit` is a class of `@staticmethod` methods; a tool's behavior is defined exactly once here. The two entrypoints — the CLI ([CLI dispatch](cli-dispatch)) and the MCP server ([MCP server](mcp-server)) — never implement behavior. They translate a command into the same toolkit method, so they can only diverge on transport (argparse vs. MCP), never on what a tool does. Adding a tool means editing one class and wiring two thin entrypoints.

Every toolkit method calls the shared helpers in [Utilities](utilities), so changes there affect every tool in the repo.

The refusal module ([Refusals](refusals)) centralizes every toolkit error string and stable error codes, keeping string contracts identical across tools. AI tools route through the local LiteLLM proxy and omlx stack ([Integrations](integrations)), so TTS and STT stay local without API keys.

Read in this order:

1. [Toolkit pattern](toolkit-pattern) — the source of truth.
2. [CLI dispatch](cli-dispatch) — one dispatch layer.
3. [MCP server](mcp-server) — the other dispatch layer.
4. [Utilities](utilities) — the shared base.
5. [Refusals](refusals) — shared error tickets and codes.
6. [Integrations](integrations) — LiteLLM/omlx AI routing.
