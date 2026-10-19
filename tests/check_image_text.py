"""Run: python tests/check_image_text.py

image_text honours font_size on Linux too (no macOS font paths), and draws Spanish accents.
"""

import tempfile
from pathlib import Path

from PIL import Image

from media_tools.tools.image import ImageToolkit

with tempfile.TemporaryDirectory() as d:
    src = str(Path(d) / "in.png")
    Image.new("RGB", (800, 300), "white").save(src)
    heights = {}
    for size in (20, 80):
        out = str(Path(d) / f"out{size}.png")
        res = ImageToolkit.text_overlay(src, out, "Señal ÁÉ", font_size=size, color="#000000", stroke_width=0)
        assert not res.startswith("Error"), res
        dark = Image.open(out).convert("L").point(lambda v: 255 if v < 128 else 0)
        box = dark.getbbox()
        assert box, f"no text drawn at size {size}"
        heights[size] = box[3] - box[1]
    assert heights[80] > 3 * heights[20], f"font_size ignored: {heights}"
print("ok")
