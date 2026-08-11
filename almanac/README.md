---
title: CodeAlmanac Wiki
topics: [concepts]
sources: []
---

# CodeAlmanac Wiki

This is the living wiki for this repository. It records the durable knowledge
the code cannot say: decisions, flows, invariants, incidents, gotchas, and
project context that future agents should not rediscover from scratch.

## What the repo is

`media-tools` is an MCP server exposing 50+ multimedia processing tools
covering PDF, image, audio, video, Office documents, and AI-powered document
analysis. It runs locally via [FastMCP](https://github.com/paulpavad/fastmcp)
and can be dropped into any MCP-compatible client.

## Notability Bar

Write a page when it preserves non-obvious knowledge that will help a future
agent work safely in this codebase.

Good pages explain:

- a decision that took research or trial-and-error
- a cross-file flow
- an invariant or gotcha not visible from one file
- an external dependency as this repo uses it
- a product or operational constraint that shapes future work

Do not write pages that restate nearby code.

## Page inventory

### Architecture

- [CLI dispatch](architecture/cli-dispatch) — how `media-tools <category> <command>` maps to `Toolkit` methods
- [MCP server](architecture/mcp-server) — FastMCP registration, scoped servers, transport
- [Toolkit pattern](architecture/toolkit-pattern) — the 7 toolkit classes, method conventions, dependency map
- [Utilities](architecture/utilities) — shared validation, logging, subprocess helpers

### Decisions

- [Local TTS uses Kokoro, not Chatterbox](decisions/local-tts-kokoro-not-chatterbox) — why Kokoro was chosen, Chatterbox's autoregressive failure mode, omlx patches

### Incidents

- [keyv/Cacheable npm worm (Shai-Hulud)](incidents/keyv-npm-worm-audit) — machine audit procedure and findings

## Topic Taxonomy

Topics live in `topics.yaml`. Pages are Markdown files directly under
`almanac/`, including nested folders.

## Links

Use normal Markdown links between pages. Put file evidence in `sources:`.
