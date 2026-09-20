"""MCP server exposing 100+ multimedia processing tools."""

from __future__ import annotations

import os

from fastmcp import FastMCP

from media_tools.tools import (
    AudioToolkit,
    ImageToolkit,
    OfficeToolkit,
    PDFToolkit,
    PiiToolkit,
    VideoToolkit,
)
from media_tools.utils import setup_logging

setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

mcp = FastMCP(
    "Media Tools",
    instructions=(
        "Multimedia processing MCP server: "
        "PDF merge/split/compress/convert, video conversion, "
        "image manipulation, audio processing, "
        "Office-to-Markdown, AI-powered document analysis."
    ),
)


@mcp.tool(name="pdf_merge", tags={"pdf"})
def pdf_merge(files: list[str], output: str, cover: bool = False) -> str:
    """Merge multiple PDF files into a single output file. cover=True also renders a page-1 thumbnail."""
    return PDFToolkit.merge(files, output, cover)


@mcp.tool(name="pdf_split", tags={"pdf"})
def pdf_split(input_path: str, pages: str, output_dir: str, cover: bool = False) -> str:
    """Split a PDF. pages: page ranges like '1-3,5,7-9' (1-indexed). cover=True also renders thumbnails."""
    return PDFToolkit.split(input_path, pages, output_dir, cover)


@mcp.tool(name="pdf_compress", tags={"pdf"})
def pdf_compress(input_path: str, output: str, quality: int = 50) -> str:
    """Compress a PDF to reduce file size."""
    return PDFToolkit.compress(input_path, output, quality)


@mcp.tool(name="pdf_extract_text", tags={"pdf"})
def pdf_extract_text(input_path: str, output: str | None = None) -> str:
    """Extract text content from a PDF. Saves to output path if provided."""
    return PDFToolkit.extract_text(input_path, output)


@mcp.tool(name="pdf_extract_images", tags={"pdf"})
def pdf_extract_images(input_path: str, output_dir: str, dpi: int = 150) -> str:
    """Render PDF pages as PNG images."""
    return PDFToolkit.extract_images(input_path, output_dir, dpi)


@mcp.tool(name="pdf_rotate", tags={"pdf"})
def pdf_rotate(input_path: str, output: str, angle: int = 90) -> str:
    """Rotate all pages in a PDF by a given angle in degrees."""
    return PDFToolkit.rotate(input_path, output, angle)


@mcp.tool(name="pdf_info", tags={"pdf"})
def pdf_info(input_path: str) -> str:
    """Get PDF metadata: page count, title, author, encryption status."""
    return PDFToolkit.info(input_path)


@mcp.tool(name="pdf_extract_structured", tags={"pdf"})
def pdf_extract_structured(
    input_path: str,
    output: str | None = None,
    ocr: bool = False,
    language: str = "eng",
    dpi: int = 150,
) -> str:
    """Extract structured text with bounding boxes using LiteParse.

    Outputs JSON with text_items (x, y, width, height, font, confidence).
    Requires: pip install liteparse
    """
    return PDFToolkit.extract_structured(input_path, output, ocr, language, dpi)


@mcp.tool(name="pdf_extract_tables", tags={"pdf"})
def pdf_extract_tables(
    input_path: str,
    output_dir: str,
    pages: list[int] | None = None,
) -> str:
    """Dump raw PDF tables to CSV files (one file per table, no layout preserved)."""
    return PDFToolkit.extract_tables(input_path, output_dir, pages)


@mcp.tool(name="pdf_tables_to_csv", tags={"pdf"})
def pdf_tables_to_csv(
    input_path: str,
    output: str,
    pages: list[int] | None = None,
) -> str:
    """Combine all PDF tables into one CSV with page/table/row columns."""
    return PDFToolkit.tables_to_csv(input_path, output, pages)


@mcp.tool(name="pdf_extract_screenshots", tags={"pdf"})
def pdf_extract_screenshots(
    input_path: str,
    output_dir: str,
    dpi: int = 150,
    page_numbers: list[int] | None = None,
) -> str:
    """Render PDF pages as PNG screenshots using LiteParse."""
    return PDFToolkit.extract_screenshots(input_path, output_dir, dpi, page_numbers)


@mcp.tool(name="pdf_watermark", tags={"pdf"})
def pdf_watermark(
    input_path: str,
    output: str,
    text: str | None = None,
    image_path: str | None = None,
    opacity: float = 0.3,
    angle: int = 45,
) -> str:
    """Add a text or image watermark to all pages of a PDF."""
    return PDFToolkit.watermark(input_path, output, text, image_path, opacity, angle)


