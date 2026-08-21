"""Agent-native CLI for media-tools.

Usage:
    media-tools pdf merge f1.pdf f2.pdf --output merged.pdf
    media-tools image rotate photo.jpg --output rotated.jpg --angle 90
    media-tools image ocr scan.png
    media-tools --help
    media-tools pdf --help
    media-tools pdf merge --help
"""

from __future__ import annotations

import argparse
import json

from media_tools.tools.audio import AudioToolkit
from media_tools.tools.image import ImageToolkit
from media_tools.tools.office import OfficeToolkit
from media_tools.tools.pdf import PDFToolkit
from media_tools.tools.video import VideoToolkit


def _result(value: str) -> str:
    try:
        return json.dumps(json.loads(value), ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"result": value}, ensure_ascii=False)


def _error(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False)


# ── Handlers: one line each, pull args from the parsed namespace ──


def _pdf_merge(ns):
    return PDFToolkit.merge(ns.input, ns.output)


def _pdf_split(ns):
    return PDFToolkit.split(ns.input, ns.pages, ns.output)


def _pdf_compress(ns):
    return PDFToolkit.compress(ns.input, ns.output, ns.quality)


def _pdf_rotate(ns):
    return PDFToolkit.rotate(ns.input, ns.output, ns.angle)


def _pdf_extract_text(ns):
    return PDFToolkit.extract_text(ns.input, ns.output)


def _pdf_extract_images(ns):
    return PDFToolkit.extract_images(ns.input, ns.output, ns.dpi)


def _pdf_to_markdown(ns):
    return PDFToolkit.pdf_to_markdown(ns.input, ns.output)


def _pdf_watermark(ns):
    return PDFToolkit.watermark(ns.input, ns.output, ns.text, ns.image, ns.opacity, ns.angle)


def _pdf_page_numbers(ns):
    return PDFToolkit.add_page_numbers(ns.input, ns.output, ns.position, ns.format)


def _pdf_protect(ns):
    return PDFToolkit.protect(ns.input, ns.output, ns.password)


def _pdf_unlock(ns):
    return PDFToolkit.unlock(ns.input, ns.output, ns.password)


def _pdf_images_to_pdf(ns):
    return PDFToolkit.images_to_pdf(ns.input, ns.output, quality=ns.quality)


def _pdf_reorder(ns):
    return PDFToolkit.reorder_pages(ns.input, ns.output, ns.pages)


def _pdf_delete(ns):
    return PDFToolkit.delete_pages(ns.input, ns.output, ns.pages)


def _pdf_sign(ns):
    return PDFToolkit.sign(ns.input, ns.output, ns.signature, ns.page, *ns.pos)


def _pdf_fill_form(ns):
    return PDFToolkit.fill_form(ns.input, ns.output, dict(f.split("=", 1) for f in ns.field))


def _pdf_compare(ns):
    return PDFToolkit.compare(ns.input, ns.other)


def _pdf_to_a(ns):
    return PDFToolkit.pdf_to_a(ns.input, ns.output, ns.version)


def _image_convert(ns):
    return ImageToolkit.convert(ns.input, ns.output, ns.quality)


def _image_resize(ns):
    return ImageToolkit.resize(ns.input, ns.output, ns.width, ns.height, ns.percent)


def _image_compress(ns):
    return ImageToolkit.compress(ns.input, ns.output, ns.quality)


def _image_crop(ns):
    return ImageToolkit.crop(ns.input, ns.output, ns.left, ns.top, ns.right, ns.bottom)


def _image_rotate(ns):
    return ImageToolkit.rotate(ns.input, ns.output, ns.angle)


def _image_flip(ns):
    return ImageToolkit.flip(ns.input, ns.output, ns.direction)


def _image_text(ns):
    return ImageToolkit.text_overlay(ns.input, ns.output, ns.text, ns.position, ns.font_size, ns.color, ns.stroke)


def _image_border(ns):
    return ImageToolkit.border(ns.input, ns.output, ns.width, ns.color)


def _image_merge(ns):
    return ImageToolkit.merge(ns.input, ns.output, ns.direction)


def _image_blur(ns):
    return ImageToolkit.blur(ns.input, ns.output, ns.radius)


def _image_ocr(ns):
    return ImageToolkit.ocr(ns.input)


def _image_info(ns):
    return ImageToolkit.info(ns.input)


def _audio_convert(ns):
    return AudioToolkit.convert(ns.input, ns.output)


def _audio_trim(ns):
    return AudioToolkit.trim(ns.input, ns.output, ns.start, ns.end or 0)


