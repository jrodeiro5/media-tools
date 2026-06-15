# media-tools × OpenWebUI Integration — STAR Report

**Date:** 2026-06-06
**Scope:** Build TinyWow/ILovePDF-like assistant in OpenWebUI using LiteLLM (Gemini/Mistral) connected to media-tools MCP server (25 multimedia processing tools).

---

## S — Situation

Need conversational AI assistant that can process multimedia files (PDF, image, audio, video, Office) through natural language. Existing tools like TinyWow and ILovePDF exist but lack AI-native interfaces. Goal: combine OpenWebUI chat interface with 25 custom MCP tools for hands-free media manipulation.

macOS M4 Max. Existing LiteLLM proxy already running on :4000 with 15+ models. No Docker. Prefer minimal single-user setup.

---

## T — Task

1. Fix and verify media-tools MCP server (25 tools across 5 categories)
2. Configure server as standalone streamable-http on port 8020
3. Install OpenWebUI with minimal single-user config
4. Wire OpenWebUI → existing LiteLLM proxy → Gemini/Mistral
5. Connect media-tools MCP as external tool server in OpenWebUI
6. Document everything for future continuation

---

## A — Action

### 1. Fixed Lazy-MCP Proxy Conflicts

- Regenerated hierarchy at `~/.claude/lazy-mcp-hierarchy`
- Replaced `memory` with `agentmemory` in lazy-mcp config
- **Removed `media-tools` from OpenCode lazy-mcp config** — must run standalone for OpenWebUI browser access

### 2. Verified & Fixed media-tools Dependencies

| Package | Version | Fix Applied |
|---------|---------|-------------|
| pypdf | 6.13.0 | **BREAKING:** `page.rotate()` in-place mutation removed. Changed to `new_page = writer.add_page(page); new_page.rotate(angle)` |
| markitdown | 0.1.6 | Installed `[docx]` extra — `mammoth` needed for .docx→markdown |
| libreoffice | 26.2.4 | macOS binary is `soffice`, not `libreoffice`. Updated OfficeToolkit.to_pdf |
| ffmpeg | 8.1.1 | Already installed via brew |

**Full test suite: 24/24 PASSED**
- PDF: merge, split, compress, extract_text, extract_images, rotate, info ✅
- Image: convert, resize, compress, crop, info ✅
- Audio: convert, trim, fade, speed, info ✅
- Video: convert, trim, compress, to_gif, probe, extract_audio ✅
- Office: to_markdown, to_pdf ✅

### 3. Configured Standalone MCP Server

**Transport:** streamable-http (required for browser-based OpenWebUI, not stdio)
**Port:** 8020 via `PORT` env var
**Endpoint:** `http://127.0.0.1:8020/mcp`

```python
# server.py
mcp = Server("media-tools")
mcp.settings.transport = "streamable-http"
# PORT=8020 from environment
```

**Key decision:** streamable-http lets browser-based OpenWebUI talk to MCP. stdio only works for local CLI agents.

### 4. Installed OpenWebUI (Native, Not Docker)

**Why no Docker:** macOS SOTA is OrbStack, but for single-user minimal setup, pip install is faster and lighter.

```bash
mkdir -p ~/openwebui && cd ~/openwebui
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install open-webui  # v0.9.6
```

**Start command:**
```bash
cd ~/openwebui && source .venv/bin/activate && env \
  WEBUI_SECRET_KEY=$(cat ~/openwebui/.secret_key) \
  DATA_DIR=~/openwebui/data \
  ENABLE_SIGNUP=false \
  DEFAULT_USER_ROLE=admin \
  ENABLE_RAG=false \
  ENABLE_IMAGE_GENERATION=false \
  ENABLE_WEB_SEARCH=false \
  ENABLE_CODE_INTERPRETER=false \
  ENABLE_AUTOMATIONS=false \
  ENABLE_CHANNELS=false \
  OPENAI_API_BASE_URLS=http://localhost:4000/v1 \
  OPENAI_API_KEYS=sk-local-gemma \
  open-webui serve
```

**Admin account:** `admin@localhost.com` / `admin12345`

### 5. Wired LiteLLM Connection

Used existing global config at `~/.config/litellm/config.yaml` — 15 models already configured:
- Local: qwen3-coder, gemma-12b (vLLM/MLX)
- Google: gemini-flash, gemini-flash-lite, gemini-tts, nano-banana-2, nano-banana-pro, imagen-4
- Mistral: mistral-large
- DeepSeek: deepseek-chat, deepseek-r1
- Kimi: kimi
- Bedrock: bedrock-claude-sonnet, bedrock-claude-haiku, bedrock-nova-pro, bedrock-nova-lite

**API endpoint discovery:** OpenWebUI mounts OpenAI router at `/openai` (not `/api/openai`):
- `POST /openai/config/update` — configure external OpenAI endpoints
- `GET /openai/models` — fetch models from LiteLLM proxy

### 6. MCP Tool Server Connection

