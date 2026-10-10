---
title: CodeAlmanac Wiki
topics: [architecture]
sources: []
---

# CodeAlmanac Wiki

This is the living wiki for this repository. It records the durable knowledge
the code cannot say: decisions, flows, invariants, incidents, gotchas, and
project context that future agents should not rediscover from scratch.

## What the repo is

`media-tools` is an MCP server exposing 104 tools
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

- [Architecture](architecture) — the dispatch-over-toolkits design: CLI dispatch, the MCP server, the toolkit pattern, and shared utilities.
- [Decisions](decisions) — the AGPL docx-extra and local-TTS-Kokoro choices.
- [Incidents](incidents) — the keyv/Cacheable npm worm machine audit.
- [Refusals](architecture/refusals) — the shared refusal-ticket module and its
  stable error codes.

## Topic Taxonomy

Topics live in `topics.yaml`. Pages are Markdown files directly under
`almanac/`, including nested folders.

## Links

Use normal Markdown links between pages. Put file evidence in `sources:`.
