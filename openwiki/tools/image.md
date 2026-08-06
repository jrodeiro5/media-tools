---
type: Tool Reference
title: Image Tools
description: "12 image processing tools: convert, resize, compress, crop, rotate, flip, text overlay, border, merge, blur, OCR, and info. Supports jpg, png, webp, gif, bmp, tiff, ico, heic, heif, avif."
resource: /src/media_tools/tools/image.py
tags: [image, tools, Pillow, pytesseract, rembg, pillow-heif]
---

## Overview

The `ImageToolkit` class provides 12 image processing operations accessible via both the MCP server and CLI.

## Supported Formats

```
jpg, jpeg, png, webp, gif, bmp, tiff, ico, heic, heif, avif
```

## Tool List

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `image_convert` | `image convert` | Convert between formats (quality: 1-100) | Pillow, pillow-heif |
| `image_resize` | `image resize` | Resize by pixels (width/height) or percentage | Pillow |
| `image_compress` | `image compress` | Compress image (quality: 1-100) | Pillow |
| `image_crop` | `image crop` | Crop by pixel coordinates (left, top, right, bottom) | Pillow |
| `image_rotate` | `image rotate` | Rotate by angle (default 90°) | Pillow |
| `image_flip` | `image flip` | Flip horizontal or vertical | Pillow |
| `image_text` | `image text` | Add text overlay (position, font_size, color, stroke) | Pillow |
| `image_border` | `image border` | Add border (width, color) | Pillow |
| `image_merge` | `image merge` | Merge multiple images (horizontal/vertical) | Pillow |
| `image_blur` | `image blur` | Apply blur effect (radius) | Pillow |
| `image_ocr` | `image ocr` | Extract text via OCR (Tesseract) | pytesseract |
| `image_remove_background` | `image remove-background` | Remove background using AI (U2-Net model) | rembg |
| `image_info` | `image info` | Get metadata: format, dimensions, mode, file size | Pillow |

## Implementation Details

### Dependencies

**Required:**
- `Pillow >= 11.0` — Core image processing (open, save, resize, crop, filter)
- `pillow-heif >= 0.20` — HEIC/HEIF format support

**Optional:**
- `pytesseract >= 0.3.10` — OCR text extraction (requires Tesseract system installation)
- `rembg >= 2.0.0` — AI background removal (U2-Net model)

### Key Implementation Notes

- **Format conversion**: Output format determined by file extension. RGBA/P modes converted to RGB for JPEG.
- **Quality**: Applies to JPEG and WebP only (1-100 scale).
- **Crop validation**: Coordinates validated against image dimensions (no negative values, left < right, top < bottom).
- **OCR**: Returns extracted text as string (not file path).
- **Background removal**: Optional `alpha_matting` parameter for finer edge detection.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how image tools are exposed via MCP/CLI
- [PDF Tools](/openwiki/tools/pdf.md) — `images_to_pdf` cross-reference
