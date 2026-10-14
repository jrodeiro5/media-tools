---
title: AI integrations — the LiteLLM proxy and omlx stack
topics: [integrations, architecture]
sources:
  - id: tts-py
    type: file
    target: src/media_tools/tools/tts.py
    title: "TTSToolkit — local TTS via the LiteLLM proxy"
  - id: audio-stt
    type: file
    target: src/media_tools/tools/audio.py
    title: "AudioToolkit.transcribe — local STT via the LiteLLM proxy"
  - id: server-ai
    type: file
    target: src/media_tools/server.py
    title: "server.py — text_to_speech / audio_transcribe MCP tools"
---

# AI integrations — the LiteLLM proxy and omlx stack

Both text-to-speech and speech-to-text in media-tools route through a single
local proxy stack — a LiteLLM proxy on `:4000` in front of omlx on `:8010` — so
neither tool needs an API key or any network egress. Both directions read the
endpoint and the model name from environment variables, and audio model ids must
carry the Hugging Face org prefix exactly as omlx reports them on
`GET :8010/v1/models`.

## The proxy stack

Every audio-AI tool talks to the LiteLLM proxy at `http://localhost:4000`
(configurable via `LITELLM_URL`), which fronts omlx at `:8010`. omlx bundles
`mlx-audio`, exposing roughly 25 TTS families plus the whisper STT model as
OpenAI-compatible endpoints. The proxy handles model routing and the OpenAI
protocol translation; omlx serves the local MLX models. The whole loop stays on
the machine.

## Text-to-speech (Kokoro)

`text_to_speech` (server.py) maps to `TTSToolkit.convert`, which posts to
`{LITELLM_URL}/v1/audio/speech` with `model=TTS_MODEL` (default
`local-kokoro-tts`) [@tts-py]. Kokoro is non-autoregressive, so the
runaway-audio failure of autoregressive models cannot occur by construction
[@server-ai]. Voice selection defaults per language via `_DEFAULT_VOICES`; the runaway
analysis, model sizes, and the two omlx snapshot patches Kokoro needs live in
[Local TTS uses Kokoro](../decisions/local-tts-kokoro-not-chatterbox).

## Speech-to-text (whisper)

`audio_transcribe`, `audio_transcribe_chunks`, and `video_transcribe`
(server.py) call `AudioToolkit.transcribe`, which posts to
`{LITELLM_URL}/v1/audio/transcriptions` with `model=STT_MODEL` (default
`local-whisper-stt`) [@audio-stt]. The chunked variants split on silence and
reassemble ordered transcripts. The singular `transcribe` tool still listed in
`BACKLOG.md` is not implemented yet, but the backend is proven.

## Model-id convention

Model ids passed through omlx must carry the HF org prefix exactly as
`GET :8010/v1/models` reports them — e.g. `mlx-community--Kokoro-82M-bf16` and
`mlx-community--whisper-large-v3-turbo-4bit`. Bare names 404. Vision models
(Ornith, Gemma) resolve by short alias; audio models must carry the full
`mlx-community--` prefix.

## The Orca exception

Orca IDE's dictation uses a separate stack (sherpa-onnx, Parakeet) with a
hardcoded cloud URL and no base-URL override. It cannot be pointed at this proxy
and shares no bytes with the omlx/LiteLLM models.

## Related

- [Local TTS uses Kokoro](../decisions/local-tts-kokoro-not-chatterbox) — the
  TTS direction in depth.
- [Toolkit pattern](toolkit-pattern) — the AI/TTS toolkit
  dependencies and the server's lazy imports.
