"""Run: .venv/bin/python tests/check_pdf_repair.py (fixtures under /tmp only)."""

import json
import subprocess
import tempfile
from pathlib import Path

import pypdf
from reportlab.pdfgen import canvas

from media_tools.tools.pdf import PDFToolkit

PAGES = 3


def _make_valid(path: str) -> None:
    c = canvas.Canvas(path)
    for i in range(1, PAGES + 1):
        c.drawString(100, 700, f"repair fixture page {i}")
        c.showPage()
    c.save()


def _dd(in_path: str, out_path: str, count: int) -> None:
    cmd = ["dd", f"if={in_path}", f"of={out_path}", "bs=1", f"count={count}"]
    subprocess.run(cmd, check=True, capture_output=True)


rows: list[tuple[str, str]] = []
with tempfile.TemporaryDirectory(prefix="repair_") as d:
    valid = str(Path(d) / "valid.pdf")
    _make_valid(valid)
    valid_bytes = Path(valid).read_bytes()
    xref_off = valid_bytes.index(b"xref")

    # healthy baseline: all pages kept, never in place
    healthy_out = str(Path(d) / "healthy.pdf")
    res = PDFToolkit.repair(valid, healthy_out)
    doc = json.loads(res)
    assert doc["pages_kept"] == PAGES and doc["pages_dropped"] == 0, res
    assert len(pypdf.PdfReader(healthy_out).pages) == PAGES
    assert "repair fixture page 1" in pypdf.PdfReader(healthy_out).pages[0].extract_text()
    rows.append(("valid", f"kept={doc['pages_kept']} dropped={doc['pages_dropped']}"))

    # in-place refusal
    assert PDFToolkit.repair(valid, valid).startswith("Error:"), "must refuse in-place"

    cases = {
        # xref + trailer + startxref gone
        "trunc-xref": xref_off,
        # last 300 bytes (%%EOF + tail of trailer) gone
        "cut-eof": len(valid_bytes) - 300,
    }
    for name, count in cases.items():
        bad = str(Path(d) / f"{name}.pdf")
        _dd(valid, bad, count)
        bad_bytes = Path(bad).read_bytes()
        out = str(Path(d) / f"{name}.repaired.pdf")
        res = PDFToolkit.repair(bad, out)
        assert Path(bad).read_bytes() == bad_bytes, f"{name}: input mutated"
        if res.startswith("Error:"):
            assert "pdf_salvage" in res, f"{name}: error must suggest pdf_salvage: {res}"
            rows.append((name, "Error→pdf_salvage"))
        else:
            doc = json.loads(res)
            assert doc["pages_kept"] >= 1, f"{name}: silent zero: {res}"
            assert set(doc) == {"output", "pages_kept", "pages_dropped", "objects_stripped", "errors"}, res
            got = pypdf.PdfReader(doc["output"]).pages
            assert len(got) == doc["pages_kept"], res
            rows.append(
                (name, f"kept={doc['pages_kept']} dropped={doc['pages_dropped']} stripped={doc['objects_stripped']}")
            )

for name, detail in rows:
    print(f"{name:10s} {detail}")
print("ok")
