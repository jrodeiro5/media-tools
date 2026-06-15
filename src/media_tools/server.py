"""MCP server exposing 25 multimedia processing tools."""

from __future__ import annotations

import os

from fastmcp import FastMCP

from media_tools.tools import (
    AudioToolkit,
    ImageToolkit,
    OfficeToolkit,
    PDFToolkit,
    VideoToolkit,
)
from media_tools.utils import setup_logging

setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

mcp = FastMCP(
    "Media Tools",
    instructions=(
        "Multimedia processing MCP server: "
        "PDF merge/split/compress, video conversion, "
        "image manipulation, audio processing, "
        "Office-to-Markdown."
    ),
)


@mcp.tool(name="pdf_merge")
def pdf_merge(files: list[str], output: str) -> str:
    """Merge multiple PDF files into a single output file."""
    return PDFToolkit.merge(files, output)


@mcp.tool(name="pdf_split")
def pdf_split(input_path: str, pages: str, output_dir: str) -> str:
    """Split a PDF. pages: page ranges like '1-3,5,7-9' (1-indexed)."""
    return PDFToolkit.split(input_path, pages, output_dir)


@mcp.tool(name="pdf_compress")
def pdf_compress(input_path: str, output: str, quality: int = 50) -> str:
    """Compress a PDF to reduce file size."""
    return PDFToolkit.compress(input_path, output, quality)


@mcp.tool(name="pdf_extract_text")
def pdf_extract_text(input_path: str, output: str | None = None) -> str:
    """Extract text content from a PDF. Saves to output path if provided."""
    return PDFToolkit.extract_text(input_path, output)


@mcp.tool(name="pdf_extract_images")
def pdf_extract_images(input_path: str, output_dir: str, dpi: int = 150) -> str:
    """Render PDF pages as PNG images."""
    return PDFToolkit.extract_images(input_path, output_dir, dpi)


@mcp.tool(name="pdf_rotate")
def pdf_rotate(input_path: str, output: str, angle: int = 90) -> str:
    """Rotate all pages in a PDF by a given angle in degrees."""
    return PDFToolkit.rotate(input_path, output, angle)


@mcp.tool(name="pdf_info")
def pdf_info(input_path: str) -> str:
    """Get PDF metadata: page count, title, author, encryption status."""
    return PDFToolkit.info(input_path)


@mcp.tool(name="pdf_extract_structured")
def pdf_extract_structured(
    input_path: str, output: str | None = None,
    ocr: bool = False, language: str = "eng", dpi: int = 150,
) -> str:
    """Extract structured text with bounding boxes using LiteParse.

    Outputs JSON with text_items (x, y, width, height, font, confidence).
    Requires: pip install liteparse
    """
    return PDFToolkit.extract_structured(input_path, output, ocr, language, dpi)


@mcp.tool(name="pdf_extract_screenshots")
def pdf_extract_screenshots(
    input_path: str, output_dir: str, dpi: int = 150,
    page_numbers: list[int] | None = None,
) -> str:
    """Render PDF pages as PNG screenshots using LiteParse."""
    return PDFToolkit.extract_screenshots(input_path, output_dir, dpi, page_numbers)


@mcp.tool(name="pdf_watermark")
def pdf_watermark(
    input_path: str, output: str,
    text: str | None = None, image_path: str | None = None,
    opacity: float = 0.3, angle: int = 45,
) -> str:
    """Add a text or image watermark to all pages of a PDF."""
    return PDFToolkit.watermark(input_path, output, text, image_path, opacity, angle)


@mcp.tool(name="pdf_page_numbers")
def pdf_page_numbers(
    input_path: str, output: str,
    position: str = "bottom-center",
    format_str: str = "Page {page}",
) -> str:
    """Add page numbers to all pages of a PDF."""
    return PDFToolkit.add_page_numbers(input_path, output, position, format_str)


@mcp.tool(name="pdf_protect")
def pdf_protect(
    input_path: str, output: str, password: str,
) -> str:
    """Add password protection to a PDF."""
    return PDFToolkit.protect(input_path, output, password)


@mcp.tool(name="pdf_unlock")
def pdf_unlock(input_path: str, output: str, password: str) -> str:
    """Remove password protection from a PDF."""
    return PDFToolkit.unlock(input_path, output, password)


@mcp.tool(name="images_to_pdf")
def images_to_pdf(input_paths: list[str], output: str, quality: int = 85) -> str:
    """Convert one or more images to a single PDF."""
    return PDFToolkit.images_to_pdf(input_paths, output, quality=quality)


@mcp.tool(name="pdf_reorder_pages")
def pdf_reorder_pages(input_path: str, output: str, pages: list[int]) -> str:
    """Reorder PDF pages. pages: list of 1-indexed page numbers in desired order."""
    return PDFToolkit.reorder_pages(input_path, output, pages)


@mcp.tool(name="pdf_delete_pages")
def pdf_delete_pages(input_path: str, output: str, pages: list[int]) -> str:
    """Delete specific pages from a PDF. pages: list of 1-indexed page numbers to remove."""
    return PDFToolkit.delete_pages(input_path, output, pages)


