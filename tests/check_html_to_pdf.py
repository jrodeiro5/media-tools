"""Run: .venv/bin/python tests/check_html_to_pdf.py  (needs soffice)"""

import tempfile
from pathlib import Path

from pypdf import PdfReader

from media_tools.tools.pdf import PDFToolkit

HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body { font-family: sans-serif; }
table { border-collapse: collapse; }
th, td { border: 1px solid #333; padding: 6px 12px; }
th { background: #eef; }
</style></head>
<body><h1>Hola html_to_pdf</h1>
<table><tr><th>Nombre</th><th>Valor</th></tr>
<tr><td>Alpha</td><td>1</td></tr>
<tr><td>Beta</td><td>2</td></tr></table>
</body></html>
"""

with tempfile.TemporaryDirectory() as d:
    src, out = str(Path(d) / "table.html"), str(Path(d) / "table.pdf")
    Path(src).write_text(HTML, encoding="utf-8")
    res = PDFToolkit.html_to_pdf(src, out)
    assert not res.startswith("Error"), res
    assert Path(out).exists()
    reader = PdfReader(out)
    assert len(reader.pages) >= 1
    assert "Hola" in (reader.pages[0].extract_text() or "")

    txt = str(Path(d) / "note.txt")
    Path(txt).write_text("not html", encoding="utf-8")
    assert PDFToolkit.html_to_pdf(txt, str(Path(d) / "x.pdf")).startswith("Error")  # local HTML only
    assert "does not exist" in PDFToolkit.html_to_pdf(str(Path(d) / "missing.html"), str(Path(d) / "y.pdf"))
    assert PDFToolkit.html_to_pdf("https://example.com/a.html", str(Path(d) / "z.pdf")).startswith("Error")  # no URLs
print("ok")