@mcp.tool(name="pdf_page_numbers", tags={"pdf"})
def pdf_page_numbers(
    input_path: str,
    output: str,
    position: str = "bottom-center",
    format_str: str = "Page {page}",
) -> str:
    """Add page numbers to all pages of a PDF."""
    return PDFToolkit.add_page_numbers(input_path, output, position, format_str)


@mcp.tool(name="pdf_protect", tags={"pdf"})
def pdf_protect(
    input_path: str,
    output: str,
    password: str,
) -> str:
    """Add password protection to a PDF."""
    return PDFToolkit.protect(input_path, output, password)


@mcp.tool(name="pdf_unlock", tags={"pdf"})
def pdf_unlock(input_path: str, output: str, password: str) -> str:
    """Remove password protection from a PDF."""
    return PDFToolkit.unlock(input_path, output, password)


@mcp.tool(name="images_to_pdf", tags={"pdf"})
def images_to_pdf(input_paths: list[str], output: str, quality: int = 85) -> str:
    """Convert one or more images to a single PDF."""
    return PDFToolkit.images_to_pdf(input_paths, output, quality=quality)


@mcp.tool(name="pdf_reorder_pages", tags={"pdf"})
def pdf_reorder_pages(input_path: str, output: str, pages: list[int]) -> str:
    """Reorder PDF pages. pages: list of 1-indexed page numbers in desired order."""
    return PDFToolkit.reorder_pages(input_path, output, pages)


@mcp.tool(name="pdf_delete_pages", tags={"pdf"})
def pdf_delete_pages(input_path: str, output: str, pages: list[int]) -> str:
    """Delete specific pages from a PDF. pages: list of 1-indexed page numbers to remove."""
    return PDFToolkit.delete_pages(input_path, output, pages)


@mcp.tool(name="pdf_sign", tags={"pdf"})
def pdf_sign(
    input_path: str,
    output: str,
    signature_image: str,
    page: int = 1,
    x: float = 50,
    y: float = 50,
    width: float = 150,
    height: float = 50,
) -> str:
    """Add a signature image to a specific page of a PDF."""
    return PDFToolkit.sign(input_path, output, signature_image, page, x, y, width, height)


@mcp.tool(name="pdf_fill_form", tags={"pdf"})
def pdf_fill_form(input_path: str, output: str, fields: dict[str, str]) -> str:
    """Fill PDF form fields. fields: dict mapping field names to values."""
    return PDFToolkit.fill_form(input_path, output, fields)


@mcp.tool(name="pdf_compare", tags={"pdf"})
def pdf_compare(input_path: str, other_path: str) -> str:
    """Compare two PDFs and report page count and text differences."""
    return PDFToolkit.compare(input_path, other_path)


@mcp.tool(name="pdf_to_a", tags={"pdf"})
def pdf_to_a(input_path: str, output: str, pdf_a_version: str = "1b") -> str:
    """Convert PDF to PDF/A archival format (requires Ghostscript)."""
    return PDFToolkit.pdf_to_a(input_path, output, pdf_a_version)


@mcp.tool(name="pdf_to_markdown", tags={"pdf"})
def pdf_to_markdown(
    input_path: str,
    output: str | None = None,
    pages: list[int] | None = None,
) -> str:
    """Convert a PDF (or DOCX, HTML, XLSX) to Markdown locally with anydoc.

    Local files only. Supports .pdf, .docx, .html, .xlsx, .odt, .rtf.
    No API key, no network — the file never leaves the machine.
    """
    return PDFToolkit.pdf_to_markdown(input_path, output, pages)


@mcp.tool(name="md_to_branded_pdf", tags={"pdf"})
def md_to_branded_pdf(
    input_path: str,
    output: str,
    font_path: str | None = None,
    color: str | None = None,
    logo_path: str | None = None,
    logo_position: str = "bottom-right",
    page_numbers: bool = True,
) -> str:
    """Convert Markdown (H1-H3, lists, code, tables, images) to a branded PDF, offline."""
    return PDFToolkit.md_to_branded_pdf(input_path, output, font_path, color, logo_path, logo_position, page_numbers)


@mcp.tool(name="html_to_pdf", tags={"pdf"})
def html_to_pdf(input_path: str, output: str) -> str:
    """Convert a local HTML file (.html/.htm) to PDF using LibreOffice. Local files only, never URLs."""
    return PDFToolkit.html_to_pdf(input_path, output)


@mcp.tool(name="video_convert", tags={"video"})
def video_convert(input_path: str, output: str) -> str:
    """Convert a video between formats. Uses the file extension to determine output codec."""
    return VideoToolkit.convert(input_path, output)


