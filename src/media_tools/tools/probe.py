"""Universal media probe — sniff a file, report metadata, rank applicable tools.

Read-only and local-first: magic bytes + extension decide the kind, then the
already-required backends do the measuring (ffprobe for audio/video, pypdf for
PDF, PIL for images, zipfile for Office). Zero new binaries or dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from media_tools.utils import logger, validate_input

# NOTE (rot risk): TOOLS_BY_KIND is hand-maintained; regenerate from server.py @mcp.tool names if tools change.

TOOLS_BY_KIND: dict[str, list[tuple[str, str]]] = {
    "pdf": [
        ("pdf_extract_text", "read the selectable text"),
        ("pdf_to_markdown", "convert the text to Markdown"),
        ("document_summarize", "summarize the document with the LLM"),
        ("document_qa", "ask questions about the document"),
        ("document_translate", "translate the document"),
        ("pdf_extract_tables", "dump embedded tables to CSV files"),
        ("pdf_tables_to_csv", "combine all tables into one CSV"),
        ("pdf_extract_images", "render pages as PNG images"),
        ("pdf_extract_structured", "extract text with bounding boxes"),
        ("pdf_extract_screenshots", "render pages as screenshots"),
        ("pii_scan", "find Spanish/EU identifiers (masked previews)"),
        ("pii_redact", "black out PII in the PDF"),
        ("pdf_info", "page count, title, author, encryption"),
        ("pdf_compress", "shrink the file size"),
        ("pdf_merge", "combine with other PDFs"),
        ("pdf_split", "split out page ranges"),
        ("pdf_rotate", "rotate all pages"),
        ("pdf_reorder_pages", "reorder pages"),
        ("pdf_delete_pages", "drop pages (original stashed)"),
        ("pdf_watermark", "stamp text or image over pages"),
        ("pdf_page_numbers", "add page numbers"),
        ("pdf_protect", "add a password"),
        ("pdf_unlock", "remove the password"),
        ("pdf_sign", "place a signature"),
        ("pdf_fill_form", "fill AcroForm fields"),
        ("pdf_compare", "diff against another PDF"),
        ("pdf_to_a", "convert to archival PDF/A"),
        ("pdf_to_docx", "convert to DOCX via LibreOffice"),
        ("pdf_redact", "black out text patterns or areas"),
        ("pdf_salvage", "recover text from a corrupt file"),
        ("pdf_repair", "rebuild a viewable PDF from a corrupt file"),
        ("images_to_pdf", "rebuild a PDF from page renders"),
        ("md_to_branded_pdf", "rebuild a branded PDF from extracted Markdown"),
        ("image_ocr", "OCR page renders (for scanned pages)"),
        ("returns_reclaim", "restore a stashed original"),
        ("text_to_speech", "read the extracted text aloud"),
        ("batch_sweep", "repeat one op over a folder of PDFs"),
    ],
    "image": [
        ("image_info", "format, mode and dimensions"),
        ("image_convert", "convert to another format"),
        ("image_resize", "resize by pixels or percent"),
        ("image_compress", "shrink the file size"),
        ("image_crop", "crop a region"),
        ("image_rotate", "rotate the image"),
        ("image_flip", "flip horizontal or vertical"),
        ("image_text", "overlay text"),
        ("image_border", "add a border"),
        ("image_merge", "merge with other images"),
        ("image_watermark", "stamp a watermark"),
        ("image_collage", "tile into a collage"),
        ("image_blur", "blur regions"),
        ("image_ocr", "read text in the image"),
        ("image_remove_background", "cut out the background"),
        ("image_apply_brand", "apply the brand kit"),
        ("image_to_video", "animate into a video"),
        ("image_export_social_pack", "export 9:16 / 1:1 / 16:9 variants"),
        ("image_grayscale", "convert to grayscale"),
        ("image_sharpen", "sharpen the image"),
        ("image_circle_crop", "circle crop with transparency"),
        ("image_split_tiles", "split into tiles plus a manifest"),
        ("image_upscale", "upscale 2x/3x with FSRCNN"),
        ("image_blur_faces", "obscure faces"),
        ("images_to_pdf", "bundle into a PDF"),
        ("gif_to_mp4", "convert a GIF to MP4 (only if animated)"),
        ("batch_sweep", "repeat one op over a folder of images"),
    ],
    "audio": [
        ("audio_info", "duration, channels, sample rate"),
        ("audio_convert", "convert to another format"),
        ("audio_trim", "cut a segment"),
        ("audio_fade", "add fades"),
        ("audio_speed", "change tempo"),
        ("audio_merge", "concatenate with other audio"),
        ("audio_normalize", "normalize loudness"),
        ("audio_chunk_silence", "split on silence"),
        ("audio_transcribe", "speech to text"),
        ("audio_transcribe_chunks", "transcribe long audio in chunks"),
        ("audio_to_srt", "format transcript segments as SubRip"),
        ("audio_pad_to_duration", "pad with silence to a duration"),
        ("audio_to_video", "render with a static image as video"),
        ("batch_sweep", "repeat one op over a folder of audio"),
    ],
    "video": [
        ("video_probe", "full codec, resolution and bitrate detail"),
        ("video_convert", "convert to another format"),
        ("video_trim", "cut a segment"),
        ("video_compress", "shrink with CRF"),
        ("video_to_gif", "export a segment as GIF"),
        ("video_extract_audio", "rip the audio track"),
        ("video_merge", "concatenate with other videos"),
        ("video_crop", "crop a region"),
        ("video_rotate", "rotate the video"),
        ("video_resize", "resize the video"),
        ("video_watermark", "stamp a watermark"),
        ("video_reverse", "play backwards"),
        ("video_mute", "drop the audio track"),
        ("video_speed", "change playback speed"),
        ("video_transcribe", "transcribe speech to SRT (no burn)"),
        ("video_subtitle_burn", "burn in subtitles"),
        ("video_extract_frames", "dump frames as images"),
        ("video_thumbnail", "grab a still"),
        ("video_contact_sheet", "grid preview plus a manifest"),
        ("video_export_social_pack", "export 9:16 / 1:1 / 16:9 MP4s"),
        ("video_chroma_cut", "remove a green screen"),
        ("video_object_erase", "erase a boxed region"),
        ("video_blur_faces", "obscure faces"),
        ("batch_sweep", "repeat one op over a folder of videos"),
    ],
    "office": [
        ("office_inspect", "peek at the document structure"),
        ("office_to_markdown", "convert to Markdown"),
        ("office_to_pdf", "convert via LibreOffice"),
        ("office_edit", "edit cells or paragraphs into a new file, never in place"),
        ("document_summarize", "summarize with the LLM"),
        ("document_qa", "ask questions about it"),
        ("document_translate", "translate it"),
        ("pii_scan", "find identifiers in exported text"),
        ("text_to_speech", "read exported text aloud"),
        ("batch_sweep", "repeat one op over a folder of docs"),
    ],
    "unknown": [
        ("document_summarize", "summarize it if readable"),
        ("document_qa", "ask questions if readable"),
        ("document_translate", "translate it if readable"),
        ("pii_scan", "scan it if text-like"),
        ("text_to_speech", "speak it if text-like"),
        ("url_to_markdown", "refetch from its source URL instead"),
        ("html_to_pdf", "render it as PDF (only if HTML)"),
        ("md_to_branded_pdf", "render it as a branded PDF (only if Markdown)"),
        ("batch_sweep", "run one op over a folder of similar files"),
    ],
}

_EXT_FALLBACK: dict[str, tuple[str, str]] = {
    ".pdf": ("application/pdf", "pdf"),
    ".png": ("image/png", "image"),
    ".jpg": ("image/jpeg", "image"),
    ".jpeg": ("image/jpeg", "image"),
    ".webp": ("image/webp", "image"),
    ".gif": ("image/gif", "image"),
    ".bmp": ("image/bmp", "image"),
    ".tif": ("image/tiff", "image"),
    ".tiff": ("image/tiff", "image"),
    ".ico": ("image/x-icon", "image"),
    ".heic": ("image/heic", "image"),
    ".heif": ("image/heif", "image"),
    ".avif": ("image/avif", "image"),
    ".wav": ("audio/wav", "audio"),
    ".mp3": ("audio/mpeg", "audio"),
    ".flac": ("audio/flac", "audio"),
    ".ogg": ("audio/ogg", "audio"),
    ".oga": ("audio/ogg", "audio"),
    ".opus": ("audio/opus", "audio"),
    ".m4a": ("audio/mp4", "audio"),
    ".aac": ("audio/aac", "audio"),
    ".wma": ("audio/x-ms-wma", "audio"),
    ".mp4": ("video/mp4", "video"),
    ".m4v": ("video/mp4", "video"),
    ".mov": ("video/quicktime", "video"),
    ".mkv": ("video/x-matroska", "video"),
    ".avi": ("video/x-msvideo", "video"),
    ".webm": ("video/webm", "video"),
    ".docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "office"),
    ".xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "office"),
    ".pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "office"),
    ".doc": ("application/msword", "office"),
    ".xls": ("application/vnd.ms-excel", "office"),
    ".ppt": ("application/vnd.ms-powerpoint", "office"),
    ".md": ("text/markdown", "unknown"),
    ".markdown": ("text/markdown", "unknown"),
    ".html": ("text/html", "unknown"),
    ".htm": ("text/html", "unknown"),
    ".txt": ("text/plain", "unknown"),
}

_FTYP_BRANDS: dict[str, tuple[str, str]] = {
    "isom": ("video/mp4", "video"),
    "mp41": ("video/mp4", "video"),
    "mp42": ("video/mp4", "video"),
    "avc1": ("video/mp4", "video"),
    "qt": ("video/quicktime", "video"),
    "M4A": ("audio/mp4", "audio"),
    "heic": ("image/heic", "image"),
    "heix": ("image/heic", "image"),
    "avif": ("image/avif", "image"),
    "mif1": ("image/heif", "image"),
}


def _sniff(path: str) -> tuple[str, str]:
    """Return (mime, kind) from magic bytes, falling back to the extension."""
    with open(path, "rb") as fh:
        head = fh.read(16)
    ext = Path(path).suffix.lower()

    if head.startswith(b"%PDF"):
        return "application/pdf", "pdf"
    if head.startswith(b"\x89PNG"):
        return "image/png", "image"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "image"
    if head.startswith(b"GIF8"):
        return "image/gif", "image"
    if head.startswith(b"BM"):
        return "image/bmp", "image"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff", "image"
    if head.startswith(b"\x00\x00\x01\x00"):
        return "image/x-icon", "image"
    if head.startswith(b"fLaC"):
        return "audio/flac", "audio"
    if head.startswith(b"OggS"):
        return "audio/ogg", "audio"
    if head.startswith(b"ID3") or head.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
        return "audio/mpeg", "audio"
    if head.startswith((b"\xff\xf1", b"\xff\xf9")):
        return "audio/aac", "audio"
    if head.startswith(b"RIFF") and len(head) >= 12:
        form = head[8:12]
        if form == b"WAVE":
            return "audio/wav", "audio"
        if form == b"AVI":
            return "video/x-msvideo", "video"
        if form == b"WEBP":
            return "image/webp", "image"
    if head[4:8] == b"ftyp" and len(head) >= 12:
        brand = head[8:12].decode("ascii", errors="replace")
        if brand in _FTYP_BRANDS:
            return _FTYP_BRANDS[brand]
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        if ext == ".webm":
            return "video/webm", "video"
        return "video/x-matroska", "video"
    if head.startswith(b"PK\x03\x04"):
        subtype = _office_subtype(path)
        if subtype:
            mime = _EXT_FALLBACK.get("." + subtype, ("application/zip", "office"))[0]
            return mime, "office"
        return "application/zip", "unknown"
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return _EXT_FALLBACK.get(ext, ("application/msword", "office"))

    return _EXT_FALLBACK.get(ext, ("application/octet-stream", "unknown"))


def _office_subtype(path: str) -> str | None:
    """Return docx/xlsx/pptx for an OOXML zip, else None."""
    try:
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
    except zipfile.BadZipFile:
        return None
    if "word/document.xml" in names:
        return "docx"
    if "xl/workbook.xml" in names:
        return "xlsx"
    if "ppt/presentation.xml" in names:
        return "pptx"
    return None


def _ffprobe_streams(path: str) -> tuple[list[dict[str, object]], float | None] | None:
    """Return (stream summaries, duration) via ffprobe, or None if unavailable."""
    if shutil.which("ffprobe") is None:
        logger.warning("ffprobe not found — skipping stream detail")
        return None
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        logger.error("ffprobe failed: %s", exc)
        return None
    if result.returncode != 0:
        logger.error("ffprobe failed: %s", result.stderr.strip())
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        logger.error("ffprobe output unparseable: %s", exc)
        return None
    streams: list[dict[str, object]] = []
    for s in data.get("streams", []):
        summary: dict[str, object] = {"codec_type": s.get("codec_type"), "codec_name": s.get("codec_name")}
        for key in ("width", "height", "sample_rate", "channels"):
            if s.get(key) is not None:
                summary[key] = s.get(key)
        streams.append(summary)
    duration: float | None = None
    raw = data.get("format", {}).get("duration")
    try:
        duration = float(raw) if raw is not None else None
    except (TypeError, ValueError):
        duration = None
    return streams, duration


def _pdf_meta(path: str) -> tuple[int | None, int | None, int | None, bool, bool]:
    """Return (pages, width, height, scanned, corrupt) via pypdf (pdfinfo is not a required binary)."""
    try:
        import pypdf
    except ImportError:
        logger.warning("pypdf not installed — skipping PDF detail")
        return None, None, None, False, False
    try:
        reader = pypdf.PdfReader(path)
        pages = len(reader.pages)
        width = height = None
        if pages:
            box = reader.pages[0].mediabox
            width, height = int(box.width), int(box.height)
        text = "".join((reader.pages[i].extract_text() or "") for i in range(min(pages, 3)))
        scanned = len(text.strip()) < 20
        return pages, width, height, scanned, False
    except Exception as exc:
        logger.error("pypdf failed on %s: %s", path, exc)
        return None, None, None, False, True


def _image_meta(path: str) -> tuple[int | None, int | None, bool]:
    """Return (width, height, has_alpha) via PIL."""
    try:
        from PIL import Image
    except ImportError:
        logger.warning("PIL not installed — skipping image detail")
        return None, None, False
    try:
        with Image.open(path) as img:
            alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
            return img.width, img.height, bool(alpha)
    except Exception as exc:
        logger.error("PIL failed on %s: %s", path, exc)
        return None, None, False


def _ranked(kind: str, ext: str, scanned: bool, corrupt: bool) -> list[dict[str, str]]:
    """Order TOOLS_BY_KIND for this file, promoting conditional best-fits first."""
    names = [name for name, _ in TOOLS_BY_KIND[kind]]
    front: list[tuple[str, str]] = []
    if kind == "pdf" and corrupt:
        front = [
            ("pdf_repair", "this file failed to parse — rebuild a viewable PDF"),
            ("pdf_salvage", "this file failed to parse — salvage readable pages"),
        ]
    elif kind == "pdf" and scanned:
        front = [
            ("image_ocr", "no selectable text found — OCR the page renders"),
            ("pdf_extract_structured", "OCR with bounding boxes (ocr=True)"),
            ("pdf_extract_screenshots", "render pages to feed the OCR"),
        ]
    elif kind == "image" and ext == ".gif":
        front = [("gif_to_mp4", "animate this GIF as MP4")]
    elif kind == "unknown" and ext in (".md", ".markdown"):
        front = [("md_to_branded_pdf", "render this Markdown as a branded PDF")]
    elif kind == "unknown" and ext in (".html", ".htm"):
        front = [("html_to_pdf", "render this HTML as PDF")]
    by_name = dict(TOOLS_BY_KIND[kind])
    ordered = front + [(n, by_name[n]) for n in names if n not in {n for n, _ in front}]
    return [{"name": name, "why": why} for name, why in ordered]


class ProbeToolkit:
    name = "probe"

    @staticmethod
    def probe(input_path: str) -> str:
        """Sniff a local media file and rank the media_tools that apply. Returns JSON."""
        err = validate_input(input_path)
        if err:
            return err

        mime, kind = _sniff(input_path)
        ext = Path(input_path).suffix.lower()
        streams: list[dict[str, object]] = []
        width = height = None
        duration = None
        pages = None
        has_audio = False
        has_alpha = False
        extra: dict[str, object] = {}

        if kind in ("audio", "video"):
            probed = _ffprobe_streams(input_path)
            if probed is not None:
                streams, duration = probed
                video = next((s for s in streams if s.get("codec_type") == "video"), None)
                audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
                if video is not None:
                    w, h = video.get("width"), video.get("height")
                    width = int(w) if isinstance(w, int) else None
                    height = int(h) if isinstance(h, int) else None
                has_audio = audio is not None or kind == "audio"
        elif kind == "pdf":
            pages, width, height, scanned, corrupt = _pdf_meta(input_path)
            extra["scanned"] = scanned
            if corrupt:
                extra["corrupt"] = True
        elif kind == "image":
            width, height, has_alpha = _image_meta(input_path)
        elif kind == "office":
            subtype = _office_subtype(input_path)
            if subtype:
                extra["subtype"] = subtype

        scanned = bool(extra.get("scanned", False))
        corrupt = bool(extra.get("corrupt", False))
        report: dict[str, object] = {
            "mime": mime,
            "kind": kind,
            "streams": streams,
            "width": width,
            "height": height,
            "duration": duration,
            "pages": pages,
            "has_audio": has_audio,
            "has_alpha": has_alpha,
            **extra,
            "tools": _ranked(kind, ext, scanned, corrupt),
        }
        logger.info("Probed %s as %s (%s)", input_path, kind, mime)
        return json.dumps(report, ensure_ascii=False)
