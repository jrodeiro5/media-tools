---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
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
generated: { by: "openwiki/0.5.2", at: "2026-09-20T15:47:08.433Z" }
sources:
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-b635fea87ca1e53077f6aba1
    resource: repo://src/media_tools/tools/__init__.py
  - id: openwiki-source-4c98e0114ea62b3994f0a92a
    resource: repo://src/media_tools/tools/ai.py
verified:
  - by: openwiki/0.5.2
    at: 2026-09-20T15:47:08.433Z
---

## Overview

The `AIToolkit` class provides three AI-powered document operations exposed **only** through the MCP server (no CLI commands). Each reads a document to Markdown via `anydoc`, then asks an LLM (Gemma 4) to summarize, answer a question, or translate it. The LLM call goes through a local [LiteLLM](https://github.com/BerriAI/litellm) proxy, so no external API key or network egress is required.

The three tools share one two-stage flow — **read → ask** — and one error convention: every method returns a string and **never raises**, so failures surface as `"Error: …"` results rather than exceptions.

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
| `LITELLM_API_KEY` | `sk-no-key-required` (code fallback, rejected with 401) | Bearer token. The proxy requires a real key: `export LITELLM_API_KEY=$(pass <your-litellm-key>)` |

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

### The two-stage read → ask flow

Every tool funnels through the same steps (`ai.py`):

1. **Validate** — `validate_input(input_path)` rejects empty paths, `..` traversal, missing files, and unreadable files; `validate_output_dir(output)` creates/validates the output directory when an output path is given. A failed check returns its error string and aborts the tool.
2. **Read** — `anydoc.to_markdown(input_path)` materializes the document. Read failures return `Error: Could not read document: …` and abort the tool.
3. **Ask** — `_call_llm(prompt, document_content)` builds an `OpenAI` client pointed at `LITELLM_URL` (or its default) and calls `chat.completions.create(model=LLM_MODEL, …)` with a system message, a user prompt combining the task and the document content, and `max_tokens=4096`. The assistant's response is returned.

The per-tool prompts are:
- **summarize** — "Summarize the following document concisely. Focus on key points and main ideas."
- **qa** — "Answer the following question based on the document content. If the answer is not in the document, say so." plus the question.
- **translate** — "Translate the following document to `{target_language}`. Preserve formatting and structure."

### Output semantics

- **summarize / qa**: when `output` is provided, the result is written to the path and the tool returns `"Summary → {output}"` / `"Answer → {output}"`; otherwise the string is returned directly.
- **translate**: `output` is **required** (no default), so the translated text is always written and the tool returns `"Translated to {target_language} → {output}"`.

### Key Implementation Notes

- **Local proxy only**: The model runs through a LiteLLM proxy (e.g., Ollama/Gemma 4 e2e). No external API key or network egress is required; `LITELLM_API_KEY` falls back to `sk-no-key-required`, which the proxy rejects with `401`.
- **Error handling**: Each method returns the error string (e.g. `Error: Could not read document`) instead of raising.
- **No CLI**: These tools are registered only in `server.py` (tags `ai`); there are no CLI handlers in `cli.py`.
- **Reads first**: Document content is materialized via `anydoc` before the LLM call, so large documents are converted to Markdown in memory.

### Server registration (`server.py`)

The three tools are exposed as MCP tools tagged `ai`:

| MCP Tool | Handler | Delegates To |
|----------|---------|--------------|
| `document_summarize(input_path, output=None)` | `document_summarize` | `AIToolkit.summarize` |
| `document_qa(input_path, question, output=None)` | `document_qa` | `AIToolkit.qa` |
| `document_translate(input_path, output, target_language="en")` | `document_translate` | `AIToolkit.translate` |

Each handler is a thin `@mcp.tool(name=..., tags={"ai"})` wrapper that imports `AIToolkit` and forwards the call. The toolkit is re-exported from `media_tools.tools` (`__init__.py`), and the tools are served by the `ai`-tagged server entrypoint `main_ai` (`media-tools-server-ai`), which runs the MCP server scoped to the `ai` tag.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how AI tools are exposed via the `ai`-tagged server (`media-tools-server-ai`)
- [Office Tools](/openwiki/tools/office.md) — also converts documents to Markdown (via firecrawl-anydoc/anydoc)
- [Text-to-Speech](/openwiki/tools/tts.md) — also uses the LiteLLM proxy
- [Operations & Deployment](/openwiki/operations/deployment.md) — dev tooling and server configuration