@mcp.tool(name="video_trim", tags={"video"})
def video_trim(
    input_path: str, output: str, start: str = "00:00:00", duration: str | None = None, end: str | None = None
) -> str:
    """Trim a video. Times in HH:MM:SS. Use duration OR end (not both)."""
    return VideoToolkit.trim(input_path, output, start, duration, end)


@mcp.tool(name="video_compress", tags={"video"})
def video_compress(input_path: str, output: str, crf: int = 28) -> str:
    """Compress a video. CRF: 18 is near-lossless, 23-28 is good quality, 51 is worst."""
    return VideoToolkit.compress(input_path, output, crf)


@mcp.tool(name="video_to_gif", tags={"video"})
def video_to_gif(
    input_path: str,
    output: str,
    width: int = 480,
    fps: int = 10,
    start: str = "00:00:00",
    duration: str = "5",
) -> str:
    """Convert a video segment into an animated GIF."""
    return VideoToolkit.to_gif(input_path, output, width, fps, start, duration)


@mcp.tool(name="video_probe", tags={"video"})
def video_probe(input_path: str) -> str:
    """Get detailed video metadata: codec, resolution, duration, bitrate."""
    return VideoToolkit.probe(input_path)


@mcp.tool(name="video_extract_audio", tags={"video"})
def video_extract_audio(input_path: str, output: str, format: str = "mp3", bitrate: str = "192k") -> str:
    """Extract the audio track from a video. Format: mp3, aac, wav, ogg, or flac."""
    return VideoToolkit.extract_audio(input_path, output, format, bitrate)


@mcp.tool(name="video_merge", tags={"video"})
def video_merge(input_paths: list[str], output: str, cover: bool = False) -> str:
    """Concatenate videos in order (stream-copy fast path, else re-encode). cover=True also grabs a thumbnail."""
    return VideoToolkit.merge(input_paths, output, cover)


@mcp.tool(name="video_contact_sheet", tags={"video"})
def video_contact_sheet(
    input_path: str,
    output_png: str,
    cols: int = 4,
    fps: int = 1,
    thumb_width: int = 320,
    manifest: bool = True,
) -> str:
    """Render a grid contact sheet PNG + sidecar JSON manifest (tiles capped at 120, timestamps approximate on VFR)."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.contact_sheet(input_path, output_png, cols, fps, thumb_width, manifest)


@mcp.tool(name="video_export_social_pack", tags={"video"})
def video_export_social_pack(src: str, out_dir: str, mode: str = "center-crop") -> str:
    """Export 9:16 / 1:1 / 16:9 MP4 variants in one decode pass. mode: center-crop or letterbox."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.export_social_pack(src, out_dir, mode)


@mcp.tool(name="video_chroma_cut", tags={"video"})
def video_chroma_cut(
    input_path: str,
    output: str,
    color: str = "00FF00",
    similarity: float = 0.3,
    blend: float = 0.1,
    background: str = "black",
) -> str:
    """Key out a solid color via colorkey, composited over a background image path or color."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.chroma_cut(input_path, output, color, similarity, blend, background)


@mcp.tool(name="video_object_erase", tags={"video"})
def video_object_erase(
    input_path: str,
    output: str,
    boxes: list[str],
    start: str | None = None,
    duration: str | None = None,
) -> str:
    """Erase fixed x,y,w,h rects on every frame via inpaint (TELEA). Optional start/duration range."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.object_erase(input_path, output, boxes, start, duration)


