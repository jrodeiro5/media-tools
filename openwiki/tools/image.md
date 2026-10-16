---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Tool Reference
title: Image Tools
description: "23 ImageToolkit methods plus image_to_video (VideoToolkit.slideshow), yielding 24 MCP tools tagged image and 22 CLI subcommands. Covers format conversion, resize, compress, crop, rotate, flip, text overlay, border, merge, blur, watermark, collage, OCR, info, remove_background, grayscale, sharpen, circle_crop, split_tiles, upscale, blur_faces, apply_brand, export_social_pack, and image_to_video. Supports jpg, png, webp, gif, bmp, tiff, ico, heic, heif, avif."
resource: /src/media_tools/tools/image.py
tags: [image, tools, Pillow, pytesseract, rembg, pillow-heif, opencv, FSRCNN]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-20T19:00:50.561Z
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
generated: { by: "openwiki/0.5.2", at: "2026-09-20T19:00:50.561Z" }
---

## Overview

The `ImageToolkit` class provides 23 image-processing methods. All 23 are wired to the MCP server (tag `image`), and 22 are reachable through the CLI `media-tools image …` subcommands. The 24th MCP image-tagged tool, `image_to_video`, delegates to `VideoToolkit.slideshow` for creating video slideshows from images.

In MCP, every image method is registered with `tags={"image"}`. In the CLI, `remove_background` is the only ImageToolkit method without a CLI subcommand; all others have one.

## Supported Formats

```
jpg, jpeg, png, webp, gif, bmp, tiff, ico, heic, heif, avif
```

## Tool List

| Method | MCP Name | CLI Command | Description | Key Dependencies |
|---|---|---|---|---|
| `convert` | `image_convert` | `image convert` | Convert between formats (quality 1–100) | Pillow, pillow-heif |
| `resize` | `image_resize` | `image resize` | Resize by pixels (width/height) or percentage | Pillow |
| `compress` | `image_compress` | `image compress` | Compress image (quality 1–100) | Pillow |
| `crop` | `image_crop` | `image crop` | Crop by pixel coordinates (left, top, right, bottom) | Pillow |
| `rotate` | `image_rotate` | `image rotate` | Rotate by angle (90/180/270, default 90°) | Pillow |
| `flip` | `image_flip` | `image flip` | Flip horizontal or vertical | Pillow |
| `text_overlay` | `image_text` | `image text` | Add text overlay (position, font_size, color, stroke) | Pillow |
| `border` | `image_border` | `image border` | Add border/frame (width, color) | Pillow |
| `merge` | `image_merge` | `image merge` | Merge multiple images (horizontal/vertical) | Pillow |
| `blur` | `image_blur` | `image blur` | Apply Gaussian blur (radius) | Pillow |
| `watermark` | `image_watermark` | `image watermark` | Overlay a watermark image (position, opacity) | Pillow |
| `collage` | `image_collage` | `image collage` | Arrange images into a fixed-size grid collage | Pillow |
| `apply_brand_kit` | `image_apply_brand` | `image apply-brand` | Apply brand kit: color band + logo corner paste | Pillow |
| `export_social_pack` | `image_export_social_pack` | `image social-pack` | Export 9:16 / 1:1 / 16:9 image variants (center-crop or letterbox) | Pillow |
| `ocr` | `image_ocr` | `image ocr` | Extract text via Tesseract OCR | pytesseract |
| `remove_background` | `image_remove_background` | *(no CLI)* | Remove background using AI (U2-Net model) | rembg |
| `grayscale` | `image_grayscale` | `image grayscale` | Convert image to grayscale (mode L) | Pillow |
| `sharpen` | `image_sharpen` | `image sharpen` | Sharpen with unsharp mask (radius, percent, threshold) | Pillow |
| `circle_crop` | `image_circle_crop` | `image circle-crop` | Center-crop to circle; corners stay transparent (RGBA) | Pillow |
| `split_tiles` | `image_split_tiles` | `image split-tiles` | Split image into rows×cols tile grid + JSON manifest | Pillow |
| `upscale` | `image_upscale` | `image upscale` | Upscale 2×/3× with FSRCNN-small (downloads model on first run) | OpenCV, cv2.dnn_superres |
| `blur_faces` | `image_blur_faces` | `image blur-faces` | Obscure faces via Haar frontal cascade (pixelate or blur) | OpenCV |
| `info` | `image_info` | `image info` | Get metadata: format, dimensions, mode, file size | Pillow |
| `slideshow` *(VideoToolkit)* | `image_to_video` | *(no CLI)* | Create a video slideshow from images using MoviePy | MoviePy |

## Implementation Details

### Dependencies

**Required:**
- `Pillow >= 12.3.0` — Core image processing (open, save, resize, crop, filter)
- `pillow-heif >= 0.20` — HEIC/HEIF format support

**Optional:**
- `pytesseract >= 0.3.10` — OCR text extraction (requires Tesseract system installation)
- `rembg >= 2.0.75` — AI background removal (U2-Net model)
- `opencv-python` / `cv2` — Required for `upscale` (FSRCNN) and `blur_faces` (Haar cascade)

