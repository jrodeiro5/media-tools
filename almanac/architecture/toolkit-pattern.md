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
---

# Toolkit pattern

All tool functionality lives in toolkit classes under `src/media_tools/tools/`.
Each toolkit is a class with `@staticmethod` methods that perform a specific
category of media processing.

## Toolkit classes

| class | file | lines | category |
|---|---|---|---|
| `PDFToolkit` | `pdf.py` | 1030 | PDF manipulation [@pdf-py] |
| `VideoToolkit` | `video.py` | 519 | Video manipulation [@video-py] |
| `ImageToolkit` | `image.py` | 557 | Image manipulation [@image-py] |
| `OfficeToolkit` | `office.py` | 73 | Office document conversion [@office-py] |
| `AIToolkit` | `ai.py` | 136 | AI-powered document analysis [@ai-py] |
| `TTSToolkit` | `tts.py` | 114 | Text-to-speech [@tts-py] |
| `AudioToolkit` | `audio.py` | 177 | Audio manipulation [@audio-py] |

Each toolkit exports a `name` attribute (e.g. `"pdf"`) used for scoped server
tagging. The toolkit classes are exported from `tools/__init__.py` [@tools-init].
Toolkit methods call the shared helpers in [Utilities](../architecture/utilities)
(`validate_input`, `validate_output_dir`).

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
  `reportlab`, `pdf2docx` [@pdf-py]
- **ImageToolkit**: `Pillow`, `pytesseract`, `rembg` [@image-py]
- **AudioToolkit**: `pydub` [@audio-py]
- **VideoToolkit**: `moviepy`, `opencv-python-headless` [@video-py]
- **OfficeToolkit**: `anydoc`, `subprocess` (LibreOffice) [@office-py]
- **AIToolkit**: `anydoc`, `litellm` (via HTTP) [@ai-py]
- **TTSToolkit**: `litellm` (via HTTP), `omlx` (local) [@tts-py]

The CLI and server import the 5 core toolkits (PDF, Video, Image, Audio,
Office) at module level, so those dependencies must be installed for any
invocation. AI and TTS are lazy-imported inside their handler functions —
`litellm` and `omlx` are loaded only when those tools are invoked. This is
intentional: it avoids loading heavy VLM and audio model dependencies when
only PDF or image tools are needed.

## Adding a new toolkit

To add a new toolkit:

1. Create `src/media_tools/tools/<name>.py` with a class named
   `<Name>Toolkit`.
2. Add the class to `src/media_tools/tools/__init__.py`.
3. Add `@mcp.tool` decorators in `server.py` for each tool.
4. Add CLI handlers in `cli.py` (optional — the CLI is not required for
   new toolkits).
5. Update `pyproject.toml` with any new dependencies.
