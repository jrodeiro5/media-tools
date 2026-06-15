"""Shared validation, logging, and error helpers."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger("media_tools")


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger for the media-tools package."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addHandler(handler)


def validate_input(path: str, label: str = "input") -> str | None:
    """Return an error string if the input path is invalid, else None.

    Checks:
    - Path is not empty
    - Path does not escape (no '..' components)
    - Path exists and is a file (or is a URL)
    """
    if not path or not path.strip():
        return f"{label} path is empty"

    # Allow URLs through (firecrawl, etc.)
    if path.startswith(("http://", "https://")):
        return None

    # Path traversal check
    parts = Path(path).parts
    if ".." in parts:
        return f"{label} path contains '..' — path traversal blocked: {path}"

    p = Path(path)
    if not p.exists():
        return f"{label} path does not exist: {path}"
    if not p.is_file():
        return f"{label} path is not a file: {path}"
    if not os.access(path, os.R_OK):
        return f"{label} path is not readable: {path}"

    return None


def validate_output_dir(path: str, label: str = "output") -> str | None:
    """Return an error string if the output directory is unwritable, else None."""
    p = Path(path)
    parent = p.parent if p.suffix else p

    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return f"cannot create output directory {parent}: {exc}"

    if not os.access(str(parent), os.W_OK):
        return f"output directory is not writable: {parent}"

    return None


def safe_basename(path: str) -> str:
    """Extract basename after stripping any parent components for safety."""
    return Path(path).name


def _subprocess_with_logging(cmd: list[str], description: str) -> tuple[str, bool]:
    """Run a subprocess command with logging. Returns (result_string, success)."""
    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.error("%s failed (rc=%d): %s", description, result.returncode, stderr)
        return f"Error: {stderr}", False
    logger.info("%s", description)
    return description, True


def _validate_crop_bounds(
    img_width: int, img_height: int,
    left: int, top: int, right: int, bottom: int,
) -> str | None:
    """Validate crop coordinates against image dimensions."""
    if left < 0 or top < 0 or right < 0 or bottom < 0:
        return "crop coordinates cannot be negative"
    if left >= right:
        return f"left ({left}) must be less than right ({right})"
    if top >= bottom:
        return f"top ({top}) must be less than bottom ({bottom})"
    if right > img_width:
        return f"right ({right}) exceeds image width ({img_width})"
    if bottom > img_height:
        return f"bottom ({bottom}) exceeds image height ({img_height})"
    return None



