"""Run: .venv/bin/python tests/check_image.py"""

import json
import tempfile
from pathlib import Path

from PIL import Image

from media_tools.tools.image import ImageToolkit

with tempfile.TemporaryDirectory() as d:
    src = str(Path(d) / "grad.png")
    grad = Image.new("RGB", (64, 64))
    px = grad.load()
    assert px is not None
    for x in range(64):
        for y in range(64):
            px[x, y] = (x * 4, y * 4, (x + y) * 2)
    grad.save(src)

    gray = str(Path(d) / "gray.png")
    assert ImageToolkit.grayscale(src, gray).startswith("Grayscale"), gray
    assert Image.open(gray).mode == "L"

    sharp = str(Path(d) / "sharp.png")
    assert ImageToolkit.sharpen(src, sharp).startswith("Sharpened"), sharp
    assert Path(sharp).read_bytes() != Path(src).read_bytes()

    circ = str(Path(d) / "circ.png")
    assert ImageToolkit.circle_crop(src, circ).startswith("Circle crop"), circ
    cimg = Image.open(circ).convert("RGBA")
    assert cimg.mode == "RGBA"
    corner = cimg.getpixel((0, 0))
    assert isinstance(corner, tuple) and corner[3] == 0  # transparent corner
    center = cimg.getpixel((32, 32))
    assert isinstance(center, tuple) and center[3] == 255  # opaque center

    tiles_dir = str(Path(d) / "tiles")
    res = json.loads(ImageToolkit.split_tiles(src, tiles_dir, rows=2, cols=3))
    assert res["tiles"] == 6, res
    assert len(res["files"]) == 6, res
    for f in res["files"]:
        assert Path(str(f["path"])).is_file(), f
    assert Path(str(res["manifest"])).is_file()
    red = str(Path(d) / "red.png")
    assert ImageToolkit.redact(src, red, 10, 10, 30, 30).startswith("Redacted"), red
    rimg = Image.open(red).convert("RGB")
    assert rimg.getpixel((20, 20)) == (0, 0, 0)
    assert rimg.getpixel((40, 40)) == grad.getpixel((40, 40))  # outside untouched
    pix = str(Path(d) / "pix.png")
    assert ImageToolkit.redact(src, pix, 0, 0, 64, 64, mode="pixelate").startswith("Redacted"), pix
    assert ImageToolkit.redact(src, pix, 50, 50, 10, 10).startswith("Error"), "empty area"
    assert ImageToolkit.redact(src, pix, 0, 0, 5, 5, mode="nope").startswith("Error"), "bad mode"
    from PIL import Image as _I

    cut = str(Path(d) / "cut.png")
    half = _I.new("RGBA", (8, 8), (255, 0, 0, 255))
    half.paste((0, 0, 0, 0), (0, 0, 4, 8))
    half.save(cut)
    fb = str(Path(d) / "fb.png")
    assert ImageToolkit.fill_background(cut, fb, "lightblue").startswith("Background"), fb
    assert _I.open(fb).getpixel((1, 1)) == (173, 216, 230, 255)
    assert _I.open(fb).getpixel((6, 1)) == (255, 0, 0, 255)
    assert ImageToolkit.fill_background(cut, fb, "notacolour").startswith("Error"), "bad colour"
print("ok")