@mcp.tool(name="video_blur_faces", tags={"video"})
def video_blur_faces(
    input_path: str,
    output: str,
    every_n_frames: int = 5,
    mode: str = "pixelate",
) -> str:
    """Obscure faces on every video frame (Haar detect every Nth frame, IoU-track between)."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.blur_faces(input_path, output, every_n_frames, mode)


@mcp.tool(name="video_thumbnail", tags={"video"})
def video_thumbnail(input_path: str, output: str, timestamp: str = "00:00:01", accurate: bool = False) -> str:
    """Grab a single frame thumbnail. Fast input-seek by default; accurate=True for a frame-exact grab."""
    return VideoToolkit.thumbnail(input_path, output, timestamp, accurate)


@mcp.tool(name="video_crop", tags={"video"})
def video_crop(input_path: str, output: str, width: int, height: int, x: int = 0, y: int = 0) -> str:
    """Crop a video to a rectangle (width x height, offset x,y)."""
    return VideoToolkit.crop(input_path, output, width, height, x, y)


@mcp.tool(name="video_rotate", tags={"video"})
def video_rotate(input_path: str, output: str, angle: int = 90) -> str:
    """Rotate a video by 90, 180, or 270 degrees clockwise."""
    return VideoToolkit.rotate(input_path, output, angle)


@mcp.tool(name="video_resize", tags={"video"})
def video_resize(input_path: str, output: str, width: int, height: int = -2) -> str:
    """Resize a video. Height -2 preserves aspect ratio (even dimensions)."""
    return VideoToolkit.resize(input_path, output, width, height)


@mcp.tool(name="video_watermark", tags={"video"})
def video_watermark(
    input_path: str,
    watermark_path: str,
    output: str,
    position: str = "bottom-right",
    margin: int = 10,
) -> str:
    """Overlay an image watermark onto a video."""
    return VideoToolkit.watermark(input_path, watermark_path, output, position, margin)


@mcp.tool(name="video_reverse", tags={"video"})
def video_reverse(input_path: str, output: str) -> str:
    """Reverse a video (and its audio) — loads the full clip into memory."""
    return VideoToolkit.reverse(input_path, output)


@mcp.tool(name="video_mute", tags={"video"})
def video_mute(input_path: str, output: str) -> str:
    """Strip all audio streams, copying the video stream without re-encoding."""
    return VideoToolkit.mute(input_path, output)


@mcp.tool(name="video_speed", tags={"video"})
def video_speed(input_path: str, output: str, factor: float = 2.0) -> str:
    """Change video playback speed. factor > 1 speeds up, < 1 slows down."""
    return VideoToolkit.speed(input_path, output, factor)


@mcp.tool(name="video_subtitle_burn", tags={"video"})
def video_subtitle_burn(input_path: str, subtitle_path: str, output: str, preset: str = "plain") -> str:
    """Burn an .srt/.ass subtitle file into the video. preset: plain, karaoke, or social."""
    return VideoToolkit.subtitle_burn(input_path, subtitle_path, output, preset)


@mcp.tool(name="video_transcribe", tags={"video"})
def video_transcribe(
    input_path: str,
    out_dir: str,
    model: str | None = None,
    language: str | None = None,
    min_silence_ms: int = 1000,
    silence_thresh_dbfs: float | None = None,
    keep_ms: int = 200,
) -> str:
    """Transcribe a video's speech to .srt in out_dir (extract → chunks → SRT, no burn)."""
    return VideoToolkit.transcribe(input_path, out_dir, model, language, min_silence_ms, silence_thresh_dbfs, keep_ms)


@mcp.tool(name="gif_to_mp4", tags={"video"})
def gif_to_mp4(input_path: str, output: str) -> str:
    """Convert a GIF (or any silent looping input) to MP4 (h264 + yuv420p + faststart)."""
    return VideoToolkit.gif_to_mp4(input_path, output)


@mcp.tool(name="image_convert", tags={"image"})
def image_convert(input_path: str, output: str, quality: int = 85) -> str:
    """Convert an image to another format (extension determines format)."""
    return ImageToolkit.convert(input_path, output, quality)


@mcp.tool(name="image_resize", tags={"image"})
def image_resize(
    input_path: str,
    output: str,
    width: int | None = None,
    height: int | None = None,
    percent: int | None = None,
) -> str:
    """Resize an image by pixels (width/height) or by percentage."""
    return ImageToolkit.resize(input_path, output, width, height, percent)


@mcp.tool(name="image_compress", tags={"image"})
def image_compress(input_path: str, output: str, quality: int = 70) -> str:
    """Compress an image. Quality: 1 (smallest) to 100 (highest)."""
    return ImageToolkit.compress(input_path, output, quality)


@mcp.tool(name="image_crop", tags={"image"})
def image_crop(input_path: str, output: str, left: int, top: int, right: int, bottom: int) -> str:
    """Crop an image by pixel coordinates (left, top, right, bottom)."""
    return ImageToolkit.crop(input_path, output, left, top, right, bottom)


@mcp.tool(name="image_info", tags={"image"})
def image_info(input_path: str) -> str:
    """Get image metadata: format, dimensions, mode, file size."""
    return ImageToolkit.info(input_path)


@mcp.tool(name="image_remove_background", tags={"image"})
def image_remove_background(input_path: str, output: str, alpha_matting: bool = False) -> str:
    """Remove background from an image using AI (U2-Net model)."""
    return ImageToolkit.remove_background(input_path, output, alpha_matting)


@mcp.tool(name="image_rotate", tags={"image"})
def image_rotate(input_path: str, output: str, angle: int = 90) -> str:
    """Rotate an image by 90, 180, or 270 degrees."""
    return ImageToolkit.rotate(input_path, output, angle)


