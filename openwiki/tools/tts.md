---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Tool Reference
title: Text-to-Speech
description: "1 MCP tool (text_to_speech) that converts text to speech locally via a LiteLLM proxy running the Kokoro TTS model. No API key, no network egress. Supports wav (native) and mp3 (via pydub/ffmpeg). No CLI command."
resource: /src/media_tools/tools/tts.py
tags: [tts, tools, litellm, kokoro, pydub]
openwiki:
  roles: [domain, integration]
  change_kinds: [public-api]
  source_paths: [/src/media_tools/tools/tts.py, /src/media_tools/server.py]
  symbols: [TTSToolkit, text_to_speech]
  test_paths: []
  invariants: [Endpoint is built from LITELLM_URL env var, not from any tool argument; no API key or network egress required.]
  validation_commands: ["media-tools-server-tts"]
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
verified:
  - by: openwiki/0.5.2
    at: 2026-09-19T19:14:37.934Z
sources:
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-30b3bd03b5a87d9d89e0da7b
    resource: repo://src/media_tools/tools/tts.py
---

## Overview

The `TTSToolkit` class provides a single text-to-speech operation exposed **only** through the MCP server (no CLI command). It sends text to a local LiteLLM proxy running the [Kokoro](https://github.com/efrainlin/kokoro) TTS model, producing WAV (native, 24 kHz mono int16) or MP3 (converted via pydub/ffmpeg) audio. No API key and no network egress are required.

## Tool List

| MCP Name | Description | Key Dependencies |
|----------|-------------|------------------|
| `text_to_speech` | Convert text to speech; default voice chosen per `language`, or override with a Kokoro voice id | pydub (mp3 export), LiteLLM proxy (Kokoro) |

## Implementation Details

### Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `LITELLM_URL` | `http://localhost:4000` | LiteLLM proxy base URL (endpoint = `{base}/v1/audio/speech`) |
| `TTS_MODEL` | `local-kokoro-tts` | Model name sent to the proxy |
| `LITELLM_API_KEY` | `sk-no-key-required` (code fallback, rejected with 401) | Bearer token. The proxy requires a real key: `export LITELLM_API_KEY=$(pass litellm/keys/jrodeiro-cli)` |

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `text` | — | Text to convert (required, non-empty) |
| `output` | — | Output audio file path |
| `voice` | `""` | Kokoro voice id (e.g. `af_heart`, `ef_dora`). Empty picks the default for `language`. |
| `audio_format` | `wav` | `wav` (native) or `mp3` (converted via pydub/ffmpeg) |
| `language` | `en` | ISO code that selects the default voice and G2P |
| `timeout` | `300` | Seconds to wait for generation. A library parameter of `TTSToolkit.convert`; the MCP tool `text_to_speech` does not expose it, so the 300s default always applies when used over MCP. |

### Default voices by language

Kokoro voice ids encode language + gender (`a`=en-US, `b`=en-GB, `e`=es, `f`=fr, `h`=hi, `i`=it, `j`=ja, `p`=pt-BR, `z`=zh).

| language | default voice |
|----------|---------------|
| en | `af_heart` |
| es | `ef_dora` |
| fr | `ff_siwis` |
| it | `if_sara` |
| pt | `pf_dora` |
| ja | `jf_alpha` |
| zh | `zf_xiaobei` |
| hi | `hf_alpha` |

### Flow

```
text (non-empty)
    │
    ├─ validate_output_dir(output)
    │
    ├─ voice = voice or default for language
    │
    ├─ POST {LITELLM_URL}/v1/audio/speech {model, input, voice, response_format: wav, language}
    │
    ├─ if audio_format == mp3: pydub AudioSegment.from_wav(...).export(output, format="mp3")
    │   else: write WAV bytes to output
    │
    └─ return "Speech → {output} (FORMAT, Ns, voice=...)"
```

### Key Implementation Notes

- **Local proxy only**: Runs through a LiteLLM proxy (e.g., Ollama + Kokoro). No API key and no network egress.
- **Endpoint is not attacker-controlled**: The endpoint is built from the `LITELLM_URL` env var, never from a tool argument.
- **Duration**: Computed from WAV header (`len(audio) - 44` bytes / (24000 × 2)).
- **No CLI**: Registered only in `server.py` (tag `tts`); there is no CLI handler in `cli.py`.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how TTS is exposed via the `tts`-tagged server (`media-tools-server-tts`)
- [AI Document Tools](/openwiki/tools/ai.md) — also uses the LiteLLM proxy
- [Operations & Deployment](/openwiki/operations/deployment.md) — dev tooling and server configuration
