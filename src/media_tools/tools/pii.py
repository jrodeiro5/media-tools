"""PII toolkit — find (and redact) Spanish/EU identifiers with Presidio's pattern recognizers."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from media_tools.tools.pdf import PDFToolkit
from media_tools.utils import logger, validate_input, validate_output_dir


def _recognizers():
    # ponytail: pattern+checksum recognizers only (no spaCy NER), so person names/addresses are not
    # detected; add an NlpEngine + AnalyzerEngine when names matter.
    from presidio_analyzer.predefined_recognizers import (
        EmailRecognizer,
        EsNieRecognizer,
        EsNifRecognizer,
        EsPassportRecognizer,
        IbanRecognizer,
        PhoneRecognizer,
    )

    return [
        EsNifRecognizer(),
        EsNieRecognizer(),
        EsPassportRecognizer(),
        IbanRecognizer(),
        EmailRecognizer(),
        PhoneRecognizer(supported_regions=["ES"]),
    ]


def _pages(input_path: str) -> list[str]:
    if Path(input_path).suffix.lower() == ".pdf":
        import pdfplumber

        with pdfplumber.open(input_path) as pdf:
            return [page.extract_text() or "" for page in pdf.pages]
    return [Path(input_path).read_text(encoding="utf-8")]


def _find(input_path: str) -> list[dict]:
    recognizers = _recognizers()
    found = []
    for page, text in enumerate(_pages(input_path), start=1):
        for rec in recognizers:
            for r in rec.analyze(text, rec.supported_entities, None):
                found.append(
                    {"type": r.entity_type, "page": page, "score": round(r.score, 2), "value": text[r.start : r.end]}
                )
    return found


class PiiToolkit:
    name = "pii"

    @staticmethod
    def scan(input_path: str) -> str:
        """Find Spanish/EU PII (DNI/NIF, NIE, passport, IBAN, email, phone) in a PDF or text file.

        Returns JSON with counts and per-finding type/page/score plus a masked preview; raw values are
        never returned, so they don't end up in the agent's context. Requires the `pii` extra.
        """
        err = validate_input(input_path)
        if err:
            return err
        try:
            found = _find(input_path)
        except ImportError:
            return "Error: install the pii extra: uv sync --extra pii"
        except Exception as exc:
            logger.error("pii scan failed: %s", exc)
            return f"Error: {exc}"
        findings = [{**f, "value": f["value"][:2] + "***"} for f in found]
        counts = dict(Counter(f["type"] for f in found))
        logger.info("PII scan %s: %s", input_path, counts)
        return json.dumps({"counts": counts, "findings": findings}, ensure_ascii=False)

    @staticmethod
    def redact(input_path: str, output: str) -> str:
        """Find PII in a PDF (see scan) and black it out via pdf_redact. Pages with hits lose selectable text."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if Path(input_path).suffix.lower() != ".pdf":
            return "Error: redact supports PDF only"
        try:
            values = sorted({f["value"] for f in _find(input_path)})
        except ImportError:
            return "Error: install the pii extra: uv sync --extra pii"
        except Exception as exc:
            logger.error("pii redact failed: %s", exc)
            return f"Error: {exc}"
        if not values:
            return "No PII found; nothing redacted"
        return PDFToolkit.redact(input_path, output, text_patterns=values)