@mcp.tool(name="image_flip", tags={"image"})
def image_flip(input_path: str, output: str, direction: str = "horizontal") -> str:
    """Flip an image horizontally or vertically."""
    return ImageToolkit.flip(input_path, output, direction)


@mcp.tool(name="image_text", tags={"image"})
def image_text(
    input_path: str,
    output: str,
    text: str,
    position: str = "bottom-right",
    font_size: int = 24,
    color: str = "#ffffff",
    stroke_color: str = "#000000",
    stroke_width: int = 2,
    margin: int = 10,
) -> str:
    """Add a text overlay to an image."""
    return ImageToolkit.text_overlay(
        input_path, output, text, position, font_size, color, stroke_color, stroke_width, margin
    )


@mcp.tool(name="image_border", tags={"image"})
def image_border(input_path: str, output: str, width: int = 10, color: str = "#ffffff") -> str:
    """Add a border/frame to an image."""
    return ImageToolkit.border(input_path, output, width, color)


@mcp.tool(name="image_merge", tags={"image"})
def image_merge(input_paths: list[str], output: str, direction: str = "horizontal") -> str:
    """Merge images side-by-side (horizontal) or stacked (vertical)."""
    return ImageToolkit.merge(input_paths, output, direction)


@mcp.tool(name="image_watermark", tags={"image"})
def image_watermark(
    input_path: str,
    watermark_path: str,
    output: str,
    position: str = "bottom-right",
    margin: int = 10,
    opacity: float = 1.0,
) -> str:
    """Overlay a watermark image onto another image."""
    return ImageToolkit.watermark(input_path, watermark_path, output, position, margin, opacity)


@mcp.tool(name="image_apply_brand", tags={"image"})
def image_apply_brand(
    input_path: str,
    output: str,
    font_path: str | None = None,
    color: str | None = None,
    logo_path: str | None = None,
    logo_position: str = "bottom-right",
    logo_scale: float = 0.15,
) -> str:
    """Apply an offline brand kit: optional color band + logo corner paste."""
    return ImageToolkit.apply_brand_kit(input_path, output, font_path, color, logo_path, logo_position, logo_scale)


@mcp.tool(name="image_collage", tags={"image"})
def image_collage(
    input_paths: list[str],
    output: str,
    columns: int = 2,
    cell_size: int = 300,
    spacing: int = 5,
    background: str = "#ffffff",
) -> str:
    """Arrange images into a fixed-size grid collage."""
    return ImageToolkit.collage(input_paths, output, columns, cell_size, spacing, background)


@mcp.tool(name="image_blur", tags={"image"})
def image_blur(input_path: str, output: str, radius: float = 5.0) -> str:
    """Apply a Gaussian blur filter to an image."""
    return ImageToolkit.blur(input_path, output, radius)


@mcp.tool(name="image_export_social_pack", tags={"image"})
def image_export_social_pack(src: str, out_dir: str, mode: str = "center-crop") -> str:
    """Export 9:16 / 1:1 / 16:9 image variants. mode: center-crop or letterbox. Never upscales."""
    return ImageToolkit.export_social_pack(src, out_dir, mode)


@mcp.tool(name="image_ocr", tags={"image"})
def image_ocr(input_path: str) -> str:
    """Extract text from an image using Tesseract OCR."""
    return ImageToolkit.ocr(input_path)


@mcp.tool(name="image_grayscale", tags={"image"})
def image_grayscale(input_path: str, output: str) -> str:
    """Convert an image to grayscale (mode L)."""
    return ImageToolkit.grayscale(input_path, output)


@mcp.tool(name="image_sharpen", tags={"image"})
def image_sharpen(input_path: str, output: str, radius: float = 2.0, percent: int = 150, threshold: int = 3) -> str:
    """Sharpen an image with an unsharp mask (sensible defaults)."""
    return ImageToolkit.sharpen(input_path, output, radius, percent, threshold)


@mcp.tool(name="image_circle_crop", tags={"image"})
def image_circle_crop(input_path: str, output: str) -> str:
    """Center-crop an image to a circle; corners stay transparent (RGBA)."""
    return ImageToolkit.circle_crop(input_path, output)


@mcp.tool(name="image_split_tiles", tags={"image"})
def image_split_tiles(input_path: str, output_dir: str, rows: int = 2, cols: int = 2) -> str:
    """Split an image into a rows×cols tile grid + sidecar JSON manifest."""
    return ImageToolkit.split_tiles(input_path, output_dir, rows, cols)


@mcp.tool(name="image_upscale", tags={"image"})
def image_upscale(input_path: str, output: str, scale: int = 2) -> str:
    """Upscale an image 2x/3x with FSRCNN-small (model downloads on first run)."""
    return ImageToolkit.upscale(input_path, output, scale)