### Model Cache (`_vision.py`)

The `upscale` and `blur_faces` methods rely on pre-trained models managed by the shared `_vision.py` module (`repo://src/media_tools/tools/_vision.py`).

Models are **never vendored into git**. On first use, `ensure_asset(key)` downloads the model to `~/.cache/media-tools/models/`. Every file is **SHA256-pinned**: the function computes the hash of any cached file and re-downloads when it mismatches. If there is no cached file and no network, the caller receives an offline `RuntimeError` (prefixed `"Error: ..."`) rather than an unhandled exception.

The registered assets are:

| Key | Model | Source License | Size |
|---|---|---|---|
| `fsrcnn_x2` | FSRCNN-small ×2 | Apache-2.0 (Saafke/FSRCNN_Tensorflow) | ~10 KB |
| `fsrcnn_x3` | FSRCNN-small ×3 | Apache-2.0 (Saafke/FSRCNN_Tensorflow) | ~10 KB |
| `haar_frontalface` | Haar frontal-face cascade | Intel BSD (opencv/opencv) | ~100 KB |

The `_vision.py` module also provides two helper functions consumed by `blur_faces`:

- **`detect_faces(gray, xml_path, scale_factor, min_neighbors)`** — Wraps `cv2.CascadeClassifier.detectMultiScale`. Returns a list of `(x, y, w, h)` tuples for frontal faces ≥ 30 px. Raises `RuntimeError` if the cascade XML fails to load.
- **`obscure_boxes(img, boxes, mode)`** — Pixelates (downsample 1/16 then nearest-neighbor upsample) or Gaussian-blurs each bounding box in-place on a BGR ndarray.

For video face-blurring, `_vision.py` also exports **`track_boxes(tracked, fresh, iou_threshold, max_missed)`** (greedy IoU matching) and **`iou(a, b)`**, used by `VideoToolkit.blur_faces` to maintain identity across frames.

### Key Implementation Notes

- **Format conversion**: Output format determined by file extension. RGBA/P modes converted to RGB for JPEG.
- **Quality**: Applies to JPEG and WebP only (1–100 scale).
- **Crop validation**: Coordinates validated inline in `crop()` against image dimensions (no negative values, left < right, top < bottom, right ≤ width, bottom ≤ height). The shared helper `_validate_crop_bounds` in `utils.py` is defined but never called.
- **OCR**: Returns extracted text as string (not file path). Fails gracefully with a message if `pytesseract` is not installed.
- **Background removal**: Optional `alpha_matting` parameter for finer edge detection; MCP-only (no CLI subcommand). Fails gracefully if `rembg` is not installed.
- **Grayscale**: Converts to Pillow mode `"L"`. Always produces output even if the source is already grayscale.
- **Sharpen**: Uses `ImageFilter.UnsharpMask` with configurable `radius` (default 2.0), `percent` (default 150), and `threshold` (default 3).
- **Circle crop**: Converts to RGBA, center-crops to a square, applies a circular alpha mask. Output as JPEG converts to RGB (losing transparency).
- **Split tiles**: Divides the image into a `rows × cols` grid, writes each tile as PNG, and emits a sidecar JSON manifest with tile paths, coordinates, and dimensions.
- **Upscale**: Uses OpenCV's `cv2.dnn_superres.DnnSuperResImpl` with FSRCNN-small models (2× or 3×). Model is SHA256-pinned and downloaded to `~/.cache/media-tools/models/` on first run.
- **Blur faces**: Uses OpenCV Haar frontal-face cascade. Finds near-upright frontal faces ≥ 30 px; misses profiles, heavy occlusion, tiny or rotated faces. Two modes: `"pixelate"` (default) and `"blur"`. Zero faces is success (output is still written). This is best-effort, not a privacy guarantee.
- **Apply brand kit**: Accepts optional `color` (draws an 8%-height color band at bottom) and `logo_path` (resizes to `logo_scale` fraction of image width and composites at `logo_position`). The `font_path` parameter is accepted for API parity with `md_to_branded_pdf` but has no visual effect.
- **Export social pack**: Generates 9:16 (1080×1920), 1:1 (1080×1080), and 16:9 (1920×1080) variants. Content is **never upscaled** past source resolution. Two modes: `center-crop` (crop to target aspect then scale down) and `letterbox` (scale-to-fit, pad with black). EXIF orientation is applied before processing. Note: naive center-crop can cut salient subjects — smart-focal detection is a future upgrade.
- **Image to video** (`image_to_video`): Delegates to `VideoToolkit.slideshow`, which uses MoviePy. Accepts `fps` (default 30) and `duration_per_image` (default 5 seconds).

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how image tools are exposed via MCP/CLI
- [Video Tools](/openwiki/tools/video.md) — `image_to_video` cross-reference (VideoToolkit.slideshow)
- [PDF Tools](/openwiki/tools/pdf.md) — `images_to_pdf` cross-reference
