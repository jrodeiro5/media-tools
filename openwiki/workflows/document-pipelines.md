---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Concept
title: Document & Multimedia Pipelines
description: Cross-tool workflows that chain the document stack (PDF/image → anydoc or Firecrawl → LLM summarize/QA/translate), text-to-speech through the local LiteLLM proxy (Kokoro), and multimedia pipelines (video→GIF, image slideshow, frame extraction). Covers entry points, control flow, configuration, failure modes, and invariants.
tags: [document-pipeline, tts, multimedia, anydoc, firecrawl, litellm, kokoro, pdf, mcp, cli]
sources:
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-4c98e0114ea62b3994f0a92a
    resource: repo://src/media_tools/tools/ai.py
  - id: openwiki-source-a3224bb41cc4d6a3c172db92
    resource: repo://src/media_tools/tools/office.py
  - id: openwiki-source-f1f4e4d9d900b12b94ee3c47
    resource: repo://src/media_tools/tools/pdf.py
  - id: openwiki-source-30b3bd03b5a87d9d89e0da7b
    resource: repo://src/media_tools/tools/tts.py
  - id: openwiki-source-5d693fa860b270ba3e69348c
    resource: repo://src/media_tools/tools/video.py
  - id: openwiki-source-f7be093be4a966caaa381229
    resource: repo://src/media_tools/utils.py
  - id: openwiki-source-0f45531f40d627881b1ab052
    resource: repo://tests/check_redact.py
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
---

## Overview

This page describes the cross-tool workflows in the `media_tools` package that **chain several toolkits or external services end to end**. Three pipelines fall in scope:

1. **Document pipeline** — turn a document (PDF, DOCX, image, HTML, …) into Markdown with `anydoc` or the Firecrawl CLI, then feed that Markdown to an LLM for **summarize / QA / translate** (`AIToolkit`, via a local LiteLLM proxy).
2. **Text-to-speech pipeline** — send text to a local LiteLLM proxy running the **Kokoro** TTS model and export **wav / mp3** (`TTSToolkit`).
3. **Multimedia pipeline** — **video → GIF**, **image slideshow → video**, and **video → frame extraction** (`VideoToolkit`).

The toolkit classes (`PDFToolkit`, `OfficeToolkit`, `AIToolkit`, `TTSToolkit`, `VideoToolkit`) hold the logic; two presentation layers expose them:

- **MCP server** (`src/media_tools/server.py`) — the primary interface. AI and TTS tools are registered **only** here (no CLI commands). Multimedia helpers (`image_to_video`, `video_extract_frames`) are registered lazily via `from media_tools.tools.video import VideoToolkit` inside their handlers.
- **CLI** (`src/media_tools/cli.py`) — a category/subcommand front-end for PDF, image, audio, video, and office operations. AI (`document_summarize`/`document_qa`/`document_translate`) and TTS (`text_to_speech`) have **no CLI handlers**.

Every toolkit method shares one contract: call `validate_input` then `validate_output_dir` (see `src/media_tools/utils.py`), perform the work, and return a human-readable string — surfacing failures as `"Error: …"` and **never raising**.

---

## Document Pipeline (anydoc / Firecrawl → LLM)

The document pipeline has two separable halves: **materialize the document to Markdown**, then **ask an LLM** to summarize, answer a question, or translate.

- **`anydoc` (firecrawl-anydoc)** drives `OfficeToolkit.to_markdown` and `AIToolkit._read_document`. It reads ~14 Office/text formats in ~5 ms/doc and is used for local PDF/DOCX/HTML/XLSX.
- **Firecrawl CLI** (`npx firecrawl parse … -f markdown -k <key>`) drives `PDFToolkit.pdf_to_markdown`. It requires `FIRECRAWL_API_KEY` and hits the Firecrawl cloud (free tier: 500 requests/month), so it is the one step with real network egress.

`AIToolkit` funnels all three operations (`summarize`, `qa`, `translate`) through the same two-stage flow: read → ask. `translate` is the exception that requires `output` (it has no in-memory return path).

### Sequence — document pipeline

