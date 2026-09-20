"""Shared validation, logging, and error helpers."""

from __future__ import annotations

import logging
import os
import secrets
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger("media_tools")


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger for the media-tools package."""
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
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


def stash_return(input_path: str, returns_dir: str = "_returns") -> tuple[str, str]:
    """Copy the original into a `_returns/` stash dir. Copy, never move.

    The stash dir defaults to `_returns/` next to the input file. The stashed
    copy is named `<stem>__<ticket><suffix>` where ticket is 8 hex chars.
    Returns (ticket_id, stash_path). Raises OSError if the copy fails —
    callers must abort the destructive op in that case.
    """
    src = Path(input_path)
    dest_dir = Path(returns_dir) if Path(returns_dir).is_absolute() else src.parent / returns_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    ticket = secrets.token_hex(4)
    dest = dest_dir / f"{src.stem}__{ticket}{src.suffix}"
    shutil.copy2(str(src), str(dest))
    logger.info("Stashed original %s → %s (ticket %s)", input_path, dest, ticket)
    return ticket, str(dest)


def returns_reclaim(ticket_or_path: str, output: str | None = None, search_dir: str = "_returns") -> str:
    """Restore a stashed original by ticket ID or stash path. Copy, never move."""
    candidate = Path(ticket_or_path)
    if candidate.is_file():
        stash = candidate
    else:
        base = Path(search_dir)
        if not base.is_absolute():
            base = Path.cwd() / base
        matches = sorted(base.glob(f"*{ticket_or_path}*")) if base.is_dir() else []
        files = [m for m in matches if m.is_file()]
        if not files:
            return f"Error: no stashed file matches ticket {ticket_or_path!r} in {base}"
        stash = files[0]

    if output:
        err = validate_output_dir(output)
        if err:
            return err
        dest = Path(output)
    else:
        # Original name = stem before the "__<ticket>" separator, same suffix.
        stem = stash.stem
        orig_stem = stem.split("__")[0] if "__" in stem else stem
        dest = stash.parent.parent / f"{orig_stem}{stash.suffix}"
        if dest.exists():
            return f"Error: {dest} already exists; pass an output path to restore elsewhere or overwrite deliberately"

    try:
        shutil.copy2(str(stash), str(dest))
    except OSError as exc:
        logger.error("reclaim failed: %s", exc)
        return f"Error: {exc}"
    logger.info("Reclaimed %s → %s", stash, dest)
    return f"Reclaimed → {dest} (from {stash})"


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
    img_width: int,
    img_height: int,
    left: int,
    top: int,
    right: int,
    bottom: int,
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
