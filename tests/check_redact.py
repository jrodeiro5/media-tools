"""Run: python tests/check_redact.py"""

import tempfile
from pathlib import Path

import pdfplumber
from reportlab.pdfgen import canvas

from media_tools.tools.pdf import PDFToolkit

with tempfile.TemporaryDirectory() as d:
    src, out = str(Path(d) / "in.pdf"), str(Path(d) / "out.pdf")
    c = canvas.Canvas(src)
    c.drawString(100, 700, "TOPSECRET page one")
    c.showPage()
    c.drawString(100, 700, "public page two")
    c.save()
    res = PDFToolkit.redact(src, out, text_patterns=["TOPSECRET"])
    assert res.startswith("Redacted"), res
    with pdfplumber.open(out) as pdf:
        assert len(pdf.pages) == 2
        assert "TOPSECRET" not in (pdf.pages[0].extract_text() or "")
        assert "public" in (pdf.pages[1].extract_text() or "")
    assert b"TOPSECRET" not in Path(out).read_bytes()

    pix = str(Path(d) / "pix.pdf")
    res = PDFToolkit.redact(
        src, pix, rect_areas=[{"page": 0, "x": 90, "y": 120, "width": 200, "height": 40}], mode="pixelate"
    )
    assert res.startswith("Redacted"), res
    with pdfplumber.open(pix) as pdf:
        assert "TOPSECRET" not in (pdf.pages[0].extract_text() or ""), "pixelate must remove the text too"
        assert "public" in (pdf.pages[1].extract_text() or "")

    # A name of several words is one match, found case-insensitively, and the count is reported.
    contract, red = str(Path(d) / "contract.pdf"), str(Path(d) / "red.pdf")
    c = canvas.Canvas(contract)
    c.drawString(72, 760, "Arrendador: Juan Perez Garcia, DNI 12345678Z")
    c.drawString(72, 740, "Arrendataria: Ana Lopez")
    c.save()
    res = PDFToolkit.redact(contract, red, text_patterns=["juan perez", "12345678Z"])
    assert res.startswith("Redacted") and "juan perez: 1" in res and "12345678Z: 1" in res, res
    with pdfplumber.open(red) as pdf:
        assert "Juan" not in (pdf.pages[0].extract_text() or "")

    # A pattern that is not in the PDF is an error and nothing is written, never a silent success.
    missing = str(Path(d) / "missing.pdf")
    res = PDFToolkit.redact(contract, missing, text_patterns=["Juan Perez", "Nadie Existe"])
    assert res.startswith("Error") and "Nadie Existe" in res, res
    assert not Path(missing).exists()
print("ok")