```mermaid
sequenceDiagram
    participant Client as MCP / CLI
    participant AI as AIToolkit
    participant Anydoc as anydoc (firecrawl-anydoc)
    participant Fire as Firecrawl CLI (pdf_to_markdown)
    participant LLM as LiteLLM proxy (Gemma 4)

    Client->>AI: summarize(input, output?)
    AI->>AI: validate_input(path); validate_output_dir(output)
    AI->>Anydoc: anydoc.to_markdown(path)
    Anydoc-->>AI: markdown text (or Error)
    alt read failed
        AI-->>Client: "Error: Could not read document: …"
    else
        AI->>LLM: chat.completions.create(model=LLM_MODEL, max_tokens=4096)
            Note over AI,LLM: system + user prompt (task + document content)<br/>base_url=LITELLM_URL, api_key=LITELLM_API_KEY
        LLM-->>AI: assistant message
        alt LLM call failed
            AI-->>Client: "Error: LLM call failed: …"
        else
            AI->>AI: write_text(summary, output) if output given
            AI-->>Client: "Summary → {output}" / "Answer → …" / "Translated to {lang} → …"
        end
    end
```

*The read → ask flow for `summarize` / `qa` / `translate`, with the Firecrawl CLI path used by `PDFToolkit.pdf_to_markdown`.*

### Configuration (environment variables)

| Variable | Default | Used By | Purpose |
|----------|---------|---------|---------|
| `LITELLM_URL` | `http://localhost:4000` | `AIToolkit`, `TTSToolkit` | Proxy base URL. AI uses it directly; TTS appends `/v1/audio/speech`. |
| `LLM_MODEL` | `local-gemma4-e4b-vision` | `AIToolkit` | Model name sent to the proxy for summarize/QA/translate. |
| `TTS_MODEL` | `local-kokoro-tts` | `TTSToolkit` | Model name sent to the proxy for TTS. |
| `LITELLM_API_KEY` | `sk-no-key-required` | `AIToolkit`, `TTSToolkit` | Bearer token. The proxy rejects this fallback with `401`; set a real key (`export LITELLM_API_KEY=$(pass <your-litellm-key>)`). |
| `FIRECRAWL_API_KEY` | *(none)* | `PDFToolkit.pdf_to_markdown` | Firecrawl API key; **required** or the method returns an error before any request. |

### Per-tool prompts

- **summarize** — "Summarize the following document concisely. Focus on key points and main ideas."
- **qa** — "Answer the following question based on the document content. If the answer is not in the document, say so." plus the question.
- **translate** — "Translate the following document to `{target_language}`. Preserve formatting and structure." (default `target_language="en"`).

### Output semantics

- **summarize / qa**: when `output` is provided, the result is written to the path and the tool returns `"Summary → {output}"` / `"Answer → {output}"`; otherwise the string is returned directly.
- **translate**: `output` is **required** (no default), so the translated text is always written and the tool returns `"Translated to {target_language} → {output}"`.

---

## Text-to-Speech Pipeline (LiteLLM proxy → Kokoro)

`TTSToolkit.convert` sends text to a local LiteLLM proxy running the **Kokoro** TTS model. It requires **no API key and no network egress** (the proxy runs locally, e.g. via `omlx`). The single MCP tool `text_to_speech` (tag `tts`) is the only entry point — there is no CLI command.

The proxy returns native **24 kHz mono int16** WAV. The method writes WAV bytes directly, or converts to **mp3** via `pydub`/ffmpeg.

### Sequence — TTS pipeline

```mermaid
sequenceDiagram
    participant Client as MCP text_to_speech
    participant TTS as TTSToolkit
    participant Proxy as LiteLLM proxy (Kokoro)
    participant Pydub as pydub / ffmpeg

    Client->>TTS: convert(text, output, voice, audio_format, language)
    TTS->>TTS: validate_output_dir(output); reject empty text
    TTS->>TTS: voice = voice or default for language (see table below)
    TTS->>Proxy: POST {LITELLM_URL}/v1/audio/speech {model, input, voice, response_format: wav, language}
        Note over TTS,Proxy: Authorization: Bearer {LITELLM_API_KEY}<br/>timeout = 300s
    Proxy-->>TTS: raw WAV bytes
    alt proxy unreachable / error
        TTS-->>Client: "Error: {exc}"
    else audio_format == mp3
        TTS->>Pydub: AudioSegment.from_wav(bytes).export(output, format="mp3")
        Pydub-->>TTS: mp3 file
        TTS-->>Client: "Speech → {output} (MP3, Ns, voice=…)"
    else wav
        TTS->>TTS: write WAV bytes to output
        TTS-->>Client: "Speech → {output} (WAV, Ns, voice=…)"
    end
```

