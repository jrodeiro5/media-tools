---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Operations
title: Operations & Deployment
description: "How to run media-tools in production: the streamable-http server on HOST/PORT (with HOST, PORT, LOG_LEVEL, MEDIA_TOOLS_SEARCH and every LiteLLM/Firecrawl variable and default), the optional external binaries per tool (ffmpeg, soffice, tesseract, gs, firecrawl, officecli) and how missing binaries fail, the positional-argument CLI and its JSON contract, dev tooling (ruff/bandit/mypy/vulture/semgrep/radon) with pre-commit hooks, and all seven GitHub Actions workflows including the tag-driven publish workflow."
resource: /pyproject.toml
tags: [deployment, operations, environment-variables, external-binaries, dev-tools, ci]
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
verified:
  - by: openwiki/0.6.1
    at: 2026-10-01T23:14:01.781Z
---

## Server Deployment

### Running the MCP server

```bash
# Full server (all 104 tagged tools) on 127.0.0.1:8020
media-tools-server

# Category-scoped server (one toolset only)
PORT=9090 media-tools-server-pdf   # only pdf-tagged tools
PORT=9090 media-tools-server-ai    # only AI document tools
PORT=9090 media-tools-server-tts   # only text-to-speech

# Full server, but expose search_tools + call_tool instead of a huge tools/list
MEDIA_TOOLS_SEARCH=1 media-tools-server
```

**Transport:** `streamable-http` — required for browser-based clients such as OpenWebUI; the `stdio` transport is intentionally not used because it only serves local CLI agents.

