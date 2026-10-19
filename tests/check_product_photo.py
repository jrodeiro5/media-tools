"""Run: python tests/check_product_photo.py

image_product_photo: the object cropped, centred on a square white canvas, with a margin.
"""

import tempfile
from pathlib import Path

from PIL import Image

from media_tools.tools.image import ImageToolkit

with tempfile.TemporaryDirectory() as d:
    # Already cut out (transparent around), so the test needs no background-removal model.
    src = str(Path(d) / "in.png")
    img = Image.new("RGBA", (900, 500), (0, 0, 0, 0))
    img.paste((200, 30, 30, 255), (600, 50, 800, 450))  # a 200x400 object, off-centre
    img.save(src)
    out = str(Path(d) / "out.jpg")
    res = ImageToolkit.product_photo(src, out, size=1000, margin=0.1)
    assert not res.startswith("Error"), res
    o = Image.open(out).convert("RGB")
    assert o.size == (1000, 1000), o.size
    assert o.getpixel((5, 5)) == (255, 255, 255)
    mask = o.convert("L").point(lambda v: 255 if v < 200 else 0)
    bbox = mask.getbbox()
    assert bbox, "no object on the canvas"
    x0, y0, x1, y1 = bbox
    assert abs((x0 + x1) / 2 - 500) <= 3 and abs((y0 + y1) / 2 - 500) <= 3, (x0, y0, x1, y1)  # centred
    assert 795 <= y1 - y0 <= 805, (y0, y1)  # the long side fills the canvas minus 10% each side
    assert abs((x1 - x0) * 2 - (y1 - y0)) <= 6, (x0, x1)  # proportions kept

    res = ImageToolkit.product_photo(src, out, margin=0.6)
    assert res.startswith("Error"), res
print("ok")
