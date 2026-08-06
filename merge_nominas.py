#!/usr/bin/env python3
"""
Juntar archivos de nómina (PDF, JPEG, DOCX) en un solo PDF con marca de agua.
"""

import glob
import os
import sys
from pathlib import Path

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter

# ── Rutas ──────────────────────────────────────────────────────────────
DOWNLOADS = Path.home() / "Downloads"
OUTPUT = DOWNLOADS / "NOMINAS_COMPLETADAS_2026.pdf"

# Colores para la marca de agua (gris muy suave)
WATERMARK_COLOR = HexColor("#cccccc")
WATERMARK_COLOR_DIM = HexColor("#e0e0e0")

# ── Utilidades ─────────────────────────────────────────────────────────

def add_watermark_to_pdf_bytes(pdf_bytes: bytes, label: str = "CONFIDENCIAL") -> bytes:
    """Añade marca de agua diagonal semitransparente a todas las páginas."""
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    page_w, page_h = A4  # width, height

    for page in reader.pages:
        # Crear overlay con marca de agua
        packet = BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=A4)
        c.setFillColor(WATERMARK_COLOR_DIM, alpha=0.3)
        c.setFont("Helvetica-Bold", 48)
        c.saveState()
        c.translate(page_w / 2, page_h / 2)
        c.rotate(-45)
        c.drawCentredString(0, 0, label)
        c.restoreState()
        c.save()

        watermark_pdf = PdfReader(BytesIO(packet.getvalue()))
        page.merge_page(watermark_pdf.pages[0])
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def image_to_pdf_bytes(img_path: Path) -> bytes:
    """Convierte una imagen JPEG/PNG a PDF tamaño A4 (fit to page)."""
    from PIL import Image

    packet = BytesIO()
    img = Image.open(img_path)
    img.load()

    # Escalar para encajar en A4 manteniendo aspect ratio
    pdf_w, pdf_h = A4
    img_w, img_h = img.size

    scale = min(pdf_w / img_w, pdf_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    c = rl_canvas.Canvas(packet, pagesize=A4)
    c.setFillColor(HexColor("#ffffff"))
    c.rect(0, 0, pdf_w, pdf_h, fill=1, stroke=0)  # fondo blanco
    c.drawImage(
        ImageReader(img_resized),
        (pdf_w - new_w) / 2,
        (pdf_h - new_h) / 2,
        width=new_w,
        height=new_h,
    )
    c.save()
    return packet.getvalue()


def docx_to_pdf_bytes(docx_path: Path) -> bytes:
    """Convierte un DOCX a PDF básico (texto + formato simple)."""
    from docx import Document

    doc = Document(docx_path)

    packet = BytesIO()
    c = rl_canvas.Canvas(packet, pagesize=A4)
    pdf_w, pdf_h = A4
    margin = 20 * mm
    y = pdf_h - margin

    c.setFont("Helvetica", 10)

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            y -= 5 * mm
            continue

        # Ajustar tamaño según estilo
        style = para.style.name.lower() if para.style else ""
        if "title" in style or "heading 1" in style:
            c.setFont("Helvetica-Bold", 16)
        elif "heading 2" in style:
            c.setFont("Helvetica-Bold", 13)
        elif "heading 3" in style:
            c.setFont("Helvetica-Bold", 11)
        else:
            c.setFont("Helvetica", 10)

        # Word wrap manual
        max_chars = int((pdf_w - 2 * margin) / 5.8)  # ~5.8pt por char en 10pt font
        lines = []
        for line in text.split("\n"):
            while len(line) > max_chars:
                split_at = line.rfind(" ", 0, max_chars)
                if split_at == -1:
                    split_at = max_chars
                lines.append(line[:split_at])
                line = line[split_at:].lstrip()
            lines.append(line)

        for line in lines:
            if y < margin:
                c.showPage()
                y = pdf_h - margin
                c.setFont("Helvetica", 10)
            c.drawString(margin, y, line)
            y -= 4.5 * mm

    c.save()
    return packet.getvalue()


# ── Procesamiento ──────────────────────────────────────────────────────

def process_file(filepath: Path) -> bytes | None:
    """Procesa un archivo y devuelve sus bytes PDF, o None si no es soportado."""
    ext = filepath.suffix.lower()
    try:
        if ext == ".pdf":
            return filepath.read_bytes()
        elif ext in (".jpeg", ".jpg", ".png"):
            return image_to_pdf_bytes(filepath)
        elif ext == ".docx":
            return docx_to_pdf_bytes(filepath)
        else:
            print(f"  ⚠ Ignorado: {filepath.name} (formato no soportado)")
            return None
    except Exception as e:
        print(f"  ✗ Error procesando {filepath.name}: {e}")
        return None


def main():
    # Buscar todos los archivos de nómina
    patterns = [
        "*NOMINA*",
        "*nómina*",
        "*nomina*",
        "*NOMINA*",
    ]

    files = []
    for pat in patterns:
        files.extend(glob.glob(str(DOWNLOADS / pat)))

    # Filtrar duplicados y ordenar
    files = sorted(set(files), key=lambda p: Path(p).name.lower())

    if not files:
        print("No se encontraron archivos de nómina en Descargas.")
        sys.exit(1)

    print(f"📄 Encontrados {len(files)} archivos de nómina:\n")
    for f in files:
        print(f"   • {Path(f).name}")
    print()

    # Procesar cada archivo
    all_pdf_bytes = []
    for filepath in files:
        print(f"  → Procesando: {Path(filepath).name}...")
        result = process_file(Path(filepath))
        if result:
            all_pdf_bytes.append(result)

    if not all_pdf_bytes:
        print("Error: Ningún archivo pudo ser procesado.")
        sys.exit(1)

    # Unir todos los PDFs
    print(f"\n  🔗 Uniendo {len(all_pdf_bytes)} PDFs...")
    final_writer = PdfWriter()

    for i, pdf_bytes in enumerate(all_pdf_bytes):
        reader = PdfReader(BytesIO(pdf_bytes))
        for page in reader.pages:
            final_writer.add_page(page)

    # Guardar sin marca de agua primero
    final_bytes = BytesIO()
    final_writer.write(final_bytes)
    final_bytes.seek(0)

    # Añadir marca de agua a TODO el documento
    print("  💧 Añadiendo marca de agua...")
    output_bytes = add_watermark_to_pdf_bytes(final_bytes.getvalue(), "CONFIDENCIAL")

    # Escribir archivo final
    OUTPUT.write_bytes(output_bytes)
    file_size_kb = len(output_bytes) / 1024

    print(f"\n✅ ¡Listo! Archivo unificado guardado en:\n   {OUTPUT}\n   Tamaño: {file_size_kb:.0f} KB")
    print(f"   Páginas totales: {len(final_writer.pages)}")


if __name__ == "__main__":
    main()