@mcp.tool(name="image_blur_faces", tags={"image"})
def image_blur_faces(input_path: str, output: str, mode: str = "pixelate") -> str:
    """Obscure faces in an image with the Haar frontal cascade. mode: pixelate or blur."""
    return ImageToolkit.blur_faces(input_path, output, mode)


@mcp.tool(name="audio_convert", tags={"audio"})
def audio_convert(input_path: str, output: str, bitrate: str = "192k") -> str:
    """Convert audio between formats (extension determines format)."""
    return AudioToolkit.convert(input_path, output, bitrate)


@mcp.tool(name="audio_trim", tags={"audio"})
def audio_trim(input_path: str, output: str, start_ms: int = 0, end_ms: int = 0) -> str:
    """Trim audio by milliseconds. If end_ms=0, trims from start to end."""
    return AudioToolkit.trim(input_path, output, start_ms, end_ms)


@mcp.tool(name="audio_fade", tags={"audio"})
def audio_fade(input_path: str, output: str, fade_in_ms: int = 1000, fade_out_ms: int = 2000) -> str:
    """Add fade-in and fade-out effects to an audio file."""
    return AudioToolkit.fade(input_path, output, fade_in_ms, fade_out_ms)


@mcp.tool(name="audio_speed", tags={"audio"})
def audio_speed(input_path: str, output: str, factor: float = 1.5) -> str:
    """Change audio playback speed. 2.0 = double, 0.5 = half speed."""
    return AudioToolkit.speed(input_path, output, factor)


@mcp.tool(name="audio_info", tags={"audio"})
def audio_info(input_path: str) -> str:
    """Get audio metadata: duration, channels, sample rate, file size."""
    return AudioToolkit.info(input_path)


@mcp.tool(name="audio_merge", tags={"audio"})
def audio_merge(input_paths: list[str], output: str) -> str:
    """Concatenate multiple audio clips in order."""
    return AudioToolkit.merge(input_paths, output)


@mcp.tool(name="audio_normalize", tags={"audio"})
def audio_normalize(input_path: str, output: str, target_dbfs: float = -20.0) -> str:
    """Normalize audio volume to a target dBFS level."""
    return AudioToolkit.normalize(input_path, output, target_dbfs)


@mcp.tool(name="audio_chunk_silence", tags={"audio"})
def audio_chunk_silence(
    input_path: str,
    output_dir: str,
    min_silence_ms: int = 1000,
    silence_thresh_dbfs: float | None = None,
    keep_ms: int = 200,
) -> str:
    """Split audio on silence into bite-size clips sized for small-model transcribe windows."""
    return AudioToolkit.chunk_silence(input_path, output_dir, min_silence_ms, silence_thresh_dbfs, keep_ms)


@mcp.tool(name="audio_transcribe", tags={"audio"})
def audio_transcribe(
    input_path: str,
    output: str | None = None,
    model: str | None = None,
    language: str | None = None,
) -> str:
    """Transcribe speech to text via the local LiteLLM proxy (whisper)."""
    return AudioToolkit.transcribe(input_path, output, model, language)


@mcp.tool(name="audio_transcribe_chunks", tags={"audio"})
def audio_transcribe_chunks(
    input_path: str,
    out_dir: str,
    model: str | None = None,
    language: str | None = None,
    min_silence_ms: int = 1000,
    silence_thresh_dbfs: float | None = None,
    keep_ms: int = 200,
) -> str:
    """Chunk audio on silence, transcribe each chunk in order, reassemble one transcript."""
    return AudioToolkit.transcribe_chunks(
        input_path, out_dir, model, language, min_silence_ms, silence_thresh_dbfs, keep_ms
    )


@mcp.tool(name="audio_pad_to_duration", tags={"audio"})
def audio_pad_to_duration(input_path: str, output: str, target_ms: int, position: str = "end") -> str:
    """Pad audio with generated silence to reach exactly target_ms. No time-stretching."""
    return AudioToolkit.pad_to_duration(input_path, output, target_ms, position)


@mcp.tool(name="audio_to_srt", tags={"audio"})
def audio_to_srt(input: str, output: str) -> str:
    """Format transcribe_chunks segments (transcript.json path or segments JSON) as a SubRip (.srt) file."""
    return AudioToolkit.transcript_to_srt(input, output)


@mcp.tool(name="office_to_markdown", tags={"office"})
def office_to_markdown(input_path: str, output: str | None = None) -> str:
    """Convert Office files (.docx, .pptx, .xlsx) to Markdown."""
    return OfficeToolkit.to_markdown(input_path, output)