def _audio_fade(ns):
    return AudioToolkit.fade(ns.input, ns.output)


def _audio_speed(ns):
    return AudioToolkit.speed(ns.input, ns.output, ns.factor)


def _audio_info(ns):
    return AudioToolkit.info(ns.input)


def _video_convert(ns):
    return VideoToolkit.convert(ns.input, ns.output)


def _video_trim(ns):
    return VideoToolkit.trim(ns.input, ns.output, ns.start, end=ns.end)


def _video_compress(ns):
    return VideoToolkit.compress(ns.input, ns.output)


def _video_to_gif(ns):
    return VideoToolkit.to_gif(ns.input, ns.output, ns.width, ns.fps)


def _video_info(ns):
    return VideoToolkit.probe(ns.input)


def _office_to_markdown(ns):
    return OfficeToolkit.to_markdown(ns.input, ns.output)


def _office_to_pdf(ns):
    return OfficeToolkit.to_pdf(ns.input, ns.output)


def _pages_list(value: str) -> list[int]:
    return [int(p) for p in value.split(",")]


def _pos_tuple(value: str) -> list[float]:
    parts = [float(p) for p in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--pos requires 4 comma-separated values: x,y,width,height")
    return parts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="media-tools", description="Agent-native media processing CLI")
    categories = parser.add_subparsers(dest="category", required=True)

    def add(cat_parsers, name, handler, *arg_specs):
        sub = cat_parsers.add_parser(name)
        for flags, kwargs in arg_specs:
            sub.add_argument(*flags, **kwargs)
        sub.set_defaults(handler=handler)

    REQ_OUT = (("--output",), {"required": True})
    OPT_OUT: tuple[tuple[str, ...], dict[str, object]] = (("--output",), {})
    IN_ONE: tuple[tuple[str, ...], dict[str, object]] = (("input",), {})
    IN_MANY = (("input",), {"nargs": "+"})

    pdf = categories.add_parser("pdf").add_subparsers(dest="command", required=True)
    add(pdf, "merge", _pdf_merge, IN_MANY, REQ_OUT)
    add(pdf, "split", _pdf_split, IN_ONE, REQ_OUT, (("--pages",), {"required": True}))
    add(pdf, "compress", _pdf_compress, IN_ONE, REQ_OUT, (("--quality",), {"type": int, "default": 50}))
    add(pdf, "rotate", _pdf_rotate, IN_ONE, REQ_OUT, (("--angle",), {"type": int, "default": 90}))
    add(pdf, "extract-text", _pdf_extract_text, IN_ONE, OPT_OUT)
    add(pdf, "extract-images", _pdf_extract_images, IN_ONE, REQ_OUT, (("--dpi",), {"type": int, "default": 150}))
    add(pdf, "to-markdown", _pdf_to_markdown, IN_ONE, OPT_OUT)
    add(
        pdf,
        "watermark",
        _pdf_watermark,
        IN_ONE,
        REQ_OUT,
        (("--text",), {}),
        (("--image",), {}),
        (("--opacity",), {"type": float, "default": 0.3}),
        (("--angle",), {"type": int, "default": 45}),
    )
    add(
        pdf,
        "page-numbers",
        _pdf_page_numbers,
        IN_ONE,
        REQ_OUT,
        (("--position",), {"default": "bottom-center"}),
        (("--format",), {"default": "Page {page}"}),
    )
    add(pdf, "protect", _pdf_protect, IN_ONE, REQ_OUT, (("--password",), {"required": True}))
    add(pdf, "unlock", _pdf_unlock, IN_ONE, REQ_OUT, (("--password",), {"required": True}))
    add(pdf, "images-to-pdf", _pdf_images_to_pdf, IN_MANY, REQ_OUT, (("--quality",), {"type": int, "default": 85}))
    add(pdf, "reorder", _pdf_reorder, IN_ONE, REQ_OUT, (("--pages",), {"required": True, "type": _pages_list}))
    add(pdf, "delete", _pdf_delete, IN_ONE, REQ_OUT, (("--pages",), {"required": True, "type": _pages_list}))
    add(
        pdf,
        "sign",
        _pdf_sign,
        IN_ONE,
        REQ_OUT,
        (("--signature",), {"required": True}),
        (("--page",), {"type": int, "default": 1}),
        (("--pos",), {"type": _pos_tuple, "default": [50.0, 50.0, 150.0, 50.0]}),
    )
    add(
        pdf,
        "fill-form",
        _pdf_fill_form,
        IN_ONE,
        REQ_OUT,
        (("--field",), {"action": "append", "required": True, "help": "NAME=VALUE, repeatable"}),
    )
    add(pdf, "compare", _pdf_compare, IN_ONE, (("other",), {}))
    add(pdf, "to-a", _pdf_to_a, IN_ONE, REQ_OUT, (("--version",), {"default": "1b"}))

    image = categories.add_parser("image").add_subparsers(dest="command", required=True)
    add(image, "convert", _image_convert, IN_ONE, REQ_OUT, (("--quality",), {"type": int, "default": 85}))
    add(
        image,
        "resize",
        _image_resize,
        IN_ONE,
        REQ_OUT,
        (("--width",), {"type": int}),
        (("--height",), {"type": int}),
        (("--percent",), {"type": int}),
    )
    add(image, "compress", _image_compress, IN_ONE, REQ_OUT, (("--quality",), {"type": int, "default": 70}))
    add(
        image,
        "crop",
        _image_crop,
        IN_ONE,
        REQ_OUT,
        (("--left",), {"type": int, "required": True}),
        (("--top",), {"type": int, "required": True}),
        (("--right",), {"type": int, "required": True}),
        (("--bottom",), {"type": int, "required": True}),
    )
    add(image, "rotate", _image_rotate, IN_ONE, REQ_OUT, (("--angle",), {"type": int, "default": 90}))
    add(
        image,
        "flip",
        _image_flip,
        IN_ONE,
        REQ_OUT,
        (("--direction",), {"default": "horizontal", "choices": ["horizontal", "vertical"]}),
    )
    add(
        image,
        "text",
        _image_text,
        IN_ONE,
        REQ_OUT,
        (("--text",), {"required": True}),
        (("--position",), {"default": "bottom-right"}),
        (("--font-size",), {"type": int, "default": 24, "dest": "font_size"}),
        (("--color",), {"default": "#ffffff"}),
        (("--stroke",), {"default": "#000000"}),
    )
    add(
        image,
        "border",
        _image_border,
        IN_ONE,
        REQ_OUT,
        (("--width",), {"type": int, "default": 10}),
        (("--color",), {"default": "#ffffff"}),
    )
    add(
        image,
        "merge",
        _image_merge,
        IN_MANY,
        REQ_OUT,
        (("--direction",), {"default": "horizontal", "choices": ["horizontal", "vertical"]}),
    )
    add(image, "blur", _image_blur, IN_ONE, REQ_OUT, (("--radius",), {"type": float, "default": 5.0}))
    add(image, "ocr", _image_ocr, IN_ONE)
    add(image, "info", _image_info, IN_ONE)

    audio = categories.add_parser("audio").add_subparsers(dest="command", required=True)
    add(audio, "convert", _audio_convert, IN_ONE, REQ_OUT)
    add(
        audio,
        "trim",
        _audio_trim,
        IN_ONE,
        REQ_OUT,
        (("--start",), {"type": int, "required": True, "help": "start ms"}),
        (("--end",), {"type": int, "help": "end ms"}),
    )
    add(audio, "fade", _audio_fade, IN_ONE, REQ_OUT)
    add(audio, "speed", _audio_speed, IN_ONE, REQ_OUT, (("--factor",), {"type": float, "default": 1.5}))
    add(audio, "info", _audio_info, IN_ONE)

    video = categories.add_parser("video").add_subparsers(dest="command", required=True)
    add(video, "convert", _video_convert, IN_ONE, REQ_OUT)
    add(
        video,
        "trim",
        _video_trim,
        IN_ONE,
        REQ_OUT,
        (("--start",), {"required": True, "help": "HH:MM:SS"}),
        (("--end",), {"help": "HH:MM:SS"}),
    )
    add(video, "compress", _video_compress, IN_ONE, REQ_OUT)
    add(
        video,
        "to-gif",
        _video_to_gif,
        IN_ONE,
        REQ_OUT,
        (("--width",), {"type": int, "default": 480}),
        (("--fps",), {"type": int, "default": 10}),
    )
    add(video, "info", _video_info, IN_ONE)

    office = categories.add_parser("office").add_subparsers(dest="command", required=True)
    add(office, "to-markdown", _office_to_markdown, IN_ONE, OPT_OUT)
    add(office, "to-pdf", _office_to_pdf, IN_ONE, REQ_OUT)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    try:
        result = ns.handler(ns)
    except Exception as exc:
        print(_error(str(exc)))
        return 1
    print(_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
