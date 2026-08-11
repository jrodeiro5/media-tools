---
title: Local TTS uses Kokoro, not Chatterbox — autoregressive models run away
topics: [decisions, integrations, toolkits]
sources:
  - id: tts-py
    type: file
    target: src/media_tools/tools/tts.py
    title: "TTSToolkit — local TTS via LiteLLM"
  - id: server-py
    type: file
    target: src/media_tools/server.py
    title: "text_to_speech MCP tool"
  - id: chatterbox-release
    type: web
    target: https://github.com/resemble-ai/chatterbox
    title: "resemble-ai/chatterbox — V3 release notes (reduced hallucination)"
  - id: kokoro-hf
    type: web
    target: https://huggingface.co/mlx-community/Kokoro-82M-bf16
    title: "mlx-community/Kokoro-82M-bf16"
---

# Local TTS uses Kokoro, not Chatterbox

Decided 2026-08-10.

## Context

`text_to_speech` originally called the Fish Audio cloud API. That path was
removed: this machine runs everything local and open-source, and
`fish-audio-sdk` was never even a declared dependency in `pyproject.toml`,
so the tool could not have worked as shipped. Nobody noticed, which is
itself evidence of how little the tool was exercised.

The replacement had to run through the machine's existing local stack:
LiteLLM proxy on `:4000` in front of omlx on `:8010`. omlx bundles
`mlx-audio`, which supports ~25 TTS families, so the choice was open.

The first attempt used Chatterbox. It produced correct English and
**silently emitted garbage in Spanish**.

## The failure Chatterbox has

Chatterbox is **autoregressive**: it generates audio tokens one at a time
and stops when it decides to. When it fails to decide, it keeps going until
the 40-second token cap and returns noise — with an HTTP 200.

Measured against `mlx-community/chatterbox-4bit`, 2026-08-10:

| input set | runaway rate |
|---|---|
| 4 English sentences | 0/4 |
| 8 Spanish sentences | 5/8 |
| same 8 Spanish, with `language: "es"` | 3/8 |

The failure is **deterministic per input string** — retrying the same text
burns ~11 s to fail identically. `language_id` and `lang` were also tried;
neither is the parameter name mlx-audio reads.

Upstream confirms this is structural, not a packaging bug. ResembleAI's V3
release notes describe the fix as *"optimized to reduce unwanted
continuation, repetition, and off-prompt speech, especially in cases where
earlier multilingual models were less stable"* — i.e. V3 makes it rarer,
not impossible. Third-party hosts cap the input instead (Replicate:
"max 300 characters per request") [@chatterbox-release].

A related dead end is worth recording: `YUGOROU/Chatterbox-Multilingual-MLX-4bit`
ships **no `conds.safetensors`**, so every default-voice request 500s. It is
only usable for voice cloning, which is explicitly not wanted here.

## Decision

Use **`mlx-community/Kokoro-82M-bf16`** [@kokoro-hf], exposed through LiteLLM as
`local-kokoro-tts`.

Kokoro is **non-autoregressive** (StyleTTS2 architecture: it predicts
per-phoneme durations, then vocodes). Output length is bounded by the input
phoneme sequence, so the runaway failure mode **cannot occur by
construction** — not "occurs less often".

Same 8 Spanish sentences that broke Chatterbox:

```
chatterbox-4bit   5/8 runaway    0.6–1.0 s warm
Kokoro-82M        0/8 runaway    0.1 s warm
```

Verified by round-tripping Kokoro's output back through
`local-whisper-stt` (whisper-large-v3-turbo-4bit):

```
in : Borramos los ficheros duplicados para ahorrar espacio.
out: Borramos los ficheros duplicados para ahorrar espacio.
```

Kokoro is also 372 MB against Chatterbox's 598 MB, and ships stock voices
per language — no cloning, which was a hard requirement.

## Consequences

- `TTSToolkit.convert` has **no runaway guard**. The previous version
  measured the returned WAV against a chars-per-second bound and rejected
  overlong output. That check exists only because Chatterbox could produce
  overlong output; with Kokoro it is dead code. Do not reintroduce it
  without first reintroducing an autoregressive model.
