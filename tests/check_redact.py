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
print("ok")