@mcp.tool(name="pdf_to_markdown")
def pdf_to_markdown(
    input_path: str, output: str | None = None,
    pages: list[int] | None = None,
) -> str:
    """Convert a PDF (or DOCX, HTML, XLSX) to Markdown via Firecrawl CLI.

    Local files only. Supports .pdf, .docx, .html, .xlsx, .odt, .rtf.
    Requires: npx firecrawl installed + FIRECRAWL_API_KEY env var.
    Free tier: 500 requests/month.
    """
    return PDFToolkit.pdf_to_markdown(input_path, output, pages)


@mcp.tool(name="video_convert")
def video_convert(input_path: str, output: str) -> str:
    """Convert a video between formats. Uses the file extension to determine output codec."""
    return VideoToolkit.convert(input_path, output)


@mcp.tool(name="video_trim")
def video_trim(
    input_path: str, output: str, start: str = "00:00:00", duration: str | None = None, end: str | None = None
) -> str:
    """Trim a video. Times in HH:MM:SS. Use duration OR end (not both)."""
    return VideoToolkit.trim(input_path, output, start, duration, end)


@mcp.tool(name="video_compress")
def video_compress(input_path: str, output: str, crf: int = 28) -> str:
    """Compress a video. CRF: 18 is near-lossless, 23-28 is good quality, 51 is worst."""
    return VideoToolkit.compress(input_path, output, crf)


@mcp.tool(name="video_to_gif")
def video_to_gif(
    input_path: str, output: str, width: int = 480, fps: int = 10,
    start: str = "00:00:00", duration: str = "5",
) -> str:
    """Convert a video segment into an animated GIF."""
    return VideoToolkit.to_gif(input_path, output, width, fps, start, duration)


@mcp.tool(name="video_probe")
def video_probe(input_path: str) -> str:
    """Get detailed video metadata: codec, resolution, duration, bitrate."""
    return VideoToolkit.probe(input_path)


@mcp.tool(name="video_extract_audio")
def video_extract_audio(input_path: str, output: str, format: str = "mp3", bitrate: str = "192k") -> str:
    """Extract the audio track from a video. Format: mp3, aac, wav, ogg, or flac."""
    return VideoToolkit.extract_audio(input_path, output, format, bitrate)


@mcp.tool(name="image_convert")
def image_convert(input_path: str, output: str, quality: int = 85) -> str:
    """Convert an image to another format (extension determines format)."""
    return ImageToolkit.convert(input_path, output, quality)


@mcp.tool(name="image_resize")
def image_resize(
    input_path: str, output: str,
    width: int | None = None, height: int | None = None, percent: int | None = None,
) -> str:
    """Resize an image by pixels (width/height) or by percentage."""
    return ImageToolkit.resize(input_path, output, width, height, percent)


@mcp.tool(name="image_compress")
def image_compress(input_path: str, output: str, quality: int = 70) -> str:
    """Compress an image. Quality: 1 (smallest) to 100 (highest)."""
    return ImageToolkit.compress(input_path, output, quality)


@mcp.tool(name="image_crop")
def image_crop(input_path: str, output: str, left: int, top: int, right: int, bottom: int) -> str:
    """Crop an image by pixel coordinates (left, top, right, bottom)."""
    return ImageToolkit.crop(input_path, output, left, top, right, bottom)


@mcp.tool(name="image_info")
def image_info(input_path: str) -> str:
    """Get image metadata: format, dimensions, mode, file size."""
    return ImageToolkit.info(input_path)


@mcp.tool(name="audio_convert")
def audio_convert(input_path: str, output: str, bitrate: str = "192k") -> str:
    """Convert audio between formats (extension determines format)."""
    return AudioToolkit.convert(input_path, output, bitrate)


@mcp.tool(name="audio_trim")
def audio_trim(input_path: str, output: str, start_ms: int = 0, end_ms: int = 0) -> str:
    """Trim audio by milliseconds. If end_ms=0, trims from start to end."""
    return AudioToolkit.trim(input_path, output, start_ms, end_ms)


@mcp.tool(name="audio_fade")
def audio_fade(input_path: str, output: str, fade_in_ms: int = 1000, fade_out_ms: int = 2000) -> str:
    """Add fade-in and fade-out effects to an audio file."""
    return AudioToolkit.fade(input_path, output, fade_in_ms, fade_out_ms)


@mcp.tool(name="audio_speed")
def audio_speed(input_path: str, output: str, factor: float = 1.5) -> str:
    """Change audio playback speed. 2.0 = double, 0.5 = half speed."""
    return AudioToolkit.speed(input_path, output, factor)


@mcp.tool(name="audio_info")
def audio_info(input_path: str) -> str:
    """Get audio metadata: duration, channels, sample rate, file size."""
    return AudioToolkit.info(input_path)


@mcp.tool(name="office_to_markdown")
def office_to_markdown(input_path: str, output: str | None = None) -> str:
    """Convert Office files (.docx, .pptx, .xlsx) to Markdown."""
    return OfficeToolkit.to_markdown(input_path, output)


@mcp.tool(name="office_to_pdf")
def office_to_pdf(input_path: str, output: str) -> str:
    """Convert Office documents to PDF using LibreOffice."""
    return OfficeToolkit.to_pdf(input_path, output)


def main():
    port = int(os.environ.get("PORT", "8020"))
    mcp.run(transport="streamable-http", port=port)


if __name__ == "__main__":
    main()
