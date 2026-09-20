"""Office toolkit — convert to Markdown or PDF."""

from __future__ import annotations

import json
import shutil
import subprocess
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
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(Path(output).parent),
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

    @staticmethod
    def inspect(input_path: str, mode: str = "outline", page: str | None = None) -> str:
        """Read a .docx/.xlsx/.pptx with OfficeCLI: mode is text, outline, stats, issues, annotated or forms."""
        err = validate_input(input_path)
        if err:
            return err
        if mode not in _INSPECT_MODES:
            return f"Error: mode must be one of {', '.join(sorted(_INSPECT_MODES))}"
        cmd = ["officecli", "view", input_path, mode] + (["--page", page] if page else [])
        return _run_cli(cmd)

    @staticmethod
    def edit(input_path: str, output: str, commands: str) -> str:
        """Edit a .docx/.xlsx/.pptx on a copy, never in place. `commands` is OfficeCLI's batch JSON array,
        e.g. [{"command":"set","path":"/body/p[1]","props":{"bold":"true"}}]."""
        err = validate_input(input_path) or validate_output_dir(output)
        if err:
            return err
        if Path(output).resolve() == Path(input_path).resolve():
            return "Error: output must differ from input; edits are never in place"
        try:
            json.loads(commands)
        except ValueError as exc:
            return f"Error: commands is not valid JSON: {exc}"
        shutil.copyfile(input_path, output)
        res = _run_cli(["officecli", "batch", output, "--commands", commands])
        if res.startswith("Error"):
            Path(output).unlink(missing_ok=True)
            return res
        return f"Edited copy → {output}\n{res}"

    @staticmethod
    def url_to_markdown(url: str, output: str | None = None) -> str:
        """Fetch a web page or PDF URL as Markdown via the Firecrawl CLI. Cloud call: the URL is sent to
        Firecrawl and FIRECRAWL_API_KEY must be set. Local files never leave the machine; use office_to_markdown."""
        if not url.startswith(("http://", "https://")):
            return "Error: url must start with http:// or https://"
        if output:
            err = validate_output_dir(output)
            if err:
                return err
        res = _run_cli(["firecrawl", "scrape", url, "--format", "markdown", "--only-main-content"])
        if res.startswith("Error") or not output:
            return res
        Path(output).write_text(res, encoding="utf-8")
        return f"Saved markdown → {output}"


_INSPECT_MODES = {"text", "outline", "stats", "issues", "annotated", "forms"}


def _run_cli(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        return f"Error: {cmd[0]} not found" + (
            "; install with: brew install officecli" if cmd[0] == "officecli" else ""
        )
    except subprocess.TimeoutExpired:
        return "Error: officecli timed out"
    if r.returncode != 0:
        logger.error("officecli failed: %s", r.stderr.strip())
        return f"Error: {(r.stderr or r.stdout).strip()}"
    return r.stdout
