"""Run: python tests/check_pdf_overlay.py

Page numbers and watermarks land on each page's own box, whatever its size, origin or rotation.
"""

import tempfile
from pathlib import Path

import pdfplumber
import pypdf
from reportlab.pdfgen import canvas

from media_tools.tools.pdf import PDFToolkit

with tempfile.TemporaryDirectory() as d:
    src = str(Path(d) / "in.pdf")
    c = canvas.Canvas(src)
    c.setPageSize((792, 612))  # Letter, landscape
    c.drawString(72, 300, "landscape")
    c.showPage()
    c.setPageSize((595, 842))  # A4, to be shown rotated
    c.drawString(72, 400, "rotated")
    c.showPage()
    c.setPageSize((400, 300))  # small page whose box does not start at 0,0
    c.drawString(150, 150, "offset")
    c.save()
    reader, writer = pypdf.PdfReader(src), pypdf.PdfWriter()
    for i, src_page in enumerate(reader.pages):
        if i == 1:
            src_page.rotate(90)
        if i == 2:
            src_page.mediabox.lower_left = (100, 50)
            src_page.mediabox.upper_right = (400, 300)
        writer.add_page(src_page)
    prepared = str(Path(d) / "prepared.pdf")
    writer.write(prepared)

    numbered = str(Path(d) / "numbered.pdf")
    res = PDFToolkit.add_page_numbers(prepared, numbered)
    assert res.startswith("Page numbers"), res
    with pdfplumber.open(numbered) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            label = f"Página {n} de 3"
            hits = page.search(label, regex=False)
            assert hits, f"{label} missing on page {n}: {page.extract_text()!r}"
            box = hits[0]
            # Inside the visible page and in its bottom band, centred.
            assert 0 <= box["x0"] and box["x1"] <= page.width, (n, box, page.width)
            assert 0 < page.height - box["bottom"] < 50, (n, box, page.height)  # 15 mm from the bottom
            assert abs((box["x0"] + box["x1"]) / 2 - page.width / 2) < 40, (n, box, page.width)

    res = PDFToolkit.add_page_numbers(prepared, numbered, format_str="Hoja {page} / {pages}")
    assert res.startswith("Error") and "{page}" in res and "{total}" in res, res

    marked = str(Path(d) / "marked.pdf")
    res = PDFToolkit.watermark(prepared, marked, text="BORRADOR", angle=0)
    assert res.startswith("Watermark"), res
    with pdfplumber.open(marked) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            hits = page.search("BORRADOR", regex=False)
            assert hits, f"watermark missing on page {n}"
            cx = (hits[0]["x0"] + hits[0]["x1"]) / 2
            cy = (hits[0]["top"] + hits[0]["bottom"]) / 2
            assert abs(cx - page.width / 2) < 20 and abs(cy - page.height / 2) < 30, (
                n,
                hits[0],
                page.width,
                page.height,
            )
print("ok")