**Endpoint:** `http://127.0.0.1:8020/mcp` (FastMCP's default `/mcp` route on the bound host/port).

`main()` reads `MEDIA_TOOLS_SEARCH`, `PORT` and `HOST` and calls `mcp.run(transport="streamable-http", host=host, port=port)` (server.py:950–959). `LOG_LEVEL` is applied once at import time via `setup_logging(...)` (server.py:19, utils.py:15–25), so it must be set before the process starts.

**Configuration (server process):**

| Env Var | Default | Description |
|---------|---------|-------------|
| `HOST` | `127.0.0.1` | Bind address. Loopback by default; set `0.0.0.0` to accept remote clients (the Docker image does). |
| `PORT` | `8020` | HTTP port; parsed with `int(...)` (server.py:957, server.py:964). |
| `LOG_LEVEL` | `INFO` | Logger level (DEBUG/INFO/WARNING/ERROR) for the `media_tools` logger. |
| `MEDIA_TOOLS_SEARCH` | *(unset)* | When `1`, adds FastMCP's `BM25SearchTransform(max_results=5)` so clients get `search_tools` + `call_tool` instead of listing every tool (server.py:951–956). |

### Category-scoped servers

`pyproject.toml` defines nine console scripts: the CLI (`media-tools`), the full server (`media-tools-server`), and seven category-scoped servers (pyproject.toml:56–65). Every scoped entrypoint calls `_run_scoped(tag)`, which does `mcp.enable(tags={tag}, only=True)` before the same `streamable-http` run (server.py:962–966) — so only tools carrying that tag are served:

| Script | Tag | Tools served |
|--------|-----|--------------|
| `media-tools-server-pdf` | `pdf` | 31 (the 30 pdf tools plus `media_probe`, which carries the `pdf` tag) |
| `media-tools-server-image` | `image` | 24 |
| `media-tools-server-audio` | `audio` | 13 |
| `media-tools-server-video` | `video` | 24 |
| `media-tools-server-office` | `office` | 5 |
| `media-tools-server-ai` | `ai` | 3 |
| `media-tools-server-tts` | `tts` | 1 |

The `pii` and `batch` tags have MCP tools but no scoped console script — `server.py` also defines `main_batch()` (server.py:997–998), yet `pyproject.toml` never registers it, so batch and PII tools are only reachable through the full server (or `MEDIA_TOOLS_SEARCH=1`).

### Docker

The repository `Dockerfile` is the reference production image: it installs `ffmpeg`, `tesseract-ocr`, `ghostscript`, `libreoffice` and fonts via apt (Dockerfile:10–16), sets `HOST=0.0.0.0` and `PORT=8020` (Dockerfile:3–6), syncs runtime dependencies only (`uv sync --frozen --no-dev --no-editable`), runs as a non-root `appuser`, `EXPOSE 8020`, and launches `media-tools-server` (Dockerfile:27–29). Because it bakes in the system binaries, container deployments do not need the per-tool installs listed below — but they still need a LiteLLM proxy for the AI/TTS/STT tools and `FIRECRAWL_API_KEY` for `url_to_markdown`.

## Environment Variables

Every tunable for running the server and its tools. Python reads these with `os.environ.get(...)`; unset optional values fall back to a local default rather than failing.

| Env Var | Default | Read at | Purpose |
|---------|---------|---------|---------|
| `HOST` | `127.0.0.1` | server.py:958, server.py:965 | Bind address for the MCP server. |
| `PORT` | `8020` | server.py:957, server.py:964 | HTTP port for the MCP server. |
| `LOG_LEVEL` | `INFO` | server.py:19 | Root logger level applied at import via `setup_logging`. |
| `MEDIA_TOOLS_SEARCH` | *(unset; anything but `1` is a no-op)* | server.py:951 | `1` swaps the full `tools/list` for BM25 `search_tools` + `call_tool`. |
| `LITELLM_URL` | `http://localhost:4000` | ai.py:19, tts.py:36, audio.py:247 | Base URL of the LiteLLM proxy (AI tools, TTS `…/v1/audio/speech`, STT `…/v1/audio/transcriptions`). |
| `LITELLM_API_KEY` | `sk-no-key-required` | ai.py:43, tts.py:85, audio.py:287 | Bearer token sent to the proxy; a placeholder is used when unset (no public API key anywhere). |
| `LLM_MODEL` | `local-gemma4-e4b-vision` | ai.py:24 | Model for `document_summarize`, `document_qa`, `document_translate`. |
| `TTS_MODEL` | `local-kokoro-tts` | tts.py:41 | Model for `text_to_speech`. |
| `STT_MODEL` | `local-whisper-stt` | audio.py:252 | Model for `audio_transcribe`, `audio_transcribe_chunks` and `video_transcribe` (only used when no per-call `model` argument is given). |
| `FIRECRAWL_API_KEY` | *(required for `url_to_markdown`)* | by the Firecrawl CLI, not by Python (office.py:117) | Cloud credential for `url_to_markdown`. No source file reads it directly — the key must be present in the process environment when the `firecrawl scrape` subprocess runs. |

The AI tools and `text_to_speech`/`audio_transcribe` all talk to a **LiteLLM proxy** rather than a public API: AI tools call it through the `openai` client with `LLM_MODEL` (ai.py:41–53), TTS posts to `<LITELLM_URL>/v1/audio/speech` with `TTS_MODEL` (tts.py:35–41), and STT posts multipart to `<LITELLM_URL>/v1/audio/transcriptions` (audio.py:246–248). All three send `LITELLM_API_KEY` as a Bearer token. With no proxy reachable, these tools fail at runtime with `Error: LLM call failed: …` / `Error: …` strings.

`url_to_markdown` is the one tool in the repository that deliberately leaves the machine: it sends the target URL to Firecrawl's cloud (office.py:115–128). Every other tool keeps local files local.

## External Binary Requirements

Several tools shell out to system binaries. Each is optional and only needed when the corresponding tool runs; `uv sync` installs the Python packages but not the executables.

| Binary | Tool(s) that require it | Evidence |
|--------|-------------------------|----------|
| `ffmpeg` / `ffprobe` | all video operations; audio operations via `pydub` (which wraps ffmpeg); `video_probe`, `media_probe` stream detail | video.py:26 (`ffmpeg -y -i …`), audio.py:32 (`pydub.AudioSegment.from_file`), probe.py:286–289 (`ffprobe`, skipped with a warning when absent) |
| `soffice` (LibreOffice) | `office_to_pdf`, `html_to_pdf`, and `pdf_to_docx` when the `docx` extra is not installed | office.py:62–70 (`soffice --headless --convert-to pdf`), pdf.py:1677, pdf.py:1716–1719 |
| `tesseract` (+ the `pytesseract` package) | `image_ocr` and the OCR branches of the PDF text extractors | image.py:579–587, pdf.py:368–370 |
| `gs` (Ghostscript) | `pdf_to_a` | pdf.py:1357–1377 (`gs -dPDFA=…`) |
| `firecrawl` CLI | `url_to_markdown` (cloud; needs `FIRECRAWL_API_KEY`) | office.py:124 (`firecrawl scrape … --format markdown`) |
| `officecli` | `office_inspect`, `office_edit` | office.py:91, office.py:108; install hint at office.py:138–140 |

### How a missing binary fails

Failure handling is **not** uniform — know which path a tool takes before assuming you will get a string back:

- **Ticketed refusal:** `pdf_to_a` catches `FileNotFoundError` itself and returns `missing_binary("Error: Ghostscript (gs) not found. Install with: brew install ghostscript", binary="gs")` — an `E_MISSING_BINARY` ticket whose `remedy` is `install_binary:gs` (pdf.py:1374–1377, refusals.py:85–103).
- **`Error: …` strings:** OCR returns `Error: pytesseract not installed. Run: pip install pytesseract` on `ImportError` and a generic `Error: …` when the `tesseract` binary is missing (image.py:586–590); `_run_cli`-based calls (`officecli`, `firecrawl`) return `Error: {cmd} not found` on `FileNotFoundError` (office.py:134–140); audio methods wrap `pydub` and return `Error: …` (audio.py:35–37).
- **Escaping exceptions:** `_subprocess_with_logging` — used for `soffice` and every `ffmpeg` invocation — does **not** catch `FileNotFoundError` (utils.py:136–145). A missing `soffice`/`ffmpeg` therefore escapes the toolkit method: the CLI's `main` catches it and prints `{"error": …}` with exit code 1 (cli.py:910–919), while over MCP the exception surfaces as a tool error rather than a string. When the binary exists but exits non-zero, the helper returns `Error: <stderr>`.

## CLI Usage

The CLI takes **positional** inputs (specs `IN_ONE`/`IN_MANY`) with `--output` required (`REQ_OUT`) or optional (`OPT_OUT`) — there is no `--input` flag (cli.py:419–422):

```bash
# Help
media-tools --help
media-tools pdf --help

# PDF
media-tools pdf merge a.pdf b.pdf --output merged.pdf
media-tools pdf split doc.pdf --output out/ --pages "1-3,5,7-9"
media-tools pdf compress merged.pdf --output small.pdf
media-tools pdf extract-text doc.pdf                 # --output optional
media-tools pdf reorder doc.pdf --output out.pdf --pages 1,3,2   # comma-separated page numbers

# Image
media-tools image convert photo.jpg --output photo.png
media-tools image ocr scan.png                       # no --output

# Audio / video
media-tools audio convert song.mp3 --output song.wav
media-tools video convert clip.mp4 --output clip.webm

# Office / PII / probe
media-tools office to-markdown report.docx
media-tools office to-pdf report.docx --output report.pdf
media-tools pii scan report.pdf
media-tools probe any-file.bin
```

CLI categories: `pdf`, `image`, `audio`, `video`, `office`, `pii`, `batch`, `returns`, `probe` (cli.py:424–905). Note the argument-shape split inside a category: `pdf split` takes a range *string* (`--pages "1-3,5,7-9"`), while `reorder`/`delete` parse `--pages` into a list of integers (cli.py:398–399).

**Output contract:** the CLI prints JSON — `_result` re-serializes the toolkit string (JSON if it already parses, else `{"result": …}`) and `_error` emits `{"error": …}` (cli.py:28–36); `main` prints the result and returns 0, or prints the error and returns 1 on any exception (cli.py:910–919). The MCP server, by contrast, returns the raw tool strings. The CLI does not cover everything the server exposes: the AI tools, `text_to_speech`, `pdf_redact`, `pdf_info`, `pdf_to_docx`, `image_remove_background`, and a few extraction tools are server-only.

## Development Tooling

### Configuration (`pyproject.toml`)

Dev dependencies live in `[dependency-groups].dev` — `bandit`, `ruff`, `vulture`, `semgrep`, `radon`, `mypy`, `complexipy`, `pyrefly`, `hexora` (pyproject.toml:43–54) — installed with `uv sync --group dev`. Inline tool configuration:

| Tool | Config | Purpose |
|------|--------|---------|
| `ruff` | `line-length = 120`, `target-version = "py311"`, select `E,F,W,I,B,UP`, ignore `B008`, per-file `F401` for `__init__.py` (pyproject.toml:79–88) | Linting + formatting |
| `bandit` | `skips = ["B101", "B104", "B404", "B602", "B603"]`, excludes `.venv` (pyproject.toml:90–92) | Security analysis |
| `mypy` | `python_version = "3.11"`, `warn_return_any = true`, `disallow_untyped_defs = false`, plus overrides ignoring missing imports for `presidio`, `pytesseract`, `cv2`, `openai`, … (pyproject.toml:94–102) | Type checking |
| `vulture` | `min_confidence = 80`, `paths = ["src"]`, `exclude = [".venv"]` (pyproject.toml:104–107) | Dead code detection |
| `semgrep` | no `[tool.semgrep]`; rules live in `.semgrep.yaml` (four custom rules, below) | Security/custom rules |
| `radon` | in the dev group (pyproject.toml:49) but no `[tool.radon]` section | Code complexity (unconfigured) |

`[tool.uv]` sets `exclude-newer = "7 days"` and pins a `pillow` override (pyproject.toml:109–111), so dependency resolution is time-bounded.

### Pre-commit hooks (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit   # ruff --fix + ruff-format
  - repo: https://github.com/PyCQA/bandit                # bandit -c pyproject.toml
  - repo: local                                          # .venv/bin/mypy --config-file pyproject.toml
                                                         #   (require_serial: true — batches share .mypy_cache)
  - repo: local                                          # semgrep --config=auto --error --quiet (always_run)
  - repo: local                                          # gitleaks protect --staged --verbose
```

Note the split: the pre-commit semgrep hook runs with `--config=auto` (Semgrep's registry config) over the whole tree, while `.semgrep.yaml` holds the four project-specific rules (no-shell-subprocess, no-print-debug, missing-input-validation, missing-error-handling) for direct `semgrep --config .semgrep.yaml` runs. The mypy hook calls the interpreter inside `.venv`, so the dev group must be synced first.

### Semgrep rules (`.semgrep.yaml`)

Four custom rules (`.semgrep.yaml:1–34`):

1. **no-shell-subprocess** (ERROR): forbid `subprocess.run(..., shell=True)`.
2. **no-print-debug** (WARNING): flag `print(...)` before committing.
3. **missing-input-validation** (WARNING): functions taking a `str` path parameter should validate it.
4. **missing-error-handling** (INFO): consider try/except around `$LIB.open(...)` / `Path(...).$METHOD(...)`.

## CI/CD: GitHub Actions

The repository runs seven workflows under `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `ci.yml` | push to `main`, all PRs | Lint job on a Python `3.11`/`3.13` matrix: `uv sync --group dev` then `SKIP=gitleaks uvx pre-commit run --all-files`; per-ref concurrency with `cancel-in-progress` |
| `codeql.yml` | push to `main`, PRs, weekly cron (`17 4 * * 1`) | CodeQL analysis across `python` and `actions` languages |
| `gitleaks.yml` | push to `main`, PRs | Secret scan with `gitleaks/gitleaks-action` over full history (`fetch-depth: 0`) |
| `dependency-review.yml` | PRs | `actions/dependency-review-action` with `fail-on-severity: high` |
| `zizmor.yml` | push/PRs touching `.github/**` | `zizmor-action` — GitHub workflow security linting |
| `renovate-validate.yml` | push/PRs touching `renovate.json` | `npx --yes --package renovate -- renovate-config-validator renovate.json` |
| `publish.yml` | tags `v*`, manual `workflow_dispatch` | Two jobs: **pypi** (`uv build` + `uv publish --trusted-publishing always` via OIDC — no stored token) and **image** (buildx build/push to `ghcr.io/<owner>/<repo>` with semver + `latest` tags and GHA layer cache) |

CI skips gitleaks in the pre-commit run because gitleaks has its own workflow (it needs the binary and staged/history context). Every workflow pins third-party actions to commit SHAs with `persist-credentials: false` and runs with `permissions: contents: read` at the workflow level. There is no OpenWiki automation workflow in this repository.

## See Also

- [Server & CLI](../architecture/server-and-cli.md) — how the console scripts, `HOST`/`PORT`, and the CLI dispatcher are wired
- [Architecture Overview](../architecture/overview.md) — end-to-end request flow
- [Inputs, Outputs & Refusals](../concepts/inputs-and-output.md) — the `Error: …` string contract and ticketed refusals
- [PDF Tools](../tools/pdf.md) — optional backends (LiteParse, Ghostscript, LibreOffice, pdf2docx)
- [Image Tools](../tools/image.md) — optional dependencies (pytesseract, rembg)
- [AI Tools](../tools/ai.md) / [TTS Tools](../tools/tts.md) — LiteLLM proxy configuration
- [Assertion-Script Test Suite](../testing/assertion-scripts.md) — how CI's pre-commit suite layers with the `tests/check_*.py` scripts
