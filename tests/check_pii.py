"""Run: python tests/check_pii.py  (needs the pii extra)"""

import json
import tempfile
from pathlib import Path

import pdfplumber
from reportlab.pdfgen import canvas

from media_tools.tools.pii import PiiToolkit

with tempfile.TemporaryDirectory() as d:
    src, out = str(Path(d) / "in.pdf"), str(Path(d) / "out.pdf")
    c = canvas.Canvas(src)
    c.drawString(100, 700, "DNI 12345678Z NIE X1234567L bad 12345678A")
    c.showPage()
    c.drawString(100, 700, "public page two")
    c.save()

    res = json.loads(PiiToolkit.scan(src))
    assert res["counts"] == {"ES_NIF": 1, "ES_NIE": 1}, res  # wrong check letter is rejected
    assert "12345678Z" not in json.dumps(res)  # raw values never returned

    assert PiiToolkit.redact(src, out).startswith("Redacted"), out
    with pdfplumber.open(out) as pdf:
        assert "12345678Z" not in (pdf.pages[0].extract_text() or "")
        assert "public" in (pdf.pages[1].extract_text() or "")
    assert b"12345678Z" not in Path(out).read_bytes()
print("ok")
