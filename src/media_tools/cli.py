"""Agent-native CLI for media-tools.

Usage:
    media-tools pdf merge --input f1.pdf f2.pdf --output merged.pdf
    media-tools image rotate --input photo.jpg --output rotated.jpg --angle 90
    media-tools image ocr --input scan.png
    media-tools --help
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from media_tools.tools.pdf import PDFToolkit
from media_tools.tools.image import ImageToolkit
from media_tools.tools.audio import AudioToolkit
from media_tools.tools.video import VideoToolkit
from media_tools.tools.office import OfficeToolkit


def _error(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False)


def _result(**kwargs) -> str:
    return json.dumps(kwargs, ensure_ascii=False)


# ── PDF commands ──────────────────────────────────────────────

def _pdf_merge(args: list[str]) -> str:
    if len(args) < 2:
        return _error("pdf merge requires at least 2 input files")
    output = None
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return PDFToolkit.pdf_merge(output=output, input_paths=args[:i // 2 + 1] if output else args)


def _pdf_split(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf split requires an input file")
    input_path = args[0]
    output = None
    pages = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--pages" and i + 1 < len(args):
            pages = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return PDFToolkit.pdf_split(input_path=input_path, output=output, pages=pages)


def _pdf_compress(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf compress requires an input file")
    input_path = args[0]
    output = None
    quality = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--quality" and i + 1 < len(args):
            quality = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    kwargs = {"input_path": input_path, "output": output}
    if quality is not None:
        kwargs["quality"] = quality
    return PDFToolkit.pdf_compress(**kwargs)


def _pdf_rotate(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf rotate requires an input file")
    input_path = args[0]
    output = None
    angle = 90
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--angle" and i + 1 < len(args):
            angle = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return PDFToolkit.pdf_rotate(input_path=input_path, output=output, angle=angle)


def _pdf_extract_text(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf extract-text requires an input file")
    return PDFToolkit.pdf_extract_text(input_path=args[0])


def _pdf_extract_images(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf extract-images requires an input file")
    input_path = args[0]
    output_dir = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_dir = args[i + 1]
            i += 2
        else:
            i += 1
    if not output_dir:
        return _error("--output is required")
    return PDFToolkit.pdf_extract_images(input_path=input_path, output_dir=output_dir)


def _pdf_to_markdown(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf to-markdown requires an input file")
    input_path = args[0]
    output = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--pages" and i + 1 < len(args):
            i += 2  # skip pages arg, handled by toolkit
        else:
            i += 1
    return PDFToolkit.pdf_to_markdown(input_path=input_path, output=output)


def _pdf_watermark(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf watermark requires an input file")
    input_path = args[0]
    output = None
    text = None
    image_path = None
    opacity = 0.3
    angle = 45
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--text" and i + 1 < len(args):
            text = args[i + 1]
            i += 2
        elif args[i] == "--image" and i + 1 < len(args):
            image_path = args[i + 1]
            i += 2
        elif args[i] == "--opacity" and i + 1 < len(args):
            opacity = float(args[i + 1])
            i += 2
        elif args[i] == "--angle" and i + 1 < len(args):
            angle = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return PDFToolkit.watermark(input_path, output, text=text, image_path=image_path, opacity=opacity, angle=angle)


def _pdf_page_numbers(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf page-numbers requires an input file")
    input_path = args[0]
    output = None
    position = "bottom-center"
    fmt = "Page {page}"
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--position" and i + 1 < len(args):
            position = args[i + 1]
            i += 2
        elif args[i] == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return PDFToolkit.add_page_numbers(input_path, output, position, fmt)


def _pdf_protect(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf protect requires an input file")
    input_path = args[0]
    output = None
    password = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--password" and i + 1 < len(args):
            password = args[i + 1]
            i += 2
        else:
            i += 1
    if not output or not password:
        return _error("--output and --password are required")
    return PDFToolkit.protect(input_path, output, password)


def _pdf_unlock(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf unlock requires an input file")
    input_path = args[0]
    output = None
    password = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--password" and i + 1 < len(args):
            password = args[i + 1]
            i += 2
        else:
            i += 1
    if not output or not password:
        return _error("--output and --password are required")
    return PDFToolkit.unlock(input_path, output, password)


def _images_to_pdf(args: list[str]) -> str:
    if len(args) < 1:
        return _error("images-to-pdf requires at least one input image")
    output = None
    quality = 85
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--quality" and i + 1 < len(args):
            quality = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return PDFToolkit.images_to_pdf(input_paths=args[:len(args) - (i // 2 if output else 0)], output=output, quality=quality)


def _pdf_reorder(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf reorder requires an input file")
    input_path = args[0]
    output = None
    pages = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--pages" and i + 1 < len(args):
            pages = [int(p) for p in args[i + 1].split(",")]
            i += 2
        else:
            i += 1
    if not output or not pages:
        return _error("--output and --pages (comma-separated) are required")
    return PDFToolkit.reorder_pages(input_path, output, pages)


def _pdf_delete(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf delete requires an input file")
    input_path = args[0]
    output = None
    pages = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--pages" and i + 1 < len(args):
            pages = [int(p) for p in args[i + 1].split(",")]
            i += 2
        else:
            i += 1
    if not output or not pages:
        return _error("--output and --pages (comma-separated) are required")
    return PDFToolkit.delete_pages(input_path, output, pages)


def _pdf_sign(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf sign requires an input file")
    input_path = args[0]
    output = None
    sig_image = None
    page = 1
    x, y, w, h = 50, 50, 150, 50
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--signature" and i + 1 < len(args):
            sig_image = args[i + 1]
            i += 2
        elif args[i] == "--page" and i + 1 < len(args):
            page = int(args[i + 1])
            i += 2
        elif args[i] == "--pos" and i + 1 < len(args):
            parts = args[i + 1].split(",")
            if len(parts) == 4:
                x, y, w, h = [float(p) for p in parts]
            i += 2
        else:
            i += 1
    if not output or not sig_image:
        return _error("--output and --signature are required")
    return PDFToolkit.sign(input_path, output, sig_image, page, x, y, w, h)


def _pdf_fill_form(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf fill-form requires an input file")
    input_path = args[0]
    output = None
    fields = {}
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--field" and i + 1 < len(args):
            pair = args[i + 1].split("=", 1)
            if len(pair) == 2:
                fields[pair[0]] = pair[1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    if not fields:
        return _error("at least one --field NAME=VALUE is required")
    return PDFToolkit.fill_form(input_path, output, fields)


def _pdf_compare(args: list[str]) -> str:
    if len(args) < 2:
        return _error("pdf compare requires 2 input files")
    return PDFToolkit.compare(args[0], args[1])


def _pdf_to_a(args: list[str]) -> str:
    if len(args) < 1:
        return _error("pdf to-a requires an input file")
    input_path = args[0]
    output = None
    version = "1b"
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--version" and i + 1 < len(args):
            version = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return PDFToolkit.pdf_to_a(input_path, output, version)


# ── Image commands ────────────────────────────────────────────

def _image_convert(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image convert requires an input file")
    input_path = args[0]
    output = None
    quality = 85
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--quality" and i + 1 < len(args):
            quality = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.convert(input_path, output, quality)


def _image_resize(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image resize requires an input file")
    input_path = args[0]
    output = None
    width = height = percent = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--width" and i + 1 < len(args):
            width = int(args[i + 1])
            i += 2
        elif args[i] == "--height" and i + 1 < len(args):
            height = int(args[i + 1])
            i += 2
        elif args[i] == "--percent" and i + 1 < len(args):
            percent = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.resize(input_path, output, width, height, percent)


def _image_compress(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image compress requires an input file")
    input_path = args[0]
    output = None
    quality = 70
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--quality" and i + 1 < len(args):
            quality = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.compress(input_path, output, quality)


def _image_crop(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image crop requires an input file")
    input_path = args[0]
    output = None
    left = top = right = bottom = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--left" and i + 1 < len(args):
            left = int(args[i + 1])
            i += 2
        elif args[i] == "--top" and i + 1 < len(args):
            top = int(args[i + 1])
            i += 2
        elif args[i] == "--right" and i + 1 < len(args):
            right = int(args[i + 1])
            i += 2
        elif args[i] == "--bottom" and i + 1 < len(args):
            bottom = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output or any(v is None for v in (left, top, right, bottom)):
        return _error("--output and --left --top --right --bottom are required")
    return ImageToolkit.crop(input_path, output, left, top, right, bottom)


def _image_rotate(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image rotate requires an input file")
    input_path = args[0]
    output = None
    angle = 90
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--angle" and i + 1 < len(args):
            angle = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.rotate(input_path, output, angle)


def _image_flip(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image flip requires an input file")
    input_path = args[0]
    output = None
    direction = "horizontal"
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--direction" and i + 1 < len(args):
            direction = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.flip(input_path, output, direction)


def _image_text(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image text requires an input file")
    input_path = args[0]
    output = None
    text = None
    position = "bottom-right"
    font_size = 24
    color = "#ffffff"
    stroke_color = "#000000"
    stroke_width = 2
    margin = 10
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--text" and i + 1 < len(args):
            text = args[i + 1]
            i += 2
        elif args[i] == "--position" and i + 1 < len(args):
            position = args[i + 1]
            i += 2
        elif args[i] == "--font-size" and i + 1 < len(args):
            font_size = int(args[i + 1])
            i += 2
        elif args[i] == "--color" and i + 1 < len(args):
            color = args[i + 1]
            i += 2
        elif args[i] == "--stroke" and i + 1 < len(args):
            stroke_color = args[i + 1]
            i += 2
        else:
            i += 1
    if not output or not text:
        return _error("--output and --text are required")
    return ImageToolkit.text_overlay(input_path, output, text, position, font_size, color, stroke_color, stroke_width, margin)


def _image_border(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image border requires an input file")
    input_path = args[0]
    output = None
    width = 10
    color = "#ffffff"
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--width" and i + 1 < len(args):
            width = int(args[i + 1])
            i += 2
        elif args[i] == "--color" and i + 1 < len(args):
            color = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.border(input_path, output, width, color)


def _image_merge(args: list[str]) -> str:
    if len(args) < 2:
        return _error("image merge requires at least 2 input images")
    output = None
    direction = "horizontal"
    input_paths = []
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--direction" and i + 1 < len(args):
            direction = args[i + 1]
            i += 2
        else:
            input_paths.append(args[i])
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.merge(input_paths=input_paths, output=output, direction=direction)


def _image_blur(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image blur requires an input file")
    input_path = args[0]
    output = None
    radius = 5.0
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--radius" and i + 1 < len(args):
            radius = float(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return ImageToolkit.blur(input_path, output, radius)


def _image_ocr(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image ocr requires an input file")
    return ImageToolkit.ocr(args[0])


def _image_info(args: list[str]) -> str:
    if len(args) < 1:
        return _error("image info requires an input file")
    return ImageToolkit.info(args[0])


# ── Audio commands ────────────────────────────────────────────

def _audio_convert(args: list[str]) -> str:
    if len(args) < 1:
        return _error("audio convert requires an input file")
    input_path = args[0]
    output = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return AudioToolkit.convert(input_path, output)


def _audio_trim(args: list[str]) -> str:
    if len(args) < 1:
        return _error("audio trim requires an input file")
    input_path = args[0]
    output = None
    start_ms = end_ms = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--start" and i + 1 < len(args):
            start_ms = int(args[i + 1])
            i += 2
        elif args[i] == "--end" and i + 1 < len(args):
            end_ms = int(args[i + 1])
            i += 2
        else:
            i += 1
    if not output or start_ms is None:
        return _error("--output and --start are required")
    kwargs = {"input_path": input_path, "output": output, "start_ms": start_ms}
    if end_ms is not None:
        kwargs["end_ms"] = end_ms
    return AudioToolkit.trim(**kwargs)


def _audio_fade(args: list[str]) -> str:
    if len(args) < 1:
        return _error("audio fade requires an input file")
    input_path = args[0]
    output = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return AudioToolkit.fade(input_path, output)


def _audio_speed(args: list[str]) -> str:
    if len(args) < 1:
        return _error("audio speed requires an input file")
    input_path = args[0]
    output = None
    factor = 1.5
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--factor" and i + 1 < len(args):
            factor = float(args[i + 1])
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return AudioToolkit.speed(input_path, output, factor)


def _audio_info(args: list[str]) -> str:
    if len(args) < 1:
        return _error("audio info requires an input file")
    return AudioToolkit.info(args[0])


# ── Video commands ────────────────────────────────────────────

def _video_convert(args: list[str]) -> str:
    if len(args) < 1:
        return _error("video convert requires an input file")
    input_path = args[0]
    output = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return VideoToolkit.convert(input_path, output)


def _video_trim(args: list[str]) -> str:
    if len(args) < 1:
        return _error("video trim requires an input file")
    input_path = args[0]
    output = None
    start = end = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--start" and i + 1 < len(args):
            start = args[i + 1]
            i += 2
        elif args[i] == "--end" and i + 1 < len(args):
            end = args[i + 1]
            i += 2
        else:
            i += 1
    if not output or not start:
        return _error("--output and --start are required")
    kwargs = {"input_path": input_path, "output": output, "start": start}
    if end:
        kwargs["end"] = end
    return VideoToolkit.trim(**kwargs)


def _video_compress(args: list[str]) -> str:
    if len(args) < 1:
        return _error("video compress requires an input file")
    input_path = args[0]
    output = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return VideoToolkit.compress(input_path, output)


def _video_to_gif(args: list[str]) -> str:
    if len(args) < 1:
        return _error("video to-gif requires an input file")
    input_path = args[0]
    output = None
    fps = 10
    size = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--fps" and i + 1 < len(args):
            fps = int(args[i + 1])
            i += 2
        elif args[i] == "--size" and i + 1 < len(args):
            size = args[i + 1]
            i += 2
        else:
            i += 1
    kwargs = {"input_path": input_path, "output": output or f"{Path(input_path).stem}.gif"}
    if fps:
        kwargs["fps"] = fps
    if size:
        kwargs["size"] = size
    return VideoToolkit.to_gif(**kwargs)


def _video_info(args: list[str]) -> str:
    if len(args) < 1:
        return _error("video info requires an input file")
    return VideoToolkit.info(args[0])


# ── Office commands ───────────────────────────────────────────

def _office_to_markdown(args: list[str]) -> str:
    if len(args) < 1:
        return _error("office to-markdown requires an input file")
    input_path = args[0]
    output = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1
    return OfficeToolkit.to_markdown(input_path, output)


def _office_to_pdf(args: list[str]) -> str:
    if len(args) < 1:
        return _error("office to-pdf requires an input file")
    input_path = args[0]
    output = None
    i = 1
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1
    if not output:
        return _error("--output is required")
    return OfficeToolkit.to_pdf(input_path, output)


# ── Dispatch ──────────────────────────────────────────────────

COMMANDS = {
    # PDF
    ("pdf", "merge"): _pdf_merge,
    ("pdf", "split"): _pdf_split,
    ("pdf", "compress"): _pdf_compress,
    ("pdf", "rotate"): _pdf_rotate,
    ("pdf", "extract-text"): _pdf_extract_text,
    ("pdf", "extract-images"): _pdf_extract_images,
    ("pdf", "to-markdown"): _pdf_to_markdown,
    ("pdf", "watermark"): _pdf_watermark,
    ("pdf", "page-numbers"): _pdf_page_numbers,
    ("pdf", "protect"): _pdf_protect,
    ("pdf", "unlock"): _pdf_unlock,
    ("pdf", "images-to-pdf"): _images_to_pdf,
    ("pdf", "reorder"): _pdf_reorder,
    ("pdf", "delete"): _pdf_delete,
    ("pdf", "sign"): _pdf_sign,
    ("pdf", "fill-form"): _pdf_fill_form,
    ("pdf", "compare"): _pdf_compare,
    ("pdf", "to-a"): _pdf_to_a,
    # Image
    ("image", "convert"): _image_convert,
    ("image", "resize"): _image_resize,
    ("image", "compress"): _image_compress,
    ("image", "crop"): _image_crop,
    ("image", "rotate"): _image_rotate,
    ("image", "flip"): _image_flip,
    ("image", "text"): _image_text,
    ("image", "border"): _image_border,
    ("image", "merge"): _image_merge,
    ("image", "blur"): _image_blur,
    ("image", "ocr"): _image_ocr,
    ("image", "info"): _image_info,
    # Audio
    ("audio", "convert"): _audio_convert,
    ("audio", "trim"): _audio_trim,
    ("audio", "fade"): _audio_fade,
    ("audio", "speed"): _audio_speed,
    ("audio", "info"): _audio_info,
    # Video
    ("video", "convert"): _video_convert,
    ("video", "trim"): _video_trim,
    ("video", "compress"): _video_compress,
    ("video", "to-gif"): _video_to_gif,
    ("video", "info"): _video_info,
    # Office
    ("office", "to-markdown"): _office_to_markdown,
    ("office", "to-pdf"): _office_to_pdf,
}


HELP = """\
media-tools — Agent-native media processing CLI

