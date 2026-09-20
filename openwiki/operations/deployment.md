---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Operations
title: Operations & Deployment
description: "Server deployment and operational configuration for media-tools: the streamable-http transport, every environment variable and its default, the external binaries each tool requires (ffmpeg, soffice/LibreOffice, tesseract, Ghostscript, firecrawl), the optional LiteLLM proxy, dev tooling (ruff/bandit/mypy/vulture/semgrep/radon), and the GitHub Actions CI workflows."
resource: /pyproject.toml
tags: [deployment, operations, environment-variables, external-binaries, dev-tools, ci]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-19T19:14:37.934Z
sources:
  - id: openwiki-source-164e2da859b5277df81c7d94
    resource: repo://.github/workflows/ci.yml
  - id: openwiki-source-a50061a970a46c67dd3e3f21
    resource: repo://.semgrep.yaml
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-4c98e0114ea62b3994f0a92a
    resource: repo://src/media_tools/tools/ai.py
  - id: openwiki-source-a415c6a83eccf5df70162d43
    resource: repo://src/media_tools/tools/image.py
  - id: openwiki-source-a3224bb41cc4d6a3c172db92
    resource: repo://src/media_tools/tools/office.py
  - id: openwiki-source-f1f4e4d9d900b12b94ee3c47
    resource: repo://src/media_tools/tools/pdf.py
  - id: openwiki-source-30b3bd03b5a87d9d89e0da7b
    resource: repo://src/media_tools/tools/tts.py
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
---

## Server Deployment

### Running the MCP Server

```bash
# Full server (all 49 tools) on port 8020
media-tools-server

# Category-scoped server (only one toolset)
PORT=9090 media-tools-server-pdf   # only pdf tools
PORT=9090 media-tools-server-ai    # only AI document tools
PORT=9090 media-tools-server-tts   # only text-to-speech
```

**Configuration:**

| Env Var | Default | Description |
|---------|---------|-------------|
| `PORT` | `8020` | Server port (server.py:461, server.py:467) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR); applied via `setup_logging` at import time (server.py:18) |

**Transport:** `streamable-http` (required for browser-based clients like OpenWebUI). The `stdio` transport only works for local CLI agents.

**Endpoint:** `http://127.0.0.1:8020/mcp`

`main()` reads `PORT` (defaulting to `8020`) and calls `mcp.run(transport="streamable-http", port=port)` (server.py:460–462).

### Category-scoped servers

`pyproject.toml` defines nine console scripts: the CLI (`media-tools`), the full server (`media-tools-server`) exposing all 49 tools, and seven category-scoped servers. Each scoped server calls `mcp.enable(tags={tag}, only=True)` so only tools with that tag are served:

| Script | Tag |
|--------|-----|
| `media-tools-server-pdf` | `pdf` |
| `media-tools-server-image` | `image` |
| `media-tools-server-audio` | `audio` |
| `media-tools-server-video` | `video` |
| `media-tools-server-office` | `office` |
| `media-tools-server-ai` | `ai` |
| `media-tools-server-tts` | `tts` |

This lets an operator run a lean server exposing a single category instead of all 49 tools (server.py:465–496).

## Environment Variables

Every tunable for running the server and its tools. Defaults come from `os.environ.get(...)` in the source; unset optional values fall back to a local default rather than failing.

| Env Var | Default | Used By | Purpose |
|---------|---------|---------|---------|
| `PORT` | `8020` | `server.py:461`, `server.py:467` | HTTP port for the MCP server. |
| `LOG_LEVEL` | `INFO` | `server.py:18` | Root logger level (DEBUG/INFO/WARNING/ERROR). |
| `FIRECRAWL_API_KEY` | *(required)* | `pdf_to_markdown` (pdf.py:889) | API key for the Firecrawl CLI. Without it, `pdf_to_markdown` returns `Error: FIRECRAWL_API_KEY not set`. |
| `LITELLM_URL` | `http://localhost:4000` | AI tools (ai.py:19), TTS (tts.py:36) | Base URL of the LiteLLM proxy. |
| `LITELLM_API_KEY` | `sk-no-key-required` | AI tools (ai.py:43), TTS (tts.py:85) | Bearer token sent to the proxy; a placeholder is used when unset. |
| `LLM_MODEL` | `local-gemma4-e4b-vision` | AI tools (ai.py:24) | Model name for document summarize/QA/translate. |
| `TTS_MODEL` | `local-kokoro-tts` | TTS (tts.py:41) | Model name for text-to-speech. |

The AI tools (`document_summarize`, `document_qa`, `document_translate`) and the text-to-speech tool (`text_to_speech`) both talk to a **LiteLLM proxy** rather than a public API: AI tools hit `<LITELLM_URL>` with the `LLM_MODEL` and TTS hits `<LITELLM_URL>/v1/audio/speech` with `TTS_MODEL`. Both send `LITELLM_API_KEY` (defaulting to `sk-no-key-required`) as a Bearer token. No proxy means the AI/TTS tools fail at runtime.

