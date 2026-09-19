---
type: Tool Reference
title: AI Document Tools
description: "3 AI-powered document tools exposed via the MCP server: document_summarize, document_qa, and document_translate. They read a document via anydoc and call an LLM through a local LiteLLM proxy (Gemma 4). No CLI commands."
resource: /src/media_tools/tools/ai.py
tags: [ai, tools, litellm, gemma, anydoc, openai]
openwiki:
  roles: [domain, integration]
  change_kinds: [public-api]
  source_paths: [/src/media_tools/tools/ai.py, /src/media_tools/server.py]
  symbols: [AIToolkit, document_summarize, document_qa, document_translate]
  test_paths: []
  invariants: [Reads document via anydoc.to_markdown, then calls LLM through LITELLM_URL; no CLI commands exist.]
  validation_commands: ["media-tools-server-ai"]
generated: { by: openwiki/local-ornith-35b, at: 2026-08-22T14:25:15.555Z }
---

## Overview

The `AIToolkit` class provides three AI-powered document operations exposed **only** through the MCP server (no CLI commands). Each reads a document to Markdown via `anydoc`, then asks an LLM (Gemma 4) to summarize, answer a question, or translate it. The LLM call goes through a local [LiteLLM](https://github.com/BerriAI/litellm) proxy, so no external API key or network egress is required.

## Tool List

| MCP Name | Description | Key Dependencies |
|----------|-------------|------------------|
| `document_summarize` | Summarize a document concisely; writes to `output` if provided | anydoc, LiteLLM |
| `document_qa` | Answer a question about a document's content | anydoc, LiteLLM |
| `document_translate` | Translate document content to `target_language` (default `en`) | anydoc, LiteLLM |

## Implementation Details

### Dependencies

**Required:**
- `anydoc` (via `firecrawl-anydoc`) — reads the document to Markdown (`anydoc.to_markdown`).
- `litellm` / `openai` — calls the LLM chat completions API through the proxy.

### Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `LITELLM_URL` | `http://localhost:4000` | LiteLLM proxy base URL |
| `LLM_MODEL` | `local-gemma4-e4b-vision` | Model name sent to the proxy |
| `LITELLM_API_KEY` | `sk-no-key-required` (code fallback, rejected with 401) | Bearer token. The proxy requires a real key: `export LITELLM_API_KEY=$(pass litellm/keys/jrodeiro-cli)` |

### Flow

```
input_path
    │
    ├─ validate_input(path)  (rejects traversal / missing / unreadable)
    │
    ├─ anydoc.to_markdown(path)  → document content
    │
    └─ OpenAI client.chat.completions (model=LLM_MODEL, base_url=LITELLM_URL)
            ├─ summarize / qa / translate prompt + document content
            │
            └─ write to `output` if provided, else return the string
```

### Key Implementation Notes

- **Local proxy only**: The model runs through a LiteLLM proxy (e.g., Ollama/Gemma 4 e2e). No external API key or network egress is required.
- **Error handling**: Each method returns the error string (e.g. `Error: Could not read document`) instead of raising.
- **No CLI**: These tools are registered only in `server.py` (tags `ai`); there are no CLI handlers in `cli.py`.
- **Reads first**: Document content is materialized via `anydoc` before the LLM call, so large documents are converted to Markdown in memory.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how AI tools are exposed via the `ai`-tagged server (`media-tools-server-ai`)
- [Text-to-Speech](/openwiki/tools/tts.md) — also uses the LiteLLM proxy
- [Operations & Deployment](/openwiki/operations/deployment.md) — dev tooling and server configuration
