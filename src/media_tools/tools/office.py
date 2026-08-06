"""Office toolkit — convert to Markdown or PDF."""

from __future__ import annotations

from pathlib import Path

import anydoc

from media_tools.utils import _subprocess_with_logging, logger, validate_input, validate_output_dir


class OfficeToolkit:
    name = "office"

    @staticmethod
    def to_markdown(input_path: str, output: str | None = None) -> str:
        """Convert Office files (.docx, .pptx, .xlsx, .odt, .odp, .rtf, .epub, .csv, .pdf) to Markdown.

        Uses firecrawl-anydoc (Rust-based, ~5ms/doc). Supports 14 formats.
        """
        err = validate_input(input_path)
        if err:
            return err

        try:
            text = anydoc.to_markdown(input_path)

            if output:
                err = validate_output_dir(output)
                if err:
                    return err
                Path(output).write_text(text, encoding="utf-8")
                logger.info("Converted %s → %s", input_path, output)
                return f"Converted to markdown → {output}"

            logger.info("Converted %s to markdown", input_path)
            return text
        except (anydoc.EncryptedError, anydoc.UnsupportedError) as exc:
            logger.error("to_markdown failed: %s", exc)
            return f"Error: {exc}"
        except anydoc.ConvertError as exc:
            logger.error("to_markdown failed: %s", exc)
            return f"Error: {exc}"
        except Exception as exc:
            logger.error("to_markdown failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def to_pdf(input_path: str, output: str) -> str:
        """Convert Office documents to PDF using LibreOffice."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        cmd = [
            "soffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(Path(output).parent),
            input_path,
        ]
        desc, ok = _subprocess_with_logging(cmd, f"Converted to PDF → {output}")
        if not ok:
            return desc

        actual = Path(output).parent / f"{Path(input_path).stem}.pdf"
        if actual != Path(output):
            try:
                actual.rename(output)
            except OSError:
                pass  # Files may already match
        return desc