## External Binary Requirements

Several tools shell out to system binaries. Each is optional and only required when the corresponding tool runs; the package installs the Python libraries but not the underlying executables.

| Binary | Tool(s) that require it | Evidence |
|--------|-------------------------|----------|
| `ffmpeg` | audio + video (convert, trim, compress, to-gif, extract-audio, …) | README requirements; `moviepy`/`opencv` in `pyproject.toml` |
| `soffice` (LibreOffice) | `office_to_pdf` | office.py:58 (`soffice --headless --convert-to pdf`) |
| `tesseract` | `image ocr` (via `pytesseract`) | image.py:501 (`pytesseract.image_to_string`) |
| `gs` (Ghostscript) | `pdf_to_a` | pdf.py:844 (`gs -dPDFA=…`) — fails with "Ghostscript (gs) not found" otherwise |
| `npx firecrawl` | `pdf_to_markdown` | pdf.py:894 (`npx firecrawl parse … -f markdown`) — requires `FIRECRAWL_API_KEY` |

When a binary is missing the tool returns an `Error: …` string (not a crash): e.g. Ghostscript reports *"Ghostscript (gs) not found"*, Firecrawl reports *"firecrawl CLI not found"*, and OCR reports *"pytesseract not installed"*.

## CLI Usage

```bash
# Help
media-tools --help

# PDF
media-tools pdf merge --input f1.pdf f2.pdf --output merged.pdf
media-tools pdf split --input doc.pdf --output out/ --pages "1-3,5,7-9"

# Image
media-tools image convert --input photo.jpg --output photo.png
media-tools image ocr --input scan.png

# Audio
media-tools audio convert --input song.mp3 --output song.wav

# Video
media-tools video convert --input clip.mp4 --output clip.webm

# Office
media-tools office to-markdown --input report.docx
media-tools office to-pdf --input report.docx --output report.pdf
```

**Output format**: The CLI returns JSON strings (via `_result`/`_error`) for easy parsing by agents, and exits non-zero with a JSON `{"error": …}` on exception (cli.py:24–32, cli.py:397–406). The server, by contrast, returns the raw tool strings.

## Development Tooling

### Configuration (`pyproject.toml`)

| Tool | Config | Purpose |
|------|--------|---------|
| `ruff` | `line-length = 120`, `target-version = "py311"`, select `E,F,W,I,B,UP` (ignore `B008`) | Linting, formatting |
| `bandit` | `skips = ["B101", "B104", "B404", "B602", "B603"]`, excludes `.venv` | Security analysis |
| `mypy` | `python_version = "3.11"`, `warn_return_any = true`, `disallow_untyped_defs = false` | Type checking |
| `vulture` | `min_confidence = 80`, `paths = ["src"]` | Dead code detection |
| `semgrep` | four custom rules (see below) | Security rules |
| `radon` | in `dependency-groups.dev`, not configured | Code complexity |

`radon` ships in the dev dependency group but has no `[tool.radon]` section in `pyproject.toml`; the other tools are configured inline.

### Pre-commit Hooks (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: ruff-pre-commit   # ruff (--fix) + ruff-format
  - repo: bandit            # bandit -c pyproject.toml
  - repo: local             # mypy --config-file pyproject.toml
  - repo: local             # semgrep --config=auto --error --quiet
  - repo: local             # gitleaks protect --staged
```

### Semgrep Rules (`.semgrep.yaml`)

Four custom rules:

1. **no-shell-subprocess**: Prevent `shell=True` in subprocess calls.
2. **no-print-debug**: Remove `print()` statements before committing.
3. **missing-input-validation**: Tools accepting file paths should validate input.
4. **missing-error-handling**: Consider try/except for file I/O operations.

## CI/CD: GitHub Actions

The repository runs six workflows under `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `ci.yml` | push to `main`, PRs | Lint job on a Python `3.11`/`3.13` matrix; runs `SKIP=gitleaks uvx pre-commit run --all-files` |
| `codeql.yml` | push, PRs, weekly cron | CodeQL analysis across `python` and `actions` languages |
| `gitleaks.yml` | push, PRs | Secrets scan of staged changes (`gitleaks protect`) |
| `dependency-review.yml` | PRs | Dependency review, `fail-on-severity: high` |
| `zizmor.yml` | push/PRs to `.github/**` | GitHub workflow security linting |
| `renovate-validate.yml` | push/PRs to `renovate.json` | Validates `renovate.json` |

CI installs the dev group with `uv sync --group dev` and runs the pre-commit suite (with `gitleaks` skipped there, as it has its own workflow needing the binary and staged changes). There is no OpenWiki update workflow in this repository.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — server/CLI entry points
- [PDF Tools](/openwiki/tools/pdf.md) — optional dependencies (liteparse, Ghostscript, firecrawl)
- [Image Tools](/openwiki/tools/image.md) — optional dependencies (pytesseract, rembg)