@mcp.tool(name="office_inspect", tags={"office"})
def office_inspect(input_path: str, mode: str = "outline", page: str | None = None) -> str:
    """Read a .docx/.xlsx/.pptx structure via OfficeCLI: mode text, outline, stats, issues, annotated or forms."""
    return OfficeToolkit.inspect(input_path, mode, page)


@mcp.tool(name="office_edit", tags={"office"})
def office_edit(input_path: str, output: str, commands: str) -> str:
    """Edit a .docx/.xlsx/.pptx into a new file via OfficeCLI batch JSON (array of {command, path, props...})."""
    return OfficeToolkit.edit(input_path, output, commands)


@mcp.tool(name="url_to_markdown", tags={"office"})
def url_to_markdown(url: str, output: str | None = None) -> str:
    """Fetch a web page or PDF URL as Markdown via Firecrawl (cloud; needs FIRECRAWL_API_KEY)."""
    return OfficeToolkit.url_to_markdown(url, output)


@mcp.tool(name="office_to_pdf", tags={"office"})
def office_to_pdf(input_path: str, output: str) -> str:
    """Convert Office documents to PDF using LibreOffice."""
    return OfficeToolkit.to_pdf(input_path, output)


# === PDF to DOCX ===


@mcp.tool(name="pdf_to_docx", tags={"pdf"})
def pdf_to_docx(input_path: str, output: str) -> str:
    """Convert PDF to DOCX using pdf2docx."""
    from media_tools.tools.pdf import PDFToolkit

    return PDFToolkit.to_docx(input_path, output)


# === Video/Image/Audio Extensions ===


@mcp.tool(name="image_to_video", tags={"image"})
def image_to_video(
    input_paths: list[str],
    output: str,
    fps: int = 30,
    duration_per_image: int = 5,
) -> str:
    """Create a video slideshow from images using MoviePy."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.slideshow(input_paths, output, fps, duration_per_image)


@mcp.tool(name="video_extract_frames", tags={"video"})
def video_extract_frames(
    input_path: str,
    output_dir: str,
    fps: int = 1,
    start: str = "00:00:00",
    duration: str | None = None,
) -> str:
    """Extract frames from video as images using OpenCV."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.extract_frames(input_path, output_dir, fps, start, duration)


@mcp.tool(name="audio_to_video", tags={"audio"})
def audio_to_video(input_path: str, video_path: str, output: str) -> str:
    """Create a video with audio track using MoviePy."""
    from media_tools.tools.video import VideoToolkit

    return VideoToolkit.audio_to_video(input_path, video_path, output)


# === PII ===


@mcp.tool(name="pii_scan", tags={"pii"})
def pii_scan(input_path: str) -> str:
    """Find Spanish/EU PII (DNI/NIF, NIE, passport, IBAN, email, phone) in a PDF or text file.
    Returns counts and masked previews, never raw values."""
    return PiiToolkit.scan(input_path)


@mcp.tool(name="pii_redact", tags={"pii"})
def pii_redact(input_path: str, output: str) -> str:
    """Find PII in a PDF and black it out (pages with hits become image-only)."""
    return PiiToolkit.redact(input_path, output)


# === PDF Redaction ===


@mcp.tool(name="pdf_redact", tags={"pdf"})
def pdf_redact(
    input_path: str,
    output: str,
    text_patterns: list[str] | None = None,
    rect_areas: list[dict] | None = None,
) -> str:
    """Redact (black out) sensitive information from PDF.

    text_patterns: list of text strings to redact
    rect_areas: list of {x, y, width, height} to redact
    """
    from media_tools.tools.pdf import PDFToolkit

    return PDFToolkit.redact(input_path, output, text_patterns, rect_areas)


@mcp.tool(name="pdf_salvage", tags={"pdf"})
def pdf_salvage(
    input_path: str,
    out_dir: str,
    ocr_fallback: bool = True,
    dpi: int = 150,
) -> str:
    """Salvage readable text/images per page from a corrupt PDF into out_dir (one bad page never fails the job)."""
    from media_tools.tools.pdf import PDFToolkit

    return PDFToolkit.salvage(input_path, out_dir, ocr_fallback, dpi)


@mcp.tool(name="pdf_repair", tags={"pdf"})
def pdf_repair(input_path: str, output: str) -> str:
    """Rebuild a corrupt PDF's xref and re-emit parseable pages to a new viewable PDF (never in place)."""
    from media_tools.tools.pdf import PDFToolkit

    return PDFToolkit.repair(input_path, output)


# === Batch ===