*The TTS flow: build the `{LITELLM_URL}/v1/audio/speech` payload, call the proxy, and export wav (native) or mp3 (via pydub/ffmpeg).*

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

### Key implementation notes

- **Endpoint is not attacker-controlled**: the endpoint is built from the `LITELLM_URL` env var, never from a tool argument (`text`/`voice`/`language`).
- **Duration** is computed from the WAV header: `(len(audio) - 44) / (24000 × 2)` seconds.
- **Reliability**: reliable in `en`/`es`; other languages have thinner voice data.
- **No CLI**: registered only in `server.py` (tag `tts`).

---

## Multimedia Pipeline (video → GIF / slideshow / frames)

`VideoToolkit` handles the video/image/audio side. Three operations compose external tools into a pipeline:

| MCP Tool | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `video_to_gif` | `video to-gif` | Convert a video segment into an animated GIF. | ffmpeg (palettegen + paletteuse) |
| `image_to_video` | *(none)* | Create a video slideshow from images. | MoviePy (`ImageClip`, `concatenate_videoclips`) |
| `video_extract_frames` | *(none)* | Extract frames from video as images. | OpenCV (`cv2.VideoCapture`) |

### GIF pipeline (two-pass ffmpeg)

`to_gif` runs ffmpeg twice. The first pass renders the segment to a **palette PNG** (`palettegen`); the second pass re-reads the segment plus the palette and applies `paletteuse`. The palette temp file is unlinked afterward. Output width (default 480) and fps (default 10) are honored; `start`/`duration` select the segment.

### Slideshow (MoviePy)

`slideshow` builds one `ImageClip` per image (`duration_per_image`, default 5 s), concatenates them with `concatenate_videoclips(method="compose")`, and writes the file at `fps` (default 30).

### Frame extraction (OpenCV)

`extract_frames` opens the video with `cv2.VideoCapture`, computes `skip_frames = max(1, int(actual_fps / fps))`, optionally seeks to `start` and stops at `start + duration`, and writes `frame_{n:06d}.png` for every kept frame.

### Sequence — multimedia pipeline

```mermaid
sequenceDiagram
    participant Client as MCP / CLI
    participant Video as VideoToolkit
    participant Ffmpeg as ffmpeg (process)
    participant MoviePy as MoviePy
    participant Opencv as OpenCV

    Client->>Video: to_gif(input, output, width, fps, start, duration)
    Video->>Video: validate_input(path); validate_output_dir(output)
    Video->>Ffmpeg: pass 1 palettegen → palette.png
    Video->>Ffmpeg: pass 2 paletteuse → output.gif
    Ffmpeg-->>Video: GIF (palette temp unlinked)

    Client->>Video: slideshow(input_paths, output, fps, duration_per_image)
    Video->>MoviePy: ImageClip per image → concatenate_videoclips
    MoviePy-->>Video: write_videofile(output)

    Client->>Video: extract_frames(input, output_dir, fps, start, duration)
    Video->>Opencv: VideoCapture → skip_frames → imwrite
    Opencv-->>Video: frame_*.png files
```

*The three multimedia pipelines: two-pass ffmpeg for GIF, MoviePy concatenation for a slideshow, and OpenCV frame sampling.*

---

## Cross-Cutting: Validation, Error Convention, and PDF Redaction

**Validation** (`src/media_tools/utils.py`): `validate_input(path)` rejects empty paths, `..` traversal, missing files, and unreadable files (URLs are allowed through, since Firecrawl accepts them). `validate_output_dir(path)` creates the parent directory if needed and checks writability. Every toolkit method runs these first and returns the error string on failure.