Usage:
    media-tools <category> <command> [args] [--options]

Categories:
    pdf, image, audio, video, office

PDF Commands:
    merge <files...> --output <file>          Merge PDFs
    split <file> --output <dir> [--pages N-M] Split pages
    compress <file> --output <file>           Compress PDF
    rotate <file> --output <file> [--angle 90] Rotate
    extract-text <file>                       Extract text
    extract-images <file> --output <dir>      Pages → PNG
    to-markdown <file> [--output <file>]      PDF → Markdown
    watermark <file> --output <f> --text <t>  Add watermark
    page-numbers <file> --output <f>          Add page numbers
    protect <file> --output <f> --password <p>Password protect
    unlock <file> --output <f> --password <p> Remove password
    images-to-pdf <imgs...> --output <file>   Images → PDF
    reorder <file> --output <f> --pages N,M   Reorder pages
    delete <file> --output <f> --pages N,M    Delete pages
    sign <file> --output <f> --signature <img>Add signature
    fill-form <file> --output <f> --field K=V Fill form fields
    compare <file1> <file2>                   Compare PDFs
    to-a <file> --output <f>                  Convert to PDF/A

Image Commands:
    convert <file> --output <file>            Convert format
    resize <file> --output <f> [--width N]    Resize
    compress <file> --output <f> [--quality 70] Compress
    crop <file> --output <f> --left N --top N --right N --bottom N Crop
    rotate <file> --output <f> [--angle 90]   Rotate
    flip <file> --output <f> [--direction h|v] Flip
    text <file> --output <f> --text <string>  Text overlay
    border <file> --output <f> [--width 10]   Add border
    merge <imgs...> --output <file>           Merge images
    blur <file> --output <f> [--radius 5]     Blur
    ocr <file>                                OCR text
    info <file>                               Image info

