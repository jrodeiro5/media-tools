"""Milk-run folder sweep: one single-file op across every matching file.

Never writes in place — outputs mirror the input tree under out_dir.
Each file runs in its own try/except: failures are recorded, husks
(0-byte leftovers) deleted, and the sweep continues.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from media_tools.tools.audio import AudioToolkit
from media_tools.tools.image import ImageToolkit
from media_tools.tools.pdf import PDFToolkit
from media_tools.tools.video import VideoToolkit
from media_tools.utils import logger, validate_output_dir

SWEEP_OPS = ("pdf_compress", "image_convert", "image_compress", "audio_convert", "video_compress")


def _run_pdf_compress(src: str, dest: str, kw: dict[str, Any]) -> str:
    return PDFToolkit.compress(src, dest, int(kw.get("quality", 50)))


def _run_image_convert(src: str, dest: str, kw: dict[str, Any]) -> str:
    return ImageToolkit.convert(src, dest, int(kw.get("quality", 85)))


def _run_image_compress(src: str, dest: str, kw: dict[str, Any]) -> str:
    return ImageToolkit.compress(src, dest, int(kw.get("quality", 70)))


def _run_audio_convert(src: str, dest: str, kw: dict[str, Any]) -> str:
    return AudioToolkit.convert(src, dest, str(kw.get("bitrate", "192k")))


def _run_video_compress(src: str, dest: str, kw: dict[str, Any]) -> str:
    if kw.get("crf") is None:
        return VideoToolkit.compress(src, dest)
    return VideoToolkit.compress(src, dest, int(kw["crf"]))


def _same_suffix(src: Path, kw: dict[str, Any]) -> str:
    return src.suffix


def _to_format_suffix(src: Path, kw: dict[str, Any], default: str) -> str:
    return "." + str(kw.get("format", default)).lstrip(".").lower()


_DISPATCH = {
    "pdf_compress": (_run_pdf_compress, _same_suffix),
    "image_convert": (_run_image_convert, lambda s, k: _to_format_suffix(s, k, "png")),
    "image_compress": (_run_image_compress, _same_suffix),
    "audio_convert": (_run_audio_convert, lambda s, k: _to_format_suffix(s, k, "mp3")),
    "video_compress": (_run_video_compress, _same_suffix),
}


def _err(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False)


def sweep(input_dir: str, out_dir: str, op: str, pattern: str = "*", max_files: int = 200, **op_kwargs: Any) -> str:
    """Apply op to every file matching pattern under input_dir, outputs under out_dir."""
    if op not in _DISPATCH:
        return _err(f"unknown op {op!r} — choices: {', '.join(SWEEP_OPS)}")
    if ".." in Path(input_dir).parts:
        return _err(f"input dir contains '..' — path traversal blocked: {input_dir}")
    src_root = Path(input_dir)
    if not src_root.exists():
        return _err(f"input dir does not exist: {input_dir}")
    if not src_root.is_dir():
        return _err(f"input dir is not a directory: {input_dir}")
    if not os.access(str(src_root), os.R_OK):
        return _err(f"input dir is not readable: {input_dir}")
    if not out_dir or not out_dir.strip():
        return _err("output dir is required — sweep never writes in place")
    in_res, out_res = src_root.resolve(), Path(out_dir).resolve()
    if out_res == in_res or out_res.is_relative_to(in_res):
        return _err("output dir must not equal or live inside the input dir")
    err = validate_output_dir(str(out_res))
    if err:
        return _err(err)
    out_res.mkdir(parents=True, exist_ok=True)

    run, suffix_fn = _DISPATCH[op]
    files = sorted(p for p in in_res.rglob(pattern) if p.is_file() and out_res not in p.resolve().parents)
    if len(files) > max_files:
        return _err(f"matched {len(files)} files, above the cap of {max_files} — re-run with a higher max_files")
    ok = failed = skipped = 0
    seen: set[Path] = set()
    manifest: list[dict[str, Any]] = []
    for src in files:
        rel = str(src.relative_to(in_res))
        if src.stat().st_size == 0:
            manifest.append({"file": rel, "status": "skipped", "reason": "zero-byte"})
            skipped += 1
            continue
        dest = out_res / Path(rel).parent / (src.stem + suffix_fn(src, op_kwargs))
        if dest in seen:
            err_msg = f"output name collides with an earlier file: {dest.name}"
            manifest.append({"file": rel, "status": "error", "error": err_msg})
            failed += 1
            continue
        seen.add(dest)
        if validate_output_dir(str(dest)):
            manifest.append({"file": rel, "status": "error", "error": f"unwritable output: {dest}"})
            failed += 1
            continue
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            result = run(str(src), str(dest), op_kwargs)
            if result.lower().startswith("error"):
                msg = result
            elif not (dest.exists() and dest.stat().st_size > 0):
                msg = f"no output produced for {rel}: {result}"
            else:
                msg = ""
            if msg:
                raise RuntimeError(msg)
            manifest.append({"file": rel, "status": "ok", "output": str(dest.relative_to(out_res))})
            ok += 1
        except Exception as exc:
            try:
                if dest.exists() and dest.stat().st_size == 0:
                    dest.unlink()
            except OSError as cleanup_exc:
                logger.debug("husk cleanup failed for %s: %s", dest, cleanup_exc)
            manifest.append({"file": rel, "status": "error", "error": str(exc)})
            failed += 1
    summary: dict[str, Any] = {
        "op": op,
        "files_total": len(files),
        "ok": ok,
        "failed": failed,
        "skipped": skipped,
        "manifest": manifest,
    }
    (out_res / "sweep_manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    return json.dumps(summary, ensure_ascii=False)