**Status:** NOT YET COMPLETE — OpenWebUI's MCP/tool server integration requires UI configuration or additional API exploration.

OpenWebUI 0.9.6 supports tool servers via `/api/v1/tools/load/url` but native MCP streamable-http support is still being verified.

---

## R — Result

| Component | Status | Details |
|-----------|--------|---------|
| media-tools server | ✅ Ready | Port 8020, streamable-http, 24/24 tools verified |
| LiteLLM proxy | ✅ Ready | Port 4000, 15 models, existing config |
| OpenWebUI | ✅ Ready | Port 8080, single-user, LiteLLM connected |
| Model visibility | ✅ Working | 16 models fetched from LiteLLM via `/openai/models` |
| Chat via models | ⚠️ Partial | Models in memory (`OPENAI_MODELS`) but DB list empty — UI may need manual model selection or DB sync |
| MCP tools in OpenWebUI | ❌ Pending | Requires UI configuration or additional API work |

---

## Gotchas

### 1. pypdf 6.x Breaking Change
`page.rotate()` no longer works in-place. Must use:
```python
new_page = writer.add_page(page)
new_page.rotate(angle)
```

### 2. macOS LibreOffice Binary Name
Command is `soffice`, not `libreoffice`. Docker/ Linux docs assume `libreoffice`.

### 3. markitdown Needs `[docx]` Extra
`pip install markitdown` is insufficient for .docx. Need `markitdown[docx]` which installs `mammoth`.

### 4. OpenWebUI API Paths Are NOT `/api/v1/...`
OpenAI router mounts at `/openai`, not `/api/openai`:
- ✅ `POST /openai/config/update`
- ❌ `POST /api/openai/config/update`
- ❌ `POST /api/v1/openai/config/update`

### 5. Token Expiry Is Aggressive
JWT tokens expire quickly. Scripting against OpenWebUI API requires inline token refresh per request.

### 6. External Models Don't Auto-Sync to DB
`/openai/models` fetches LiteLLM models into memory (`app.state.OPENAI_MODELS`), but `/api/v1/models/list` returns DB models only. Chat UI may show models correctly even if DB list is empty.

### 7. streamable-http vs stdio
MCP servers for browser-based UIs MUST use streamable-http or SSE. stdio only works for local CLI orchestration (like Claude Code native MCP).

### 8. HF Token for First OpenWebUI Startup
Without `HF_TOKEN`, OpenWebUI downloads embedding models very slowly on first start. Set `ENABLE_RAG=false` to skip this for minimal setup.

---

## TODO

- [ ] **Connect MCP tools to OpenWebUI** — configure media-tools as external tool server in UI or via API
- [ ] **Verify end-to-end chat with tool calling** — test "convert this PDF to images" flow
- [ ] **Add model DB entries** — manually create workspace models in OpenWebUI so they appear in `/api/v1/models/list`
- [ ] **Test tool permissions** — ensure MCP tools respect OpenWebUI's tool enable/disable toggles
- [ ] **Add direct PDF/image upload handling** — OpenWebUI file upload → media-tools processing pipeline
- [ ] **Create systemd/launchd service** for media-tools server auto-start
- [ ] **Create startup script** — single command to start media-tools + OpenWebUI + LiteLLM

---

## File Locations

| File | Purpose |
|------|---------|
| `~/.config/litellm/config.yaml` | Global LiteLLM proxy config (15 models) |
| `~/openwebui/.secret_key` | OpenWebUI JWT secret |
| `~/openwebui/openwebui.pid` | Running process ID |
| `~/openwebui/openwebui.log` | Server logs |
| `~/openwebui/data/webui.db` | SQLite database |
| `/Users/jrodeiro/dev/experiments/media-tools/src/media_tools/server.py` | MCP server (port 8020) |
| `/Users/jrodeiro/dev/experiments/media-tools/src/media_tools/tools/` | 25 tool implementations |
| `/Users/jrodeiro/.claude/lazy-mcp-config.json` | OpenCode MCP proxy config |
| `/tmp/media-tools.pid` | media-tools server PID |
| `/tmp/media-tools.log` | media-tools server logs |

---

## Quick Start (Next Session)

```bash
# Terminal 1: media-tools MCP server
cd /Users/jrodeiro/dev/experiments/media-tools
source .venv/bin/activate
PORT=8020 python -m media_tools.server

# Terminal 2: OpenWebUI
cd ~/openwebui && source .venv/bin/activate && env \
  WEBUI_SECRET_KEY=$(cat ~/openwebui/.secret_key) \
  DATA_DIR=~/openwebui/data \
  ENABLE_SIGNUP=false \
  ENABLE_RAG=false \
  OPENAI_API_BASE_URLS=http://localhost:4000/v1 \
  OPENAI_API_KEYS=sk-local-gemma \
  open-webui serve

# Terminal 3: LiteLLM (if not already running)
# litellm --config ~/.config/litellm/config.yaml

# Open: http://localhost:8080
# Login: admin@localhost.com / admin12345
```
