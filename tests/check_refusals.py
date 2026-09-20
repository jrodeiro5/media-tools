"""Run: .venv/bin/python tests/check_refusals.py"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pypdf
from reportlab.pdfgen import canvas

import media_tools.tools.pdf as pdf_mod
from media_tools.refusals import REGISTRY, missing_binary
from media_tools.tools.office import OfficeToolkit
from media_tools.tools.pdf import PDFToolkit

# 1. E_OVERWRITE_BLOCKED — string identical, ticket inspectable.
with tempfile.TemporaryDirectory() as d:
    src = str(Path(d) / "a.docx")
    subprocess.run(
        [shutil.which("officecli") or "officecli", "create", src],
        check=True,
        capture_output=True,
    )
    res = OfficeToolkit.edit(src, src, "[]")
    assert res == "Error: output must differ from input; edits are never in place", res
    assert isinstance(res, str)
    assert res.ticket.code == "E_OVERWRITE_BLOCKED", res.ticket  # type: ignore[attr-defined]
    assert res.ticket.reason == res, res.ticket  # type: ignore[attr-defined]
    assert res.ticket.fix_hint and res.ticket.remedy, res.ticket  # type: ignore[attr-defined]
    assert res.to_dict()["code"] == "E_OVERWRITE_BLOCKED"  # type: ignore[attr-defined]

# 2. E_ENCRYPTED_PDF — live encrypted PDF through the wired pdf_to_markdown path.
with tempfile.TemporaryDirectory() as d:
    plain, locked = str(Path(d) / "plain.pdf"), str(Path(d) / "locked.pdf")
    c = canvas.Canvas(plain)
    c.drawString(100, 700, "secret content")
    c.save()
    writer = pypdf.PdfWriter()
    for page in pypdf.PdfReader(plain).pages:
        writer.add_page(page)
    writer.encrypt("s3cret-pw")
    with open(locked, "wb") as f:
        writer.write(f)
    res = PDFToolkit.pdf_to_markdown(locked)
    assert res.startswith("Error:"), res
    assert str(res) == res.ticket.reason, res.ticket  # type: ignore[attr-defined]
    assert res.ticket.code == "E_ENCRYPTED_PDF", res.ticket  # type: ignore[attr-defined]
    assert res.ticket.fix_hint and res.ticket.remedy, res.ticket  # type: ignore[attr-defined]

# 3. E_MISSING_BINARY — gs FileNotFoundError path in pdf_to_a (mocked).
with tempfile.TemporaryDirectory() as d:
    src, out = str(Path(d) / "in.pdf"), str(Path(d) / "out.pdf")
    c = canvas.Canvas(src)
    c.drawString(100, 700, "hi")
    c.save()
    with patch.object(pdf_mod, "_subprocess_with_logging", side_effect=FileNotFoundError("gs")):
        res = PDFToolkit.pdf_to_a(src, out)
    assert res == "Error: Ghostscript (gs) not found. Install with: brew install ghostscript", res
    assert res.ticket.code == "E_MISSING_BINARY", res.ticket  # type: ignore[attr-defined]
    assert "gs" in res.ticket.remedy, res.ticket  # type: ignore[attr-defined]
    assert "brew install ghostscript" in res.ticket.fix_hint, res.ticket  # type: ignore[attr-defined]
    assert "apt-get" in res.ticket.fix_hint, res.ticket  # type: ignore[attr-defined]

# Direct constructor keeps the exact gs string too.
direct = missing_binary("Error: Ghostscript (gs) not found. Install with: brew install ghostscript", binary="gs")
assert str(direct) == "Error: Ghostscript (gs) not found. Install with: brew install ghostscript"

assert set(REGISTRY) == {"E_OVERWRITE_BLOCKED", "E_ENCRYPTED_PDF", "E_MISSING_BINARY"}
assert json.dumps(direct.to_dict())  # dict-serializable for future agents
print("ok")
