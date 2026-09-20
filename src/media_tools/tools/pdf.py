"""PDF toolkit — merge, split, compress, extract text/images, rotate, info."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import anydoc
import pdfplumber
import pypdf
import pypdfium2 as pdfium

from media_tools.utils import (
    _subprocess_with_logging,
    logger,
    stash_return,
    validate_input,
    validate_output_dir,
)

try:
    import liteparse

    HAS_LITEPARSE = True
except ImportError:
    HAS_LITEPARSE = False


def _render_cover(pdf_path: str, cover_path: str, dpi: int = 72) -> str | None:
    """Render page 1 of a PDF to a PNG cover thumbnail.

    Shared by merge/split cover flags. Returns an error string on failure,
    else None (cover written to cover_path).
    """
    try:
        doc = pdfium.PdfDocument(pdf_path)
        try:
            img = doc[0].render(scale=dpi / 72).to_pil()
            img.save(cover_path)
        finally:
            doc.close()
    except Exception as exc:
        logger.error("cover render failed: %s", exc)
        return str(exc)
    logger.info("Cover → %s", cover_path)
    return None


class PDFToolkit:
    name = "pdf"

    @staticmethod
    def merge(files: list[str], output: str, cover: bool = False) -> str:
        """Merge multiple PDF files into one.

        cover: when True, also render page 1 at 72 dpi
        (`<output-stem>_cover.png` next to the output) and return a JSON
        string with its path. Default False = plain-text return, unchanged.
        """
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

        if not cover:
            return f"Merged {len(files)} files into {output}"
        cover_path = str(Path(output).with_name(f"{Path(output).stem}_cover.png"))
        cover_err = _render_cover(output, cover_path)
        if cover_err:
            import json

            return json.dumps(
                {"result": f"Merged {len(files)} files into {output}", "output": output, "cover_error": cover_err}
            )
        import json

        return json.dumps({"result": f"Merged {len(files)} files into {output}", "output": output, "cover": cover_path})

    @staticmethod
    def split(input_path: str, pages: str, output_dir: str, cover: bool = False) -> str:
        """Split a PDF. pages: ranges like '1-3,5,7-9' (1-indexed).

        cover: when True, also render page 1 of each split file at 72 dpi
        (`<split-stem>_cover.png` next to it) and return a JSON string with
        the file/cover lists. Default False = plain-text return, unchanged.
        """
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
                    lo, hi = part.split("-")
                    start = int(lo) - 1 if lo else 0
                    end = int(hi) if hi else total
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
            if not cover:
                return f"Split into {len(results)} files: {', '.join(results)}"
            import json

            covers = []
            for r in results:
                cover_path = str(Path(r).with_name(f"{Path(r).stem}_cover.png"))
                cover_err = _render_cover(r, cover_path)
                if cover_err:
                    return json.dumps(
                        {
                            "result": f"Split into {len(results)} files: {', '.join(results)}",
                            "files": results,
                            "cover_error": cover_err,
                        }
                    )
                covers.append(cover_path)
            return json.dumps(
                {
                    "result": f"Split into {len(results)} files: {', '.join(results)}",
                    "files": results,
                    "covers": covers,
                }
            )
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
                writer.add_page(page).compress_content_streams()

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
                text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)

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
    def ocr(input_path: str, output: str | None = None, dpi: int = 200) -> str:
        """OCR a scanned/image PDF page-by-page and return the extracted text."""
        err = validate_input(input_path)
        if err:
            return err

        try:
            import pytesseract
        except ImportError:
            return "Error: pytesseract not installed (pip install pytesseract, plus the tesseract binary)"

        try:
            pdf = pdfium.PdfDocument(input_path)
            pages_text = []
            for page in pdf:
                bitmap = page.render(scale=dpi / 72)
                img = bitmap.to_pil()
                pages_text.append(pytesseract.image_to_string(img).strip())
            pdf.close()

            text = "\n\n".join(pages_text)
            if output:
                Path(output).write_text(text, encoding="utf-8")
                logger.info("OCR'd %d pages → %s", len(pages_text), output)
                return f"OCR'd {len(pages_text)} pages → {output}"

            logger.info("OCR'd %d pages", len(pages_text))
            return text
        except Exception as exc:
            logger.error("ocr failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def salvage(input_path: str, out_dir: str, ocr_fallback: bool = True, dpi: int = 150) -> str:
        """Salvage readable content from a corrupt/malformed PDF, per page.

        Probes the page count defensively (pdfplumber, then pypdf, then
        pdfium — whatever opens it), then loops pages 1..N each in its own
        try/except so one bad page never aborts the job. Per page: (a)
        pdfplumber text, (b) pdfium render-to-PNG, (c) pytesseract OCR on
        the render when there is no text and ocr_fallback is set.
        Writes page_%04d.txt (only when non-empty), page_%04d.png, and
        salvage_manifest.json. Read-only on the input; no repair attempted.
        """
        import json
        import shutil
        import tempfile

        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(out_dir)
        if err:
            return err

        total = 0
        probe_errors: list[str] = []
        for probe in ("pdfplumber", "pypdf", "pdfium"):
            try:
                if probe == "pdfplumber":
                    with pdfplumber.open(input_path) as pdf:
                        total = len(pdf.pages)
                elif probe == "pypdf":
                    total = len(pypdf.PdfReader(input_path).pages)
                else:
                    doc = pdfium.PdfDocument(input_path)
                    try:
                        total = len(doc)
                    finally:
                        doc.close()
                break
            except Exception as exc:
                probe_errors.append(f"{probe}: {exc}")
        if total <= 0:
            logger.error("salvage failed: no reader could open %s", input_path)
            return json.dumps(
                {
                    "out_dir": out_dir,
                    "pages_total": 0,
                    "pages_with_text": 0,
                    "pages_with_images": 0,
                    "pages_failed": 0,
                    "error": f"could not determine page count ({'; '.join(probe_errors)})",
                }
            )

        try:
            plumber = pdfplumber.open(input_path)
        except Exception as exc:
            plumber = None
            plumber_error = str(exc)
        else:
            plumber_error = ""
        try:
            doc = pdfium.PdfDocument(input_path)
        except Exception as exc:
            doc = None
            pdfium_error = str(exc)
        else:
            pdfium_error = ""

        ocr_available = True
        try:
            import pytesseract  # noqa: F401
        except ImportError:
            ocr_available = False

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        pages: list[dict[str, Any]] = []
        try:
            with tempfile.TemporaryDirectory() as tmp:
                for i in range(1, total + 1):
                    entry: dict[str, Any] = {
                        "page": i,
                        "text_chars": 0,
                        "image": None,
                        "ocr_used": False,
                        "errors": [],
                    }
                    text = ""
                    if plumber is None:
                        entry["errors"].append(f"text: pdfplumber open failed: {plumber_error}")
                    else:
                        try:
                            text = plumber.pages[i - 1].extract_text() or ""
                        except Exception as exc:
                            entry["errors"].append(f"text: {exc}")
                    img = None
                    if doc is None:
                        entry["errors"].append(f"render: pdfium open failed: {pdfium_error}")
                    else:
                        try:
                            img = doc[i - 1].render(scale=dpi / 72).to_pil()
                            tmp_png = str(Path(tmp) / f"page_{i:04d}.png")
                            img.save(tmp_png)
                            final_png = str(out_path / f"page_{i:04d}.png")
                            shutil.copy(tmp_png, final_png)
                            entry["image"] = final_png
                        except Exception as exc:
                            entry["errors"].append(f"render: {exc}")
                            img = None
                    if not text.strip() and ocr_fallback and img is not None:
                        if not ocr_available:
                            entry["errors"].append("ocr: pytesseract not installed")
                        else:
                            try:
                                import pytesseract

                                ocr_text = pytesseract.image_to_string(img).strip()
                                if ocr_text:
                                    text = ocr_text
                                    entry["ocr_used"] = True
                            except Exception as exc:
                                entry["errors"].append(f"ocr: {exc}")
                    if text.strip():
                        (out_path / f"page_{i:04d}.txt").write_text(text, encoding="utf-8")
                    entry["text_chars"] = len(text)
                    pages.append(entry)
        finally:
            try:
                if plumber is not None:
                    plumber.close()
            except Exception as exc:
                logger.debug("plumber close failed: %s", exc)
            try:
                if doc is not None:
                    doc.close()
            except Exception as exc:
                logger.debug("doc close failed: %s", exc)

        with_text = sum(1 for p in pages if p["text_chars"] > 0)
        with_images = sum(1 for p in pages if p["image"])
        failed = sum(1 for p in pages if p["text_chars"] == 0 and not p["image"])
        manifest = {
            "input": input_path,
            "out_dir": out_dir,
            "pages_total": total,
            "pages": pages,
            "totals": {
                "pages_with_text": with_text,
                "pages_with_images": with_images,
                "pages_failed": failed,
            },
        }
        manifest_path = str(out_path / "salvage_manifest.json")
        Path(manifest_path).write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Salvaged %s → %s (%d/%d pages with text)", input_path, out_dir, with_text, total)
        return json.dumps(
            {
                "out_dir": out_dir,
                "pages_total": total,
                "pages_with_text": with_text,
                "pages_with_images": with_images,
                "pages_failed": failed,
                "manifest": manifest_path,
            }
        )

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
    def crop(input_path: str, output: str, left: float = 0, bottom: float = 0, right: float = 0, top: float = 0) -> str:
        """Crop page margins (points to trim from each edge)."""
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
                box = new_page.mediabox
                new_page.mediabox.lower_left = (box.left + left, box.bottom + bottom)
                new_page.mediabox.upper_right = (box.right - right, box.top - top)

            writer.write(output)
            writer.close()
            logger.info("Cropped PDF → %s", output)
        except Exception as exc:
            logger.error("crop failed: %s", exc)
            return f"Error: {exc}"

        return f"Cropped → {output}"

    @staticmethod
    def info(input_path: str) -> str:
        """Get PDF metadata."""
        err = validate_input(input_path)
        if err:
            return err

        try:
            reader = pypdf.PdfReader(input_path)
            info: Any = reader.metadata or {}
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
        input_path: str,
        output: str | None = None,
        ocr: bool = False,
        language: str = "eng",
        dpi: int = 150,
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
        input_path: str,
        output_dir: str,
        dpi: int = 150,
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

            from reportlab.lib.colors import HexColor
            from reportlab.lib.pagesizes import A4
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
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas

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
            from PIL import Image as PILImage
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            packets = []
            for img_path in input_paths:
                img: PILImage.Image = PILImage.open(img_path)
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
            ticket, stash_path = stash_return(input_path)
        except OSError as exc:
            return f"Error: could not stash original: {exc}"

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

        return f"Pages deleted → {output} (original stashed: ticket {ticket} at {stash_path})"

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
                writer.update_page_form_field_values(writer.pages[0], fields)

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
    ) -> str:
        """Convert a PDF (or DOCX, HTML, XLSX, ODT, RTF) to Markdown locally with anydoc.

        No subprocess, no API key, no network — the file never leaves the machine.
        `pages` is accepted for API compatibility but page filtering is not
        supported by anydoc (`to_markdown` converts the whole document), so the
        full document is always converted.
        """
        err = validate_input(input_path)
        if err:
            return err
        if output:
            err = validate_output_dir(output)
            if err:
                return err

        if pages:
            logger.warning("Page filtering not supported by anydoc; converting whole document")

        try:
            markdown = anydoc.to_markdown(input_path)

            if output:
                Path(output).write_text(markdown, encoding="utf-8")
                logger.info("PDF → Markdown %s", output)
                return f"Markdown → {output} ({len(markdown)} chars)"
            logger.info("PDF → Markdown %d chars from %s", len(markdown), input_path)
            return markdown
        except (anydoc.EncryptedError, anydoc.UnsupportedError) as exc:
            logger.error("pdf_to_markdown failed: %s", exc)
            return f"Error: {exc}"
        except anydoc.ConvertError as exc:
            logger.error("pdf_to_markdown failed: %s", exc)
            return f"Error: {exc}"
        except Exception as exc:
            logger.error("pdf_to_markdown failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def md_to_branded_pdf(
        input_path: str,
        output: str,
        font_path: str | None = None,
        color: str | None = None,
        logo_path: str | None = None,
        logo_position: str = "bottom-right",
        page_numbers: bool = True,
    ) -> str:
        """Convert a strict Markdown subset to a branded PDF (reportlab Platypus, offline).

        Subset: H1-H3, paragraphs, bold/italic/inline-code, bullet/numbered lists,
        fenced code, pipe tables, images, horizontal rules.
        # Degradation (by design, not bugs): nested lists are flattened to top level;
        # raw HTML tags are stripped; long tables split across pages (repeatRows=1);
        # missing image files become an italic placeholder line instead of an error.
        """
        import re
        from html import escape as _esc

        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if logo_path:
            err = validate_input(logo_path)
            if err:
                return err

        try:
            from reportlab.lib.colors import HexColor, white
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.platypus import (
                HRFlowable,
                Paragraph,
                Preformatted,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
            from reportlab.platypus import (
                Image as RLImage,
            )

            brand = HexColor(color) if color else HexColor("#222222")

            body_font = "Helvetica"
            if font_path:
                ferr = validate_input(font_path)
                if ferr:
                    return ferr
                pdfmetrics.registerFont(TTFont("BrandFont", font_path))
                body_font = "BrandFont"

            base = getSampleStyleSheet()
            s_body = ParagraphStyle("BrandBody", parent=base["Normal"], fontName=body_font, fontSize=10)
            s_h1 = ParagraphStyle("BrandH1", parent=base["Heading1"], fontName=body_font, textColor=brand, fontSize=20)
            s_h2 = ParagraphStyle("BrandH2", parent=base["Heading2"], fontName=body_font, textColor=brand, fontSize=15)
            s_h3 = ParagraphStyle("BrandH3", parent=base["Heading3"], fontName=body_font, textColor=brand, fontSize=12)
            s_bullet = ParagraphStyle("BrandBullet", parent=s_body, leftIndent=18, bulletIndent=6, spaceBefore=1)
            s_code = ParagraphStyle("BrandCode", parent=base["Code"], fontName="Courier", fontSize=9, leading=12)
            s_caption = ParagraphStyle("BrandCaption", parent=s_body, textColor=HexColor("#666666"), fontSize=9)

            tag_re = re.compile(r"<[^>]+>")

            def clean(text: str) -> str:
                text = tag_re.sub("", text.strip())
                text = _esc(text, quote=False)
                text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
                text = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", text)
                text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
                return text

            text = Path(input_path).read_text(encoding="utf-8")
            lines = text.splitlines()
            story: list[Any] = []
            i = 0
            n = len(lines)
            md_dir = Path(input_path).parent
            img_re = re.compile(r"!\[(.*?)\]\((.*?)\)")

            def flush_para(buf: list[str]) -> None:
                if buf:
                    story.append(Paragraph(clean(" ".join(b.strip() for b in buf)), s_body))
                    story.append(Spacer(1, 4))
                    buf.clear()

            para: list[str] = []
            in_code = False
            code_buf: list[str] = []
            while i < n:
                line = lines[i]
                if line.strip().startswith("```"):
                    if in_code:
                        story.append(Preformatted("\n".join(code_buf), s_code))
                        story.append(Spacer(1, 6))
                        code_buf.clear()
                        in_code = False
                    else:
                        flush_para(para)
                        in_code = True
                    i += 1
                    continue
                if in_code:
                    code_buf.append(line)
                    i += 1
                    continue
                stripped = line.strip()
                if not stripped:
                    flush_para(para)
                    i += 1
                    continue
                m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
                if m:
                    flush_para(para)
                    level = len(m.group(1))
                    style = {1: s_h1, 2: s_h2, 3: s_h3}[level]
                    story.append(Paragraph(clean(m.group(2)), style))
                    story.append(Spacer(1, 6))
                    i += 1
                    continue
                if re.match(r"^(\*\*\*|---|___)\s*$", stripped):
                    flush_para(para)
                    story.append(HRFlowable(width="100%", thickness=1, color=brand))
                    story.append(Spacer(1, 6))
                    i += 1
                    continue
                if stripped.startswith("|") and stripped.endswith("|"):
                    flush_para(para)
                    rows: list[list[str]] = []
                    while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                        if not all(re.match(r"^:?-{3,}:?$", c) for c in cells):
                            rows.append(cells)
                        i += 1
                    if rows:
                        data = [[Paragraph(clean(c), s_body) for c in row] for row in rows]
                        t = Table(data, repeatRows=1)
                        t.setStyle(
                            TableStyle(
                                [
                                    ("BACKGROUND", (0, 0), (-1, 0), brand),
                                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#999999")),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ]
                            )
                        )
                        story.append(t)
                        story.append(Spacer(1, 6))
                    continue
                m = img_re.search(stripped)
                if m and stripped.startswith("!"):
                    flush_para(para)
                    alt, src = m.group(1), m.group(2)
                    img_file = md_dir / src if not Path(src).is_absolute() else Path(src)
                    if img_file.exists():
                        story.append(RLImage(str(img_file), width=150 * mm, height=100 * mm))
                        if alt:
                            story.append(Paragraph(clean(alt), s_caption))
                    else:
                        story.append(Paragraph(f"<i>[image missing: {_esc(src, quote=False)}]</i>", s_body))
                    story.append(Spacer(1, 6))
                    i += 1
                    continue
                m = re.match(r"^\s*([-*+]|\d+[.)])\s+(.*)$", line)
                if m:
                    flush_para(para)
                    marker, content = m.group(1), m.group(2)
                    bullet = "•" if re.match(r"[-*+]", marker) else marker
                    story.append(Paragraph(clean(content), s_bullet, bulletText=bullet))
                    i += 1
                    continue
                para.append(line)
                i += 1
            flush_para(para)

            logo_info: dict[str, Any] = {}
            if logo_path:
                from reportlab.lib.utils import ImageReader

                iw, ih = ImageReader(logo_path).getSize()
                target_h = 14 * mm
                logo_info = {
                    "path": logo_path,
                    "w": target_h * iw / ih,
                    "h": target_h,
                    "position": logo_position,
                }

            def header_footer(canv: Any, doc: Any) -> None:
                canv.saveState()
                pw, ph = A4
                if page_numbers:
                    canv.setFont("Helvetica", 9)
                    canv.drawCentredString(pw / 2, 12 * mm, f"Page {doc.page}")
                if logo_info:
                    lw, lh = logo_info["w"], logo_info["h"]
                    pos = logo_info["position"]
                    margin = 12 * mm
                    if pos == "top-left":
                        x, y = margin, ph - lh - margin
                    elif pos == "top-right":
                        x, y = pw - lw - margin, ph - lh - margin
                    elif pos == "bottom-left":
                        x, y = margin, margin
                    elif pos == "center":
                        x, y = (pw - lw) / 2, (ph - lh) / 2
                    else:
                        x, y = pw - lw - margin, margin
                    canv.drawImage(logo_info["path"], x, y, width=lw, height=lh, mask="auto")
                canv.restoreState()

            doc_tpl = SimpleDocTemplate(output, pagesize=A4)
            doc_tpl.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
            logger.info("Markdown → branded PDF → %s", output)
        except Exception as exc:
            logger.error("md_to_branded_pdf failed: %s", exc)
            return f"Error: {exc}"

        return f"Markdown → branded PDF → {output}"

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
        input_path: str,
        output: str,
        text_patterns: list[str] | None = None,
        rect_areas: list[dict] | None = None,
    ) -> str:
        """Redact (black out) sensitive information from PDF.

        Pages with redactions are rasterized (144 dpi) and rewritten as image-only
        pages, so the redacted text is truly removed, but those pages lose all
        selectable text. Pages without redactions are left untouched.
        Rotated pages are not supported: rects are placed as if the page were unrotated.

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
            ticket, stash_path = stash_return(input_path)
        except OSError as exc:
            return f"Error: could not stash original: {exc}"

        try:
            import pypdf
            from PIL import ImageDraw

            # Collect per-page rectangles (top-left origin, points) to black out.
            page_rects: dict[int, list[tuple[float, float, float, float]]] = {}

            for rect in rect_areas or []:
                page_no = rect.get("page", 0)
                x, y, w, h = rect.get("x", 0), rect.get("y", 0), rect.get("width", 100), rect.get("height", 50)
                page_rects.setdefault(page_no, []).append((x, y, w, h))

            if text_patterns:
                with pdfplumber.open(input_path) as pdf:
                    for page_no, page in enumerate(pdf.pages):
                        for pattern in text_patterns:
                            for word in page.extract_words():
                                if pattern in word["text"]:
                                    x0, top, x1, bottom = word["x0"], word["top"], word["x1"], word["bottom"]
                                    page_rects.setdefault(page_no, []).append((x0, top, x1 - x0, bottom - top))

            reader = pypdf.PdfReader(input_path)
            writer = pypdf.PdfWriter()

            doc = pdfium.PdfDocument(input_path)
            for page_no, src_page in enumerate(reader.pages):
                rects = page_rects.get(page_no, [])
                if not rects:
                    writer.add_page(src_page)
                    continue
                # Rasterize, paint black, and replace the page with an image-only page
                # so the original text is not left in the content stream.
                scale = 2.0  # 144 dpi
                img = doc[page_no].render(scale=scale).to_pil().convert("RGB")
                draw = ImageDraw.Draw(img)
                for x, y, w, h in rects:
                    draw.rectangle([x * scale, y * scale, (x + w) * scale, (y + h) * scale], fill="black")
                buf = io.BytesIO()
                img.save(buf, format="PDF", resolution=72 * scale)
                buf.seek(0)
                writer.add_page(pypdf.PdfReader(buf).pages[0])
            doc.close()

            with open(output, "wb") as f:
                writer.write(f)
            logger.info("Redacted PDF → %s", output)
            return f"Redacted PDF → {output} (original stashed: ticket {ticket} at {stash_path})"
        except Exception as exc:
            logger.error("redact failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def extract_tables(
        input_path: str,
        output_dir: str,
        pages: list[int] | None = None,
    ) -> str:
        """Dump raw PDF tables to CSV files, one file per table.

        pages: optional list of 1-indexed page numbers (None = all pages).
        Per page, tries both line-based (default) and text-based strategies
        and keeps whichever yields more cells. Pages with no tables are
        skipped silently. Returns a JSON string, not an error, even when
        no tables are found anywhere.
        """
        import csv
        import json

        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_dir)
        if err:
            return err

        try:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            def _cells(tables: list[Any]) -> int:
                return sum(len(row) for t in tables for row in t)

            files: list[str] = []
            tables_info: list[dict[str, Any]] = []
            skipped: list[int] = []
            with pdfplumber.open(input_path) as pdf:
                total = len(pdf.pages)
                wanted = sorted(p for p in (pages or range(1, total + 1)) if 1 <= p <= total)
                for page_no in wanted:
                    page = pdf.pages[page_no - 1]
                    lined = page.extract_tables() or []
                    try:
                        texted = (
                            page.extract_tables(
                                {
                                    "vertical_strategy": "text",
                                    "horizontal_strategy": "text",
                                }
                            )
                            or []
                        )
                    except Exception:
                        texted = []
                    tables = texted if _cells(texted) > _cells(lined) else lined
                    # Drop fully empty tables; normalize None → "".
                    tables = [
                        [[c if c is not None else "" for c in row] for row in t]
                        for t in tables
                        if any(any(c not in (None, "") for c in row) for row in t)
                    ]
                    if not tables:
                        skipped.append(page_no)
                        continue
                    for i, table in enumerate(tables, start=1):
                        out_path = out_dir / f"page{page_no}_table{i}.csv"
                        # Plain UTF-8, no BOM: agents consume the CSVs as text.
                        with open(out_path, "w", newline="", encoding="utf-8") as f:
                            csv.writer(f).writerows(table)
                        files.append(str(out_path))
                        tables_info.append(
                            {
                                "file": str(out_path),
                                "page": page_no,
                                "table": i,
                                "rows": len(table),
                                "cols": max(len(row) for row in table),
                            }
                        )

            logger.info("Extracted %d tables → %s", len(files), output_dir)
            if not files:
                return json.dumps(
                    {
                        "message": f"No tables found in {input_path}",
                        "files": [],
                        "tables": [],
                        "pages_skipped": skipped,
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {
                    "files": files,
                    "tables": tables_info,
                    "pages_skipped": skipped,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.error("extract_tables failed: %s", exc)
            return f"Error: {exc}"
