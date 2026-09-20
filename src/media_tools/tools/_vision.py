"""Shared cv2 model/data helpers: download-on-first-run cache + Haar face utils.

Models are never vendored into git. First run downloads to
~/.cache/media-tools/models (rembg precedent); every file is SHA256-pinned
and re-downloaded when the hash mismatches. No cached file + no network =
callers return an offline Error, never an exception.

Licenses (verified 2026-09-20):
- haarcascade_frontalface_default.xml from opencv/opencv data/haarcascades:
  embedded Intel BSD-style grant (redistribute with notice, no endorsement,
  as-is disclaimer) — no NC, no copyleft. Repo LICENSE is Apache-2.0.
- FSRCNN-small .pb from Saafke/FSRCNN_Tensorflow (repo LICENSE Apache-2.0).
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from cv2.typing import MatLike

MODEL_CACHE = Path.home() / ".cache" / "media-tools" / "models"

# key: (url, sha256, filename)
ASSETS: dict[str, tuple[str, str, str]] = {
    "fsrcnn_x2": (
        "https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN-small_x2.pb",
        "429e4793d049c1ae16ddbbc322fd11c3c08831c0c20137390b4d098976a2b0d9",
        "FSRCNN-small_x2.pb",
    ),
    "fsrcnn_x3": (
        "https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN-small_x3.pb",
        "58e72d0c4231b8e754180e787d7348f45ae6230ee3c5af7dc12b558467f593f7",
        "FSRCNN-small_x3.pb",
    ),
    "haar_frontalface": (
        "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/haarcascade_frontalface_default.xml",
        "0f7d4527844eb514d4a4948e822da90fbb16a34a0bbbbc6adc6498747a5aafb0",
        "haarcascade_frontalface_default.xml",
    ),
}


def ensure_asset(key: str) -> str:
    """Return the cached path for key, downloading it first when needed.

    Raises RuntimeError with an "Error: ..."-prefixed message (offline or
    hash mismatch) so toolkit wrappers can return it directly.
    """
    url, sha256, filename = ASSETS[key]
    MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    dest = MODEL_CACHE / filename
    if dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest() == sha256:
        return str(dest)
    try:
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        urllib.request.urlretrieve(url, str(dest))  # nosec B310 -- url from hardcoded ASSETS table
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Error: could not download {filename} (offline?): {exc}") from exc
    if hashlib.sha256(dest.read_bytes()).hexdigest() != sha256:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Error: hash mismatch for {filename} (re-downloaded, still bad)")
    return str(dest)


def detect_faces(
    gray: MatLike,
    xml_path: str,
    scale_factor: float = 1.1,
    min_neighbors: int = 5,
) -> list[tuple[int, int, int, int]]:
    """Haar frontal-face boxes as (x, y, w, h). Raises RuntimeError on load failure."""
    import cv2

    cascade = cv2.CascadeClassifier(xml_path)
    if cascade.empty():
        raise RuntimeError(f"Error: could not load Haar cascade: {xml_path}")
    found = cascade.detectMultiScale(gray, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=(30, 30))
    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in found]


def obscure_boxes(img: np.ndarray, boxes: list[tuple[int, int, int, int]], mode: str) -> None:
    """Pixelate (default) or Gaussian-blur each box in place (BGR ndarray)."""
    import cv2

    h_img, w_img = img.shape[:2]
    for x, y, w, h in boxes:
        x2, y2 = min(w_img, x + w), min(h_img, y + h)
        x, y = max(0, x), max(0, y)
        if x2 <= x or y2 <= y:
            continue
        roi = img[y:y2, x:x2]
        if mode == "pixelate":
            sw, sh = max(1, (x2 - x) // 16), max(1, (y2 - y) // 16)
            small = cv2.resize(roi, (sw, sh), interpolation=cv2.INTER_LINEAR)
            img[y:y2, x:x2] = cv2.resize(small, (x2 - x, y2 - y), interpolation=cv2.INTER_NEAREST)
        else:
            k = max(3, (min(x2 - x, y2 - y) // 5) | 1)  # odd ksize for GaussianBlur
            img[y:y2, x:x2] = cv2.GaussianBlur(roi, (k, k), 0)


def iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """Intersection-over-union of two (x, y, w, h) boxes."""
    ax2, ay2, bx2, by2 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw, ih = min(ax2, bx2) - max(a[0], b[0]), min(ay2, by2) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    return inter / (a[2] * a[3] + b[2] * b[3] - inter)


def track_boxes(
    tracked: list[dict],
    fresh: list[tuple[int, int, int, int]],
    iou_threshold: float = 0.3,
    max_missed: int = 2,
) -> list[dict]:
    """Greedy IoU match of fresh detections onto tracked boxes.

    Each tracked entry is {"box": (x, y, w, h), "missed": n}. Matches update
    the box and reset missed; unmatched tracked age out after max_missed
    detection rounds; unmatched fresh start new tracks.
    """
    claimed: set[int] = set()
    for entry in tracked:
        best, best_j = -1, 0.0
        for i, box in enumerate(fresh):
            if i in claimed:
                continue
            j = iou(entry["box"], box)
            if j > best_j:
                best, best_j = i, j
        if best >= 0 and best_j >= iou_threshold:
            entry["box"], entry["missed"] = fresh[best], 0
            claimed.add(best)
        else:
            entry["missed"] += 1
    alive = [e for e in tracked if e["missed"] <= max_missed]
    for i, box in enumerate(fresh):
        if i not in claimed:
            alive.append({"box": box, "missed": 0})
    return alive