- `voice` defaults to `""`, and the toolkit picks a stock voice from
  `_DEFAULT_VOICES[language]`. Voice ids encode language and gender by
  first letter: `a`=en-US, `b`=en-GB, `e`=es, `f`=fr, `h`=hi, `i`=it,
  `j`=ja, `p`=pt-BR, `z`=zh. Full list in `VOICES.md` inside the model
  snapshot.
- Spanish and English are solid. Other languages have thin training data —
  French has exactly one voice. Treat anything outside en/es as untested.
- Deleted from the HF cache the same day, all consumer-free:
  `chatterbox-4bit` (598 MB), `YUGOROU--Chatterbox-Multilingual-MLX-4bit`
  (966 MB), a partial `chatterbox-multilingual-v3` download (279 MB), and
  `Systran/faster-whisper-large-v3` (2.9 GB, CTranslate2 format, whose only
  caller was a dead experiment outside this repo). `fish-audio-sdk` was
  uninstalled from the venv.

## Gotcha: omlx does not discover Kokoro out of the box

Two patches to the HF snapshot are required, and **both are lost if the
repo is re-downloaded**:

```
config.json        add  "model_type": "kokoro"
model.safetensors  symlink -> kokoro-v1_0.safetensors
```

Why: omlx's `detect_model_type()` classifies by `model_type`, and Kokoro's
`config.json` has no such key (it is a raw StyleTTS2 config —
`dim_in`, `istftnet`, `plbert`, …). Separately,
`_is_hf_cache_mlx_compatible()` requires a file matching
`model*.safetensors`, and Kokoro's weights are named `kokoro-v1_0.safetensors`.
Either check failing means the model never appears in `GET :8010/v1/models`,
with no error logged at default verbosity.

omlx already special-cases Parakeet exports that omit `model_type`
(`model_discovery.py`), so the upstream fix is the same treatment for
Kokoro. Worth an issue.

Note `config.json` is normally a symlink into `blobs/`; patching it means
replacing the symlink with a real file, which breaks that blob's hash
association. Harmless, but `hf download --force-download` will undo it.

## Gotcha: load order can break Kokoro with a torch error

Symptom — Kokoro 500s at engine start with:

```
module 'torch.cuda' has no attribute 'device_count'
```

This is **load-order dependent** and looks like a broken model. It is not.
omlx ships no real torch; it installs a stub (`omlx/_torch_stub.py`) into
`sys.modules` when certain engines load. Kokoro's G2P goes
misaki → spaCy → thinc, and `thinc/compat.py` runs
`torch.cuda.device_count()` unconditionally as soon as `import torch`
succeeds. The stub defines `torch.cuda.is_available` but not
`device_count`.

So: load Kokoro into a fresh server and it works. Load the VLM engine first
(e.g. any Ornith request), and every subsequent Kokoro request 500s until
restart. That is why this can appear to "break spontaneously".

Fix applied on this machine — one line in the brew-managed stub, next to
`cuda.is_available = _false`:

```python
cuda.device_count = lambda: 0
```

**This is lost on `brew upgrade omlx`.** If Kokoro starts 500ing with that
message after an upgrade, reapply it. The durable fix belongs upstream in
omlx, alongside the Kokoro discovery gap above.

## Related

- Model ids through omlx must carry the HF org prefix exactly as
  `GET :8010/v1/models` reports them (`mlx-community--Kokoro-82M-bf16`).
  Bare names 404. Ornith and Gemma have short aliases; audio models do not.
- STT is the sibling category and is settled: `local-whisper-stt` →
  `mlx-community--whisper-large-v3-turbo-4bit` (447 MB). The `transcribe`
  tool in [BACKLOG.md](../../BACKLOG.md) can now be implemented against it;
  the backend is proven.
- Orca IDE's dictation is a separate stack (sherpa-onnx ONNX, Parakeet) with
  a hardcoded cloud URL and no base-URL override. It cannot be pointed at
  this proxy and shares no bytes with these models.
- The `text_to_speech` MCP tool in `server.py` wires `TTSToolkit.convert`
  through the LiteLLM proxy, reading model and endpoint from environment
  variables (`TTS_MODEL`, `LITELLM_URL`) [@server-py].
- `TTSToolkit.convert` exposes the Kokoro model via the LiteLLM proxy
  [@tts-py].
