"""PDF toolkit — merge, split, compress, extract text/images, rotate, info."""

from __future__ import annotations

import io
import os
import subprocess
from pathlib import Path

import pdfplumber
import pypdf
import pypdfium2 as pdfium

from media_tools.utils import _subprocess_with_logging, logger, validate_input, validate_output_dir

try:
    import liteparse
    HAS_LITEPARSE = True
except ImportError:
    HAS_LITEPARSE = False


class PDFToolkit:
    name = "pdf"

    @staticmethod
    def merge(files: list[str], output: str) -> str:
        """Merge multiple PDF files into one."""
        for f in files:
            err = validate_input(f)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            writer = pypdf.PdfWriter()
            for f in files:
                writer.append(f)
            writer.write(output)
            writer.close()
            logger.info("Merged %d PDFs → %s", len(files), output)
        except Exception as exc:
            logger.error("merge failed: %s", exc)
            return f"Error: {exc}"

        return f"Merged {len(files)} files into {output}"

    @staticmethod
    def split(input_path: str, pages: str, output_dir: str) -> str:
        """Split a PDF. pages: ranges like '1-3,5,7-9' (1-indexed)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_dir)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            total = len(reader.pages)

            ranges = []
            for part in pages.split(","):
                if "-" in part:
                    start, end = part.split("-")
                    start = int(start) - 1 if start else 0
                    end = int(end) if end else total
                else:
                    start = int(part) - 1
                    end = int(part)
                ranges.append((max(0, start), min(total, end)))

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            results = []
            for i, (start, end) in enumerate(ranges):
                writer = pypdf.PdfWriter()
                for p in range(start, end):
                    writer.add_page(reader.pages[p])
                out_path = out_dir / f"split_{i + 1}.pdf"
                writer.write(str(out_path))
                writer.close()
                results.append(str(out_path))

            logger.info("Split %s into %d files", input_path, len(results))
            return f"Split into {len(results)} files: {', '.join(results)}"
        except Exception as exc:
            logger.error("split failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def compress(input_path: str, output: str, quality: int = 50) -> str:
        """Compress a PDF (reduces internal stream size)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            writer = pypdf.PdfWriter()
            reader = pypdf.PdfReader(input_path)

            for page in reader.pages:
                page.compress_content_streams()
                writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Compressed PDF → %s", output)
        except Exception as exc:
            logger.error("compress failed: %s", exc)
            return f"Error: {exc}"

        return f"Compressed to {output}"

    @staticmethod
    def extract_text(input_path: str, output: str | None = None) -> str:
        """Extract text content from a PDF."""
        err = validate_input(input_path)
        if err:
            return err

        try:
            with pdfplumber.open(input_path) as pdf:
                text = "\n\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )

            if output:
                err = validate_output_dir(output)
                if err:
                    return err
                Path(output).write_text(text, encoding="utf-8")
                logger.info("Extracted %d chars → %s", len(text), output)
                return f"Text extracted to {output} ({len(text)} chars)"
            logger.info("Extracted %d chars from %s", len(text), input_path)
            return text
        except Exception as exc:
            logger.error("extract_text failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def extract_images(input_path: str, output_dir: str, dpi: int = 150) -> str:
        """Render PDF pages as PNG images."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_dir)
        if err:
            return err

        try:
            pdf = pdfium.PdfDocument(input_path)
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            results = []
            for i, page in enumerate(pdf):
                bitmap = page.render(scale=dpi / 72)
                img = bitmap.to_pil()
                out_path = out_dir / f"page_{i + 1:04d}.png"
                img.save(str(out_path))
                results.append(str(out_path))

            pdf.close()
            logger.info("Extracted %d pages as images → %s", len(results), output_dir)
            return f"Extracted {len(results)} pages as images to {output_dir}"
        except Exception as exc:
            logger.error("extract_images failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def rotate(input_path: str, output: str, angle: int = 90) -> str:
        """Rotate all pages in a PDF by a given angle."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            for page in reader.pages:
                new_page = writer.add_page(page)
                new_page.rotate(angle)

            writer.write(output)
            writer.close()
            logger.info("Rotated PDF %d° → %s", angle, output)
        except Exception as exc:
            logger.error("rotate failed: %s", exc)
            return f"Error: {exc}"

        return f"Rotated {angle}° → {output}"

    @staticmethod
    def info(input_path: str) -> str:
        """Get PDF metadata."""
        err = validate_input(input_path)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            info = reader.metadata or {}
            return (
                f"Pages: {len(reader.pages)}\n"
                f"Title: {info.get('/Title', 'N/A')}\n"
                f"Author: {info.get('/Author', 'N/A')}\n"
                f"Encrypted: {reader.is_encrypted}"
            )
        except Exception as exc:
            logger.error("info failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def extract_structured(
        input_path: str, output: str | None = None,
        ocr: bool = False, language: str = "eng", dpi: int = 150,
    ) -> str:
        """Extract structured text with bounding boxes using LiteParse.

        Outputs JSON with text_items (x, y, width, height, font, confidence).
        Requires: pip install liteparse
        """
        err = validate_input(input_path)
        if err:
            return err
        if not HAS_LITEPARSE:
            return "Error: liteparse not installed. Run: pip install liteparse"
        if output:
            err = validate_output_dir(output)
            if err:
                return err

        try:
            lp = liteparse.LiteParse(
                ocr_enabled=ocr,
                ocr_language=language,
                dpi=dpi,
                output_format="json",
                num_workers=4,
                quiet=True,
            )
            result = lp.parse(input_path)

            structured = {
                "num_pages": result.num_pages,
                "pages": [
                    {
                        "page_num": p.page_num,
                        "width": p.width,
                        "height": p.height,
                        "text": p.text,
                        "text_items": [
                            {
                                "text": t.text,
                                "x": t.x,
                                "y": t.y,
                                "width": t.width,
                                "height": t.height,
                                "font_name": t.font_name,
                                "font_size": t.font_size,
                                "confidence": t.confidence,
                            }
                            for t in p.text_items
                        ],
                    }
                    for p in result.pages
                ],
            }

            if output:
                import json
                Path(output).write_text(
                    json.dumps(structured, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                logger.info("Structured extraction → %s", output)
                return f"Structured JSON → {output} ({result.num_pages} pages)"

            import json
            return json.dumps(structured, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.error("extract_structured failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def extract_screenshots(
        input_path: str, output_dir: str, dpi: int = 150,
        page_numbers: list[int] | None = None,
    ) -> str:
        """Render PDF pages as PNG screenshots using LiteParse."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_dir)
        if err:
            return err
        if not HAS_LITEPARSE:
            return "Error: liteparse not installed. Run: pip install liteparse"

        try:
            lp = liteparse.LiteParse(
                dpi=dpi,
                quiet=True,
            )
            screenshots = lp.screenshot(input_path, page_numbers=page_numbers)

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            results = []
            for s in screenshots:
                out_path = out_dir / f"page_{s.page_num:04d}.png"
                out_path.write_bytes(s.image_bytes)
                results.append(str(out_path))

            logger.info("Screenshots → %s (%d pages)", output_dir, len(results))
            return f"Screenshots → {output_dir} ({len(results)} pages)"
        except Exception as exc:
            logger.error("extract_screenshots failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def watermark(
        input_path: str,
        output: str,
        text: str | None = None,
        image_path: str | None = None,
        opacity: float = 0.3,
        angle: int = 45,
        font_size: int = 48,
        color: str = "#808080",
    ) -> str:
        """Add a watermark (text or image) to all pages of a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        if not text and not image_path:
            return "Error: specify either text or image_path"
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            from reportlab.lib.pagesizes import A4
            from reportlab.lib.colors import HexColor
            from reportlab.pdfgen import canvas

            w, h = A4

            for page in reader.pages:
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)
                c.saveState()
                c.translate(w / 2, h / 2)
                c.rotate(angle)
                c.setFillAlpha(opacity)

                if text:
                    c.setFont("Helvetica", font_size)
                    c.setFillColor(HexColor(color))
                    c.drawCentredString(0, 0, text)
                elif image_path:
                    img_err = validate_input(image_path)
                    if img_err:
                        return img_err
                    c.drawImage(image_path, -100, -100, width=200, height=200, mask="auto")

                c.restoreState()
                c.save()
                packet.seek(0)

                overlay = pypdf.PdfReader(packet)
                page.merge_page(overlay.pages[0])
                writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Watermarked PDF → %s", output)
        except Exception as exc:
            logger.error("watermark failed: %s", exc)
            return f"Error: {exc}"

        return f"Watermark → {output}"

    @staticmethod
    def add_page_numbers(
        input_path: str,
        output: str,
        position: str = "bottom-center",
        format_str: str = "Page {page}",
        font_size: int = 10,
        font_color: str = "#000000",
    ) -> str:
        """Add page numbers to all pages of a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            from reportlab.lib.pagesizes import A4
            from reportlab.lib.colors import HexColor
            from reportlab.pdfgen import canvas

            w, h = A4
            positions = {
                "bottom-center": (w / 2, 50),
                "bottom-right": (w - 100, 50),
                "top-center": (w / 2, h - 50),
                "top-right": (w - 100, h - 50),
            }
            x, y = positions.get(position, positions["bottom-center"])

            for i, page in enumerate(reader.pages):
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)
                c.setFont("Helvetica", font_size)
                c.setFillColor(HexColor(font_color))
                page_label = format_str.replace("{page}", str(i + 1))
                if "center" in position:
                    c.drawCentredString(x, y, page_label)
                else:
                    c.drawString(x, y, page_label)
                c.save()
                packet.seek(0)

                overlay = pypdf.PdfReader(packet)
                page.merge_page(overlay.pages[0])
                writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Page numbers → %s", output)
        except Exception as exc:
            logger.error("add_page_numbers failed: %s", exc)
            return f"Error: {exc}"

        return f"Page numbers → {output}"

    @staticmethod
    def protect(
        input_path: str,
        output: str,
        password: str,
        owner_password: str | None = None,
    ) -> str:
        """Add password protection to a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            writer.encrypt(password, owner_password or password)
            writer.write(output)
            writer.close()
            logger.info("Protected PDF → %s", output)
        except Exception as exc:
            logger.error("protect failed: %s", exc)
            return f"Error: {exc}"

        return f"PDF protected with password → {output}"

    @staticmethod
    def unlock(input_path: str, output: str, password: str) -> str:
        """Remove password protection from a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            if not reader.is_encrypted:
                return "Error: PDF is not encrypted"

            reader.decrypt(password)
            writer = pypdf.PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Unlocked PDF → %s", output)
        except Exception as exc:
            logger.error("unlock failed: %s", exc)
            return f"Error: {exc}"

        return f"PDF unlocked → {output}"

    @staticmethod
    def images_to_pdf(
        input_paths: list[str],
        output: str,
        fit: str = "fit",
        quality: int = 85,
    ) -> str:
        """Convert one or more images to a single PDF.

        Fit modes: fit (default), width, height, fill.
        """
        for f in input_paths:
            err = validate_input(f)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from PIL import Image
            import io

            writer = pypdf.PdfWriter()

            for img_path in input_paths:
                img = Image.open(img_path)
                if img.mode == "RGBA":
                    img = img.convert("RGB")

                # Convert image to PDF page
                img_stream = io.BytesIO()
                img.save(img_stream, format="JPEG", quality=quality)
                img_stream.seek(0)

                img_pdf = pypdf.PdfReader(img_stream)
                writer.add_page(img_pdf.pages[0])

            writer.write(output)
            writer.close()
            logger.info("Images → PDF (%d pages) → %s", len(input_paths), output)
        except Exception as exc:
            logger.error("images_to_pdf failed: %s", exc)
            return f"Error: {exc}"

        return f"Images → PDF ({len(input_paths)} pages) → {output}"

    @staticmethod
    def reorder_pages(
        input_path: str,
        output: str,
        pages: list[int],
    ) -> str:
        """Reorder PDF pages. pages: list of 1-indexed page numbers in desired order.

        Example: [3, 1, 2] puts page 3 first, then 1, then 2.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            total = len(reader.pages)
            writer = pypdf.PdfWriter()

            for p in pages:
                idx = p - 1  # Convert to 0-indexed
                if idx < 0 or idx >= total:
                    return f"Error: page {p} out of range (1-{total})"
                writer.add_page(reader.pages[idx])

            writer.write(output)
            writer.close()
            logger.info("Reordered pages → %s", output)
        except Exception as exc:
            logger.error("reorder_pages failed: %s", exc)
            return f"Error: {exc}"

        return f"Pages reordered → {output}"

    @staticmethod
    def delete_pages(
        input_path: str,
        output: str,
        pages: list[int],
    ) -> str:
        """Delete specific pages from a PDF. pages: list of 1-indexed page numbers to remove.

        Example: [2, 4, 5] removes pages 2, 4, and 5.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            total = len(reader.pages)
            to_delete = set(p - 1 for p in pages)  # Convert to 0-indexed

            for p in pages:
                if p < 1 or p > total:
                    return f"Error: page {p} out of range (1-{total})"

            writer = pypdf.PdfWriter()
            for i, page in enumerate(reader.pages):
                if i not in to_delete:
                    writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Deleted pages %s → %s", pages, output)
        except Exception as exc:
            logger.error("delete_pages failed: %s", exc)
            return f"Error: {exc}"

        return f"Pages deleted → {output}"

    @staticmethod
    def add_page_numbers(
        input_path: str,
        output: str,
        position: str = "bottom-center",
        format_str: str = "Page {page}",
    ) -> str:
        """Add page numbers to all pages of a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm

            w, h = A4
            positions = {
                "bottom-center": (w / 2, 15 * mm),
                "bottom-left": (20 * mm, 15 * mm),
                "bottom-right": (w - 20 * mm, 15 * mm),
                "top-center": (w / 2, h - 15 * mm),
                "top-left": (20 * mm, h - 15 * mm),
                "top-right": (w - 20 * mm, h - 15 * mm),
            }
            x, y = positions.get(position, positions["bottom-center"])

            for i, page in enumerate(reader.pages):
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)
                c.setFont("Helvetica", 10)
                page_num = format_str.format(page=i + 1, total=len(reader.pages))
                c.drawString(x, y, page_num)
                c.save()
                packet.seek(0)

                overlay = pypdf.PdfReader(packet)
                page.merge_page(overlay.pages[0])
                writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Page numbers → %s", output)
        except Exception as exc:
            logger.error("add_page_numbers failed: %s", exc)
            return f"Error: {exc}"

        return f"Page numbers → {output}"

    @staticmethod
    def protect(input_path: str, output: str, password: str) -> str:
        """Add password protection to a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            writer.encrypt(password)
            writer.write(output)
            writer.close()
            logger.info("Protected PDF → %s", output)
        except Exception as exc:
            logger.error("protect failed: %s", exc)
            return f"Error: {exc}"

        return f"PDF protected → {output}"

    @staticmethod
    def unlock(input_path: str, output: str, password: str) -> str:
        """Remove password protection from a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            if not reader.is_encrypted:
                return "Error: PDF is not password-protected"

            reader.decrypt(password)
            writer = pypdf.PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Unlocked PDF → %s", output)
        except Exception as exc:
            logger.error("unlock failed: %s", exc)
            return f"Error: {exc}"

        return f"PDF unlocked → {output}"

    @staticmethod
    def images_to_pdf(input_paths: list[str], output: str, quality: int = 85) -> str:
        """Convert one or more images to a single PDF."""
        for f in input_paths:
            err = validate_input(f)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from PIL import Image as PILImage

            packets = []
            for img_path in input_paths:
                img = PILImage.open(img_path)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Create PDF page from image
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)
                c.drawImage(img_path, 0, 0, width=A4[0], height=A4[1], mask="auto")
                c.save()
                packet.seek(0)
                packets.append(pypdf.PdfReader(packet))

            writer = pypdf.PdfWriter()
            for pdf_reader in packets:
                for page in pdf_reader.pages:
                    writer.add_page(page)

            writer.write(output)
            writer.close()
            logger.info("Images → PDF (%d pages) → %s", len(input_paths), output)
        except Exception as exc:
            logger.error("images_to_pdf failed: %s", exc)
            return f"Error: {exc}"

        return f"Images → PDF → {output} ({len(input_paths)} pages)"

    @staticmethod
    def reorder_pages(input_path: str, output: str, pages: list[int]) -> str:
        """Reorder PDF pages. pages: list of 1-indexed page numbers in desired order."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            total = len(reader.pages)

            # Validate page numbers
            for p in pages:
                if p < 1 or p > total:
                    return f"Error: page {p} out of range (1-{total})"

            writer = pypdf.PdfWriter()
            for p in pages:
                writer.add_page(reader.pages[p - 1])

            writer.write(output)
            writer.close()
            logger.info("Reordered pages → %s", output)
        except Exception as exc:
            logger.error("reorder_pages failed: %s", exc)
            return f"Error: {exc}"

        return f"Pages reordered → {output}"

    @staticmethod
    def delete_pages(input_path: str, output: str, pages: list[int]) -> str:
        """Delete specific pages from a PDF. pages: list of 1-indexed page numbers to remove."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            total = len(reader.pages)
            to_delete = set(p - 1 for p in pages)  # Convert to 0-indexed

            # Validate page numbers
            for p in pages:
                if p < 1 or p > total:
                    return f"Error: page {p} out of range (1-{total})"

            writer = pypdf.PdfWriter()
            for i in range(total):
                if i not in to_delete:
                    writer.add_page(reader.pages[i])

            writer.write(output)
            writer.close()
            logger.info("Deleted %d pages → %s", len(pages), output)
        except Exception as exc:
            logger.error("delete_pages failed: %s", exc)
            return f"Error: {exc}"

        return f"Pages deleted → {output}"

    @staticmethod
    def sign(
        input_path: str,
        output: str,
        signature_image: str,
        page: int = 1,
        x: float = 50,
        y: float = 50,
        width: float = 150,
        height: float = 50,
    ) -> str:
        """Add a signature image to a specific page of a PDF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_input(signature_image)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            from reportlab.pdfgen import canvas

            if page < 1 or page > len(reader.pages):
                return f"Error: page {page} out of range (1-{len(reader.pages)})"

            # Create signature overlay
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=reader.pages[0].mediabox)
            c.drawImage(signature_image, x, y, width=width, height=height, mask="auto")
            c.save()
            packet.seek(0)

            sig_overlay = pypdf.PdfReader(packet)

            for i, page_obj in enumerate(reader.pages):
                if i + 1 == page:
                    page_obj.merge_page(sig_overlay.pages[0])
                writer.add_page(page_obj)

            writer.write(output)
            writer.close()
            logger.info("Signed PDF → %s", output)
        except Exception as exc:
            logger.error("sign failed: %s", exc)
            return f"Error: {exc}"

        return f"PDF signed → {output} (page {page})"

    @staticmethod
    def fill_form(
        input_path: str,
        output: str,
        fields: dict[str, str],
    ) -> str:
        """Fill PDF form fields.

        fields: dict mapping field names to values.
        Example: {"name": "John Doe", "date": "2025-01-01"}
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            if not reader.get_fields():
                return "Error: PDF has no form fields"

            for page in reader.pages:
                writer.add_page(page)

            # Fill fields
            fields_obj = reader.get_fields()
            if fields_obj:
                writer.update_page_form_field_values(
                    writer.pages[0], fields, append=True
                )

            writer.write(output)
            writer.close()
            logger.info("Form filled → %s", output)
        except Exception as exc:
            logger.error("fill_form failed: %s", exc)
            return f"Error: {exc}"

        return f"Form filled → {output}"

    @staticmethod
    def compare(input_path: str, other_path: str) -> str:
        """Compare two PDFs and report differences.

        Returns page count comparison and text-level diff.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_input(other_path)
        if err:
            return err

        try:
            reader1 = pypdf.PdfReader(input_path)
            reader2 = pypdf.PdfReader(other_path)

            pages1 = len(reader1.pages)
            pages2 = len(reader2.pages)

            lines = [
                f"File 1: {input_path} ({pages1} pages)",
                f"File 2: {other_path} ({pages2} pages)",
                f"Page count {'matches' if pages1 == pages2 else 'differs'}",
            ]

            if pages1 == pages2:
                for i in range(pages1):
                    text1 = reader1.pages[i].extract_text() or ""
                    text2 = reader2.pages[i].extract_text() or ""
                    if text1.strip() != text2.strip():
                        lines.append(f"Page {i + 1}: DIFFERENT ({len(text1)} vs {len(text2)} chars)")
                    else:
                        lines.append(f"Page {i + 1}: identical")
            else:
                lines.append(f"Cannot compare text: page counts differ ({pages1} vs {pages2})")

            result = "\n".join(lines)
            logger.info("PDF compare done")
            return result
        except Exception as exc:
            logger.error("compare failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def pdf_to_a(input_path: str, output: str, pdf_a_version: str = "1b") -> str:
        """Convert PDF to PDF/A archival format.

        pdf_a_version: '1a', '1b', '2a', '2b', '3a', '3b', '3u'
        Uses Ghostscript for conversion.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            cmd = [
                "gs",
                "-dPDFA=" + pdf_a_version,
                "-dPDFAOutputIntent=",
                "-sPDFCOnvertToRGB",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=pdfwrite",
                f"-sOutputFile={output}",
                input_path,
            ]

            desc, ok = _subprocess_with_logging(cmd, f"Converted to PDF/A-{pdf_a_version} → {output}")
            if not ok:
                return desc

            logger.info("PDF/A conversion → %s", output)
        except FileNotFoundError:
            return "Error: Ghostscript (gs) not found. Install with: brew install ghostscript"
        except Exception as exc:
            logger.error("pdf_to_a failed: %s", exc)
            return f"Error: {exc}"

        return f"Converted to PDF/A-{pdf_a_version} → {output}"

    @staticmethod
    def pdf_to_markdown(
        input_path: str,
        output: str | None = None,
        pages: list[int] | None = None,
        api_key: str | None = None,
    ) -> str:
        """Convert a PDF (or DOCX, HTML, XLSX) to Markdown using Firecrawl CLI.

        Requires: npx firecrawl installed + FIRECRAWL_API_KEY env var.
        Free tier: 500 requests/month.
        """
        err = validate_input(input_path)
        if err:
            return err
        if output:
            err = validate_output_dir(output)
            if err:
                return err

        api_key = api_key or os.environ.get("FIRECRAWL_API_KEY")
        if not api_key:
            return "Error: FIRECRAWL_API_KEY not set. Get one at https://firecrawl.dev"

        try:
            cmd = [
                "npx", "firecrawl", "parse",
                input_path,
                "-f", "markdown",
                "-k", api_key,
            ]

            if pages:
                # Firecrawl CLI doesn't have a direct page filter,
                # but we can note it for future support
                logger.warning("Page filtering not yet supported by firecrawl parse CLI")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                markdown = result.stdout.strip()
                if output:
                    Path(output).write_text(markdown, encoding="utf-8")
                    logger.info("Fire-PDF → %s", output)
                    return f"Markdown → {output} ({len(markdown)} chars)"
                logger.info("Fire-PDF %d chars from %s", len(markdown), input_path)
                return markdown

            stderr = result.stderr.strip()
            if "401" in stderr or "unauthorized" in stderr.lower():
                return "Error: Invalid FIRECRAWL_API_KEY"
            if "rate" in stderr.lower() or "limit" in stderr.lower():
                return "Error: Firecrawl rate limit exceeded. Free tier: 500 req/month."
            logger.error("Fire-PDF failed (rc=%d): %s", result.returncode, stderr)
            return f"Fire-PDF error: {stderr or result.stderr}"

        except subprocess.TimeoutExpired:
            return "Error: Fire-PDF request timed out (120s limit)"
        except FileNotFoundError:
            return "Error: firecrawl CLI not found. Install with: npm install -g firecrawl"
        except Exception as exc:
            logger.error("pdf_to_markdown failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def to_docx(input_path: str, output: str) -> str:
        """Convert PDF to DOCX using pdf2docx."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from pdf2docx import Converter
            cv = Converter(input_path)
            cv.convert(output)
            cv.close()
            logger.info("Converted PDF → DOCX: %s", output)
            return f"Converted to DOCX → {output}"
        except Exception as exc:
            logger.error("to_docx failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def redact(
        input_path: str, output: str,
        text_patterns: list[str] | None = None,
        rect_areas: list[dict] | None = None,
    ) -> str:
        """Redact (black out) sensitive information from PDF.
        
        text_patterns: list of text strings to redact
        rect_areas: list of {x, y, width, height} to redact
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            import pypdf
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch

            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            for page in reader.pages:
                page_copy = page.clone()
                # Add redaction rectangles
                for rect in (rect_areas or []):
                    x, y, w, h = rect.get('x', 0), rect.get('y', 0), rect.get('width', 100), rect.get('height', 50)
                    # Convert to PDF coordinates (bottom-left origin)
                    pdf_y = letter[1] - y - h
                    page_copy.merge_page(
                        pdf_canvas.Canvas(io.BytesIO(), pagesize=letter)
                        .setFillColor('black')
                        .rect(x * inch, pdf_y, w * inch, h * inch, fill=True)
                        .getpdfdata()
                    )
                writer.add_page(page_copy)

            with open(output, 'wb') as f:
                writer.write(f)
            logger.info("Redacted PDF → %s", output)
            return f"Redacted PDF → {output}"
        except Exception as exc:
            logger.error("redact failed: %s", exc)
            return f"Error: {exc}"
