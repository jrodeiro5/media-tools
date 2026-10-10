---
title: Toolkit pattern
topics: [toolkits, architecture]
sources:
  - id: tools-init
    type: file
    target: src/media_tools/tools/__init__.py
    title: "tools/__init__.py — toolkit exports"
  - id: pdf-py
    type: file
    target: src/media_tools/tools/pdf.py
    title: "PDFToolkit implementation"
  - id: image-py
    type: file
    target: src/media_tools/tools/image.py
    title: "ImageToolkit implementation"
  - id: audio-py
    type: file
    target: src/media_tools/tools/audio.py
    title: "AudioToolkit implementation"
  - id: video-py
    type: file
    target: src/media_tools/tools/video.py
    title: "VideoToolkit implementation"
  - id: office-py
    type: file
    target: src/media_tools/tools/office.py
    title: "OfficeToolkit implementation"
  - id: ai-py
    type: file
    target: src/media_tools/tools/ai.py
    title: "AIToolkit implementation"
  - id: tts-py
    type: file
    target: src/media_tools/tools/tts.py
    title: "TTSToolkit implementation"
  - id: pillow-override
    type: file
    target: pyproject.toml
    title: "pyproject.toml — override-dependencies forcing pillow>=12.3.0"
  - id: pii-py
    type: file
    target: src/media_tools/tools/pii.py
    title: "PiiToolkit implementation"
  - id: probe-py
    type: file
    target: src/media_tools/tools/probe.py
    title: "ProbeToolkit implementation"
  - id: vision-py
    type: file
    target: src/media_tools/tools/_vision.py
    title: "_vision.py — shared face detection, obscuring, and model cache"
---

# Toolkit pattern

All tool functionality lives in toolkit classes under `src/media_tools/tools/`.
Each toolkit is a class with `@staticmethod` methods that perform a specific
category of media processing.

The CLI ([CLI dispatch](../architecture/cli-dispatch)) and the MCP server
([MCP server](../architecture/mcp-server)) are both thin dispatch layers over
these classes rather than independent implementations: a tool's behavior is
defined once in a `<Name>Toolkit` class and exposed through both entrypoints.
Adding or changing a tool therefore means editing one class and wiring two thin
entrypoints — a CLI handler in `cli.py` and a `@mcp.tool` decorator in
`server.py`. The two entrypoints never diverge on what a tool does; they diverge
only on transport (argparse vs. MCP).

Each toolkit exports a `name` attribute (e.g. `"pdf"`) used for scoped server
tagging. The toolkit classes are exported from `tools/__init__.py` [@tools-init].
Toolkit methods call the shared helpers in [Utilities](../architecture/utilities).

## Toolkit classes

| class | file | lines | category |
|---|---|---|---|
| `PDFToolkit` | `pdf.py` | 1963 | PDF manipulation [@pdf-py] |
| `VideoToolkit` | `video.py` | 1263 | Video manipulation [@video-py] |
| `ImageToolkit` | `image.py` | 919 | Image manipulation [@image-py] |
| `AudioToolkit` | `audio.py` | 576 | Audio manipulation [@audio-py] |
| `ProbeToolkit` | `probe.py` | 442 | Sniff file, report metadata, rank applicable tools [@probe-py] |
| `OfficeToolkit` | `office.py` | 146 | Convert, inspect, edit, URL-to-Markdown [@office-py] |
| `AIToolkit` | `ai.py` | 139 | AI-powered document analysis [@ai-py] |
| `TTSToolkit` | `tts.py` | 114 | Text-to-speech [@tts-py] |
| `PiiToolkit` | `pii.py` | 101 | PII scan/redact (Presidio) [@pii-py] |

## Method signature convention

All toolkit methods follow the same pattern:

```python
@staticmethod
def some_operation(input_path: str, output: str, ...) -> str:
    err = validate_input(input_path)
    if err: return err
    err = validate_output_dir(output)
    if err: return err
    try:
        # ... actual work ...
        return f"Success: {output}"
    except Exception as exc:
        return f"Error: {exc}"
```

This uniform error handling means:

1. Invalid inputs return an error string (not raise exceptions).
2. Successful operations return a result string (not the processed data).
3. The CLI and MCP server both receive strings, keeping the transport layer
   simple.

## Dependencies

Each toolkit pulls in its own dependencies:

- **PDFToolkit**: `pypdf`, `pypdfium2`, `pdfplumber`, `liteparse` (optional),
  `reportlab` [@pdf-py]. `pdf2docx` (AGPL PyMuPDF) is optional — install it with
  `uv sync --extra docx`; see [pdf2docx to optional docx extra](../decisions/docx-optional-extra).
- **ImageToolkit**: `Pillow`, `pytesseract`, `rembg` [@image-py]
- **AudioToolkit**: `pydub` [@audio-py]
- **VideoToolkit**: `moviepy`, `opencv-python-headless` [@video-py]
- **OfficeToolkit**: `anydoc` (Markdown), OfficeCLI (`office_inspect`/`office_edit`),
  Firecrawl (`url_to_markdown`, cloud), LibreOffice (PDF→DOCX fallback) [@office-py]
- **AIToolkit**: `anydoc`, `litellm` (via HTTP) [@ai-py]
- **TTSToolkit**: `litellm` (via HTTP), `omlx` (local) [@tts-py]
- **PiiToolkit**: `pdfplumber` (PDF), `presidio` analyzers (optional) [@pii-py]
- **ProbeToolkit**: `subprocess`, `zipfile` (lazy `pypdf`/`PIL`) [@probe-py]

The server imports six toolkit classes at module level (PDF, Video,
Image, Audio, Office, PII), so those dependencies must be installed for any
invocation; the CLI imports those six plus `ProbeToolkit`. AI, TTS, and Probe
are lazy-imported inside the server's handler functions — `litellm`, `omlx`,
and Probe's backends load only when those tools are invoked. This is
intentional: it avoids loading heavy VLM and audio model dependencies when
only PDF or image tools are needed.

**Forced Pillow override (security ceiling).** `moviepy==2.2.1` hard-pins
`pillow<12.0`, while `rembg>=2.0.75` requires `pillow>=12.1.0` — mutually
exclusive for a from-scratch `uv sync`. The repo resolves this by forcing
`pillow>=12.3.0` in `override-dependencies` [@pillow-override], which pins the
lock to 12.3.0. This holds at runtime: moviepy still imports and runs despite
the metadata conflict, and 12.3.0 carries the security patches the older floor
lacks. Do not "fix" the override down to satisfy moviepy — that reintroduces
the patched CVEs; revisit only if moviepy ships a release that accepts
`pillow>=12`.

## Shared vision helper (`_vision.py`)

`image.py` and `video.py` both import `media_tools.tools._vision` lazily, inside
their handler functions, for face detection, face obscuring, and first-run model
caching. It is a private module (not exported from `tools/__init__.py`), so it
is not a toolkit and has no CLI handler or `@mcp.tool` registration.

Its invariant: **models are never vendored into git.** On first run each asset
downloads to `~/.cache/media-tools/models/<filename>`; every asset is SHA256
pinned and re-downloaded when the stored hash mismatches. With no cached file
and no network, `ensure_asset` raises `RuntimeError("Error: ...")`, which the
toolkit wrappers return directly — matching the toolkit error convention rather
than leaking an exception.

- `ensure_asset(key)` — downloads, pins, and caches an asset by key; raises
  `RuntimeError` on offline or hash mismatch.
- `detect_faces()` / `obscure_boxes()` — Haar cascade face boxes plus
  pixelate/Gaussian-blur (face redaction in the image tools).
- `iou()` / `track_boxes()` — greedy IoU matching of detections across video
  frames.

Licenses verified 2026-09-20: the Haar cascade is Intel BSD-style (redistribute
with notice), the FSRCNN model is Apache-2.0 — no copyleft, no NC [@vision-py].

## Adding a new toolkit

To add a new toolkit:

1. Create `src/media_tools/tools/<name>.py` with a class named
   `<Name>Toolkit`.
2. Add the class to `src/media_tools/tools/__init__.py`.
3. Add `@mcp.tool` decorators in `server.py` for each tool.
4. Add CLI handlers in `cli.py` (optional — the CLI is not required for
   new toolkits).
5. Update `pyproject.toml` with any new dependencies.

## Related pages

- [CLI dispatch](../architecture/cli-dispatch) — how `argparse` maps commands to
  toolkit methods.
- [MCP server](../architecture/mcp-server) — how the same methods are
  registered as MCP tools and scoped servers.
- [Refusals](../architecture/refusals) — the shared module that produces every
  toolkit refusal string and its stable error codes.
