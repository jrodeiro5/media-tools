"""PDF toolkit — merge, split, compress, extract text/images, rotate, info."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pdfplumber
import pypdf
import pypdfium2 as pdfium

from media_tools.utils import logger, validate_input, validate_output_dir

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