Audio Commands:
    convert <file> --output <file>            Convert format
    trim <file> --output <f> --start N        Trim audio
    fade <file> --output <f>                  Fade in/out
    speed <file> --output <f> [--factor 1.5]  Change speed
    info <file>                               Audio info

Video Commands:
    convert <file> --output <file>            Convert format
    trim <file> --output <f> --start N        Trim video
    compress <file> --output <f>              Compress video
    to-gif <file> --output <file>             Video → GIF
    info <file>                               Video info

Office Commands:
    to-markdown <file> [--output <file>]      Office → Markdown
    to-pdf <file> --output <file>             Office → PDF

Examples:
    media-tools pdf merge a.pdf b.pdf --output merged.pdf
    media-tools image rotate photo.jpg --output rotated.jpg --angle 90
    media-tools image ocr scan.png
    media-tools pdf watermark doc.pdf --output marked.pdf --text "CONFIDENTIAL"
    media-tools pdf compare original.pdf modified.pdf
"""


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(HELP)
        return 0

    category = args[0].lower()
    command = args[1].lower() if len(args) > 1 else ""
    key = (category, command)

    if key not in COMMANDS:
        print(f"Unknown command: {category} {command}", file=sys.stderr)
        print(HELP, file=sys.stderr)
        return 1

    cmd_args = args[2:] if len(args) > 2 else []
    try:
        result = COMMANDS[key](cmd_args)
    except Exception as exc:
        result = _error(str(exc))

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