@mcp.tool(name="batch_sweep", tags={"batch"})
def batch_sweep(input_dir: str, output_dir: str, op: str, pattern: str = "*", max_files: int = 200) -> str:
    """Apply one op across every matching file in a folder, outputs under output_dir (never in place).

    op: one of pdf_compress, image_convert, image_compress, audio_convert, video_compress.
    Records per-file ok/error/skipped, continues past errors, writes sweep_manifest.json.
    """
    from media_tools.sweep import sweep

    return sweep(input_dir, output_dir, op, pattern, max_files)


# === Probe (cross-family router) ===


# Tag {"pdf"}: one family tag is required for scoped-server filtering; pdf is the
# largest family and matches the returns_reclaim precedent for cross-cutting utilities.
@mcp.tool(name="media_probe", tags={"pdf"})
def media_probe(input_path: str) -> str:
    """Sniff any local file (magic bytes + extension) and rank the media_tools that apply.

    Read-only. Returns JSON: mime, kind, streams, width/height, duration, pages,
    has_audio, has_alpha, plus a ranked tools list with one-line whys.
    """
    from media_tools.tools.probe import ProbeToolkit

    return ProbeToolkit.probe(input_path)


# === Returns (originals stash) ===


@mcp.tool(name="returns_reclaim", tags={"pdf"})
def returns_reclaim(ticket_id: str, output: str | None = None, search_dir: str | None = None) -> str:
    """Restore a stashed original by ticket ID (see pdf_delete_pages / pdf_redact output)."""
    from media_tools.utils import returns_reclaim as _reclaim

    if search_dir is not None:
        return _reclaim(ticket_id, output, search_dir)
    return _reclaim(ticket_id, output)


# === AI-Powered Document Tools ===


@mcp.tool(name="document_summarize", tags={"ai"})
def document_summarize(input_path: str, output: str | None = None) -> str:
    """Summarize a document using LLM (Gemma 4 e2e via LiteLLM)."""
    from media_tools.tools.ai import AIToolkit

    return AIToolkit.summarize(input_path, output)


@mcp.tool(name="document_qa", tags={"ai"})
def document_qa(input_path: str, question: str, output: str | None = None) -> str:
    """Answer questions about a document using LLM (Gemma 4 e2e via LiteLLM)."""
    from media_tools.tools.ai import AIToolkit

    return AIToolkit.qa(input_path, question, output)


@mcp.tool(name="document_translate", tags={"ai"})
def document_translate(input_path: str, output: str, target_language: str = "en") -> str:
    """Translate document content using LLM (Gemma 4 e2e via LiteLLM)."""
    from media_tools.tools.ai import AIToolkit

    return AIToolkit.translate(input_path, output, target_language)


# === Text-to-Speech ===


@mcp.tool(name="text_to_speech", tags={"tts"})
def text_to_speech(
    text: str,
    output: str,
    voice: str = "",
    audio_format: str = "wav",
    language: str = "en",
) -> str:
    """Convert text to speech locally via the LiteLLM proxy (omlx / Kokoro).

    No API key and no network egress. Override the endpoint with LITELLM_URL
    and the model with TTS_MODEL. `language` picks a default voice; pass
    `voice` to override with a specific Kokoro id (af_heart, ef_dora,
    em_alex, …). Reliable in en/es; other languages have thinner voice data.
    """
    from media_tools.tools.tts import TTSToolkit

    return TTSToolkit.convert(
        text=text,
        output=output,
        voice=voice,
        audio_format=audio_format,
        language=language,
    )


def main():
    if os.environ.get("MEDIA_TOOLS_SEARCH") == "1":
        # 85 tools ≈ 13.7k tokens in tools/list; this exposes search_tools + call_tool (≈330).
        # ceiling: BM25 is lexical, so vague queries miss; swap for a vector transform if that bites.
        from fastmcp.server.transforms.search import BM25SearchTransform

        mcp.add_transform(BM25SearchTransform(max_results=5))
    port = int(os.environ.get("PORT", "8020"))
    host = os.environ.get("HOST", "127.0.0.1")
    mcp.run(transport="streamable-http", host=host, port=port)


def _run_scoped(tag: str):
    mcp.enable(tags={tag}, only=True)
    port = int(os.environ.get("PORT", "8020"))
    host = os.environ.get("HOST", "127.0.0.1")
    mcp.run(transport="streamable-http", host=host, port=port)


def main_pdf():
    _run_scoped("pdf")


def main_image():
    _run_scoped("image")


def main_audio():
    _run_scoped("audio")


def main_video():
    _run_scoped("video")


def main_office():
    _run_scoped("office")


def main_ai():
    _run_scoped("ai")


def main_tts():
    _run_scoped("tts")


def main_batch():
    _run_scoped("batch")


if __name__ == "__main__":
    main()
