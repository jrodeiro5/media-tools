# media-tools

MCP server with **50+ multimedia processing tools** covering PDF, image, audio, video, Office documents, and AI-powered document analysis.

Built on [FastMCP](https://github.com/paulpavad/fastmcp) — drop it into any MCP-compatible client (OpenWebUI, Claude Desktop, etc.).

## Install

```bash
uv pip install media-tools
# or from source:
uv sync
```

## Usage

### As an MCP server (standalone)

```bash
media-tools-server
```

Starts a streamable-HTTP server on port `8020` by default.

### As a CLI tool

```bash
media-tools <tool-name> [args...]
```

### In OpenWebUI

Add as an external tool server pointing at your `media-tools-server` endpoint.

## Available Tools (50+)

### PDF (23)
`pdf_merge`, `pdf_split`, `pdf_compress`, `pdf_extract_text`, `pdf_extract_images`, `pdf_rotate`, `pdf_info`, `pdf_extract_structured`, `pdf_extract_screenshots`, `pdf_watermark`, `pdf_page_numbers`, `pdf_protect`, `pdf_unlock`, `images_to_pdf`, `pdf_reorder_pages`, `pdf_delete_pages`, `pdf_sign`, `pdf_fill_form`, `pdf_compare`, `pdf_to_a`, `pdf_to_markdown`, `pdf_to_docx`, `pdf_redact`

### Image (13)
`image_convert`, `image_resize`, `image_compress`, `image_crop`, `image_rotate`, `image_flip`, `image_text_overlay`, `image_border`, `image_merge`, `image_blur`, `image_ocr`, `image_info`, `image_remove_background`

### Audio (5)
`audio_convert`, `audio_trim`, `audio_fade`, `audio_speed`, `audio_info`

### Video (9)
`video_convert`, `video_trim`, `video_compress`, `video_to_gif`, `video_probe`, `video_extract_audio`, `image_to_video`, `video_extract_frames`, `audio_to_video`

### Office (3)
`office_to_markdown`, `office_to_pdf`

### AI-Powered (3)
`document_summarize`, `document_qa`, `document_translate`

## Requirements

- Python ≥ 3.11
- [uv](https://github.com/astral-sh/uv) for dependency management
- [LiteLLM proxy](https://github.com/BerriAI/litellm) for AI-powered tools (optional)

## Development

```bash
uv sync
pre-commit run --all-files
```

## License

Private — all rights reserved.
