---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Tool Reference
title: Image Tools
description: "15 image processing methods (12 exposed via CLI, 7 via MCP): convert, resize, compress, crop, rotate, flip, text overlay, border, merge, blur, watermark, collage, OCR, and info. Supports jpg, png, webp, gif, bmp, tiff, ico, heic, heif, avif."
resource: /src/media_tools/tools/image.py
tags: [image, tools, Pillow, pytesseract, rembg, pillow-heif]
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
verified:
  - by: openwiki/0.5.2
    at: 2026-09-19T19:14:37.934Z
sources:
  - id: openwiki-source-f24618d3fb91081293690cc3
    resource: repo://src/media_tools/cli.py
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-a415c6a83eccf5df70162d43
    resource: repo://src/media_tools/tools/image.py
  - id: openwiki-source-f7be093be4a966caaa381229
    resource: repo://src/media_tools/utils.py
  - id: openwiki-source-0f45531f40d627881b1ab052
    resource: repo://tests/check_redact.py
---

## Overview

The `ImageToolkit` class provides 15 image processing methods. Twelve are exposed via the CLI (convert, resize, compress, crop, rotate, flip, text, border, merge, blur, ocr, info) and seven via the MCP server (convert, resize, compress, crop, info, remove_background, text). Only two methods — `watermark` and `collage` — are exposed to neither interface. `border`, `merge`, and `blur` are CLI-only (no MCP tools), and `remove_background` is MCP-only (no CLI subcommand).

## Supported Formats

```
jpg, jpeg, png, webp, gif, bmp, tiff, ico, heic, heif, avif
```

## Tool List

| Method | MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|-------------|------------------|
| `convert` | `image_convert` | `image convert` | Convert between formats (quality: 1-100) | Pillow, pillow-heif |
| `resize` | `image_resize` | `image resize` | Resize by pixels (width/height) or percentage | Pillow |
| `compress` | `image_compress` | `image compress` | Compress image (quality: 1-100) | Pillow |
| `crop` | `image_crop` | `image crop` | Crop by pixel coordinates (left, top, right, bottom) | Pillow |
| `rotate` | *(no MCP)* | `image rotate` | Rotate by angle (90/180/270, default 90°) | Pillow |
| `flip` | *(no MCP)* | `image flip` | Flip horizontal or vertical | Pillow |
| `text_overlay` | `image_text` | `image text` | Add text overlay (position, font_size, color, stroke) | Pillow |
| `border` *(CLI-only)* | *(no MCP)* | `image border` | Add border (width, color) | Pillow |
| `merge` *(CLI-only)* | *(no MCP)* | `image merge` | Merge multiple images (horizontal/vertical) | Pillow |
| `blur` *(CLI-only)* | *(no MCP)* | `image blur` | Apply blur effect (radius) | Pillow |
| `ocr` | `image_ocr` | `image ocr` | Extract text via OCR (Tesseract) | pytesseract |
| `remove_background` | `image_remove_background` | *(no CLI)* | Remove background using AI (U2-Net model) | rembg |
| `watermark` *(not exposed)* | *(none)* | *(none)* | Watermark an image | Pillow |
| `collage` *(not exposed)* | *(none)* | *(none)* | Arrange images into a collage | Pillow |
| `info` | `image_info` | `image info` | Get metadata: format, dimensions, mode, file size | Pillow |

## Implementation Details

### Dependencies

**Required:**
- `Pillow >= 12.3.0` — Core image processing (open, save, resize, crop, filter)
- `pillow-heif >= 0.20` — HEIC/HEIF format support

**Optional:**
- `pytesseract >= 0.3.10` — OCR text extraction (requires Tesseract system installation)
- `rembg >= 2.0.75` — AI background removal (U2-Net model)

### Key Implementation Notes

- **Format conversion**: Output format determined by file extension. RGBA/P modes converted to RGB for JPEG.
- **Quality**: Applies to JPEG and WebP only (1-100 scale).
- **Crop validation**: Coordinates validated inline in `crop()` against image dimensions (no negative values, left < right, top < bottom, right ≤ width, bottom ≤ height). The shared helper `_validate_crop_bounds` in `utils.py` is defined but never called.
- **OCR**: Returns extracted text as string (not file path). Fails gracefully with a message if `pytesseract` is not installed.
- **Background removal**: Optional `alpha_matting` parameter for finer edge detection; MCP-only (no CLI subcommand). Fails gracefully if `rembg` is not installed.
- **Not yet exposed**: `ImageToolkit.watermark` and `ImageToolkit.collage` have no `@mcp.tool` or CLI registration. Wire them through `server.py` and `cli.py` to expose them. `border`, `merge`, and `blur` are wired to the CLI only (no MCP tools), and `remove_background` is exposed via MCP only (no CLI subcommand).

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how image tools are exposed via MCP/CLI
- [PDF Tools](/openwiki/tools/pdf.md) — `images_to_pdf` cross-reference
