# media-tools

MCP server with **25 multimedia processing tools** covering PDF, image, audio, video, and Office documents.

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

## Available Tools (25)

### PDF (12)
`pdf_extract_text`, `pdf_merge`, `pdf_split`, `pdf_rotate`, `pdf_encrypt`, `pdf_decrypt`, `pdf_add_watermark`, `pdf_add_logo`, `pdf_extract_images`, `pdf_to_image`, `pdf_sign`, `pdf_fill_form`

### Image (8)
`image_resize`, `image_convert`, `image_compress`, `image_crop`, `image_rotate`, `image_info`, `image_add_text`, `image_remove_background`

### Audio/Video (3)
`audio_convert`, `video_extract_audio`, `video_trim`

### Office (2)
`office_extract_text`, `office_convert`

### Utilities
`firecrawl_parse` — extract content from any URL via Firecrawl

## Requirements

- Python ≥ 3.11
- [uv](https://github.com/astral-sh/uv) for dependency management

## Development

```bash
uv sync
pre-commit run --all-files
```

## License

Private — all rights reserved.
