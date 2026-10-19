"""Run: python tests/check_pdf_compress.py

pdf_compress shrinks embedded photos, keeps the text, and never returns a bigger file.
"""

import os
import tempfile
from pathlib import Path

import pdfplumber
from PIL import Image
from reportlab.pdfgen import canvas

from media_tools.tools.pdf import PDFToolkit

with tempfile.TemporaryDirectory() as d:
    photo = Path(d) / "photo.png"
    # Smooth gradient plus a little noise: a photo-like image that PNG stores badly and JPEG well.
    img = Image.radial_gradient("L").resize((2400, 1800)).convert("RGB")
    noise = Image.effect_noise((2400, 1800), 12).convert("RGB")
    Image.blend(img, noise, 0.15).save(photo)
    src = str(Path(d) / "in.pdf")
    c = canvas.Canvas(src)
    c.drawString(72, 800, "Factura 2026-117")
    c.drawImage(str(photo), 72, 300, width=450, height=340)
    c.save()

    out = str(Path(d) / "out.pdf")
    res = PDFToolkit.compress(src, out)
    assert not res.startswith("Error"), res
    before, after = os.path.getsize(src), os.path.getsize(out)
    assert after < before * 0.6, (before, after, res)
    with pdfplumber.open(out) as pdf:
        assert "Factura 2026-117" in (pdf.pages[0].extract_text() or "")
        assert len(pdf.pages[0].images) == 1

    # Nothing to gain: the original is kept, never a bigger file.
    text_only = str(Path(d) / "text.pdf")
    c = canvas.Canvas(text_only)
    c.drawString(72, 800, "solo texto")
    c.save()
    out2 = str(Path(d) / "out2.pdf")
    res = PDFToolkit.compress(text_only, out2)
    assert not res.startswith("Error"), res
    assert os.path.getsize(out2) <= os.path.getsize(text_only), res
print("ok")
