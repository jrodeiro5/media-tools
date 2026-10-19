"""Run: python tests/check_pdf_ocr.py  (needs tesseract with the Spanish data, as in the image)

pdf_ocr turns an image-only page into a searchable one and leaves pages with text alone.
"""

import io
import tempfile
from pathlib import Path

import pdfplumber
import pypdf
import pypdfium2 as pdfium
from reportlab.pdfgen import canvas

from media_tools.tools.pdf import PDFToolkit

with tempfile.TemporaryDirectory() as d:
    text_pdf = str(Path(d) / "text.pdf")
    c = canvas.Canvas(text_pdf)
    c.setFont("Helvetica", 28)
    c.drawString(72, 700, "Contrato de arrendamiento")
    c.showPage()
    c.setFont("Helvetica", 12)
    c.drawString(72, 700, "Esta segunda pagina ya tiene su capa de texto y no se toca nunca.")
    c.save()
    # Page 1 as a scan: rendered to an image, no text layer. Page 2 keeps its text.
    scan = pdfium.PdfDocument(text_pdf)[0].render(scale=200 / 72).to_pil().convert("RGB")
    buf = io.BytesIO()
    scan.save(buf, format="PDF", resolution=200)
    writer = pypdf.PdfWriter()
    writer.add_page(pypdf.PdfReader(buf).pages[0])
    writer.add_page(pypdf.PdfReader(text_pdf).pages[1])
    src = str(Path(d) / "scan.pdf")
    writer.write(src)
    with pdfplumber.open(src) as pdf:
        assert not (pdf.pages[0].extract_text() or "").strip()

    out = str(Path(d) / "ocr.pdf")
    res = PDFToolkit.ocr_pdf(src, out)
    assert res.startswith("Searchable PDF (1 pages"), res
    with pdfplumber.open(out) as pdf:
        assert len(pdf.pages) == 2
        assert "arrendamiento" in (pdf.pages[0].extract_text() or ""), pdf.pages[0].extract_text()
        assert abs(pdf.pages[0].width - 595.27) < 2, pdf.pages[0].width  # A4 kept
        assert "segunda pagina" in (pdf.pages[1].extract_text() or "")
    assert PDFToolkit.ocr_pdf(text_pdf, out, min_chars=10).startswith("Error"), "a PDF with text needs no OCR"
print("ok")