**Error convention**: every method returns a string and **never raises**; failures surface as `"Error: …"` results. The CLI wraps this in `{"result": ...}` / `{"error": ...}` JSON; the server registers the tools as MCP tools tagged by category.

**PDF redaction** (`PDFToolkit.redact`, MCP `pdf_redact`): a special case worth flagging. It collects per-page rectangles (from `rect_areas` and matched `text_patterns` via `pdfplumber.extract_words`), then for any page that has redactions it **rasterizes the page (scale 2.0 ≈ 144 dpi), paints black rectangles over the regions, and rewrites the page as an image-only page**. This genuinely removes the underlying text (verified by `tests/check_redact.py`: the redacted text is absent from both the extracted text and the raw bytes). The trade-off: **redacted pages lose all selectable text**; pages without redactions are copied through untouched. Rotated pages are not specially supported (rects are placed as if the page were unrotated).

---

## Failure Modes

| Failure | Symmetry / Where it surfaces | Return value |
|---------|------------------------------|--------------|
| `FIRECRAWL_API_KEY` not set | `PDFToolkit.pdf_to_markdown` (before any request) | `"Error: FIRECRAWL_API_KEY not set. Get one at https://firecrawl.dev"` |
| Firecrawl rate limit / auth | `PDFToolkit.pdf_to_markdown` (parsed from stderr) | `"Error: Firecrawl rate limit exceeded. Free tier: 500 req/month."` / `"Error: Invalid FIRECRAWL_API_KEY"` |
| Firecrawl CLI / network | `PDFToolkit.pdf_to_markdown` | `"Error: firecrawl CLI not found…"`, `"Error: Fire-PDF request timed out (120s limit)"`, or generic `Fire-PDF error: …` |
| anydoc parse failure | `OfficeToolkit.to_markdown`, `AIToolkit._read_document` | `"Error: {exc}"` / `"Error: Could not read document: …"` |
| LiteLLM proxy unreachable | `AIToolkit._call_llm`, `TTSToolkit.convert` | `"Error: LLM call failed: …"` / `"Error: {exc}"` (TTS) |
| `liteparse` not installed | `PDFToolkit.extract_structured` / `extract_screenshots` | `"Error: liteparse not installed. Run: pip install liteparse"` |
| `tesseract` not installed | `PDFToolkit.ocr` | `"Error: pytesseract not installed (pip install pytesseract, plus the tesseract binary)"` |
| `rembg` not installed | image background removal | import-time failure surfaced as `"Error: …"` |
| Ghostscript / LibreOffice / ffmpeg / pydub missing | `pdf_to_a`, `office_to_pdf`, video ops, mp3 export | `"Error: Ghostscript (gs) not found…"`, subprocess error strings, `"Error: mp3 export failed (…). Use audio_format='wav'."` |

All these are consistent with the "never raise" contract: each returns an `"Error: …"` string.

---

## Server & CLI Entry Points

The toolkit classes are aggregated in `src/media_tools/tools/__init__.py` (`PDFToolkit`, `VideoToolkit`, `ImageToolkit`, `OfficeToolkit`, `AudioToolkit`, `AIToolkit`, `TTSToolkit`). `server.py` registers ~50 MCP tools (plus scoped entry points `main_pdf`/`main_image`/`main_audio`/`main_video`/`main_office`/`main_ai`/`main_tts` via `mcp.enable(tags={…}, only=True)`), while `cli.py` wires PDF/image/audio/video/office subcommands. AI and TTS live **only** in `server.py`.

---

## See Also

- [AI Document Tools](/openwiki/tools/ai.md) — the `AIToolkit` summarize/QA/translate implementation this page chains to
- [PDF Toolkit](/openwiki/tools/pdf.md) — `pdf_to_markdown` (Firecrawl) and `redact` (rasterize-and-paint-over)
- [Office Tools](/openwiki/tools/office.md) — `to_markdown` via firecrawl-anydoc
- [Text-to-Speech](/openwiki/tools/tts.md) — the Kokoro proxy call this page wraps
