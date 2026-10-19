"""Run: python tests/check_pdf_pages_and_metadata.py

pdf_rotate on chosen pages, pdf_crop, and image_strip_metadata (orientation kept, GPS gone).
"""

import tempfile
from pathlib import Path

import pypdf
from PIL import Image
from reportlab.pdfgen import canvas

from media_tools.tools.image import ImageToolkit
from media_tools.tools.pdf import PDFToolkit

with tempfile.TemporaryDirectory() as d:
    src = str(Path(d) / "in.pdf")
    c = canvas.Canvas(src)
    for i in range(3):
        c.drawString(72, 700, f"page {i + 1}")
        c.showPage()
    c.save()
    out = str(Path(d) / "rot.pdf")
    assert PDFToolkit.rotate(src, out, 90, pages=[2]).startswith("Rotated")
    assert [p.rotation for p in pypdf.PdfReader(out).pages] == [0, 90, 0]
    assert PDFToolkit.rotate(src, out, 90, pages=[7]).startswith("Error")
    assert PDFToolkit.crop(src, out, left=50, right=50).startswith("Cropped")
    w0 = float(pypdf.PdfReader(src).pages[0].mediabox.width)
    assert float(pypdf.PdfReader(out).pages[0].mediabox.width) == w0 - 100

    photo = str(Path(d) / "photo.jpg")
    img = Image.new("RGB", (40, 20), "red")
    exif = img.getexif()
    exif[0x0112] = 6  # Orientation: rotate 90 CW to display
    exif[0x8825] = {2: (40.0, 25.0, 0.0)}  # GPSInfo
    img.save(photo, exif=exif)
    clean = str(Path(d) / "clean.jpg")
    res = ImageToolkit.strip_metadata(photo, clean)
    assert res.startswith("Metadata removed") and "none" not in res, res
    out_img = Image.open(clean)
    assert not out_img.getexif(), dict(out_img.getexif())
    assert out_img.size == (20, 40), out_img.size  # orientation applied to the pixels
print("ok")
