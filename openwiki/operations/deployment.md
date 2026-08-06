---
type: Operations
title: Operations & Deployment
description: "Server deployment, CLI usage, dev tooling (ruff, bandit, mypy, semgrep), pre-commit hooks, and GitHub Actions workflow for automated OpenWiki updates."
resource: /pyproject.toml
tags: [deployment, operations, dev-tools, CI-CD, pre-commit]
---

## Server Deployment

### Running the MCP Server

```bash
# Default: streamable-http on port 8020
media-tools-server

# Custom port
PORT=9020 media-tools-server
```

**Configuration:**

| Env Var | Default | Description |
|---------|---------|-------------|
| `PORT` | `8020` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

**Transport:** `streamable-http` (required for browser-based clients like OpenWebUI). The `stdio` transport only works for local CLI agents.

**Endpoint:** `http://127.0.0.1:8020/mcp`

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

**Output format**: All commands return JSON strings for easy parsing by agents.

## Development Tooling

### Configuration (`pyproject.toml`)

| Tool | Config | Purpose |
|------|--------|---------|
| `ruff` | `line-length = 120`, `target-version = "py311"` | Linting, formatting |
| `bandit` | `skip = ["B104", "B602", "B603"]` | Security analysis |
| `mypy` | `python_version = "3.11"` | Type checking |
| `vulture` | `min_confidence = 80` | Dead code detection |
| `semgrep` | `rules: no-shell-subprocess, no-print-debug, missing-input-validation, missing-error-handling` | Security rules |
| `radon` | (not configured) | Code complexity |

### Pre-commit Hooks (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: ruff-pre-commit  # lint + format
  - repo: bandit          # security analysis
  - repo: mypy            # type checking
  - repo: local           # semgrep (runs on all files)
```

### Semgrep Rules (`.semgrep.yaml`)

Four custom rules:
1. **no-shell-subprocess**: Prevent `shell=True` in subprocess calls.
2. **no-print-debug**: Remove `print()` statements before committing.
3. **missing-input-validation**: Tools accepting file paths should validate input.
4. **missing-error-handling**: Consider try/except for file I/O operations.

## CI/CD: GitHub Actions

**Workflow**: `.github/workflows/openwiki-update.yml`

**Schedule**: Daily at 8:00 AM UTC (`cron: "0 8 * * *"`) + manual trigger.

**Steps:**
1. Check out repository
2. Install OpenWiki globally (`npm install --global openwiki`)
3. Run `openwiki code --update --print`
4. Create pull request with documentation updates

**Environment:**
- `OPENWIKI_PROVIDER: openrouter`
- `OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}`
- `OPENWIKI_MODEL_ID: z-ai/glm-5.2`
- `LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}`

**PR Details:**
- Branch: `openwiki/update`
- Files added: `openwiki/`, `AGENTS.md`, `CLAUDE.md`, `.github/workflows/openwiki-update.yml`

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — server/CLI entry points
- [PDF Tools](/openwiki/tools/pdf.md) — optional dependencies (liteparse, Ghostscript, firecrawl)
- [Image Tools](/openwiki/tools/image.md) — optional dependencies (pytesseract, rembg)
