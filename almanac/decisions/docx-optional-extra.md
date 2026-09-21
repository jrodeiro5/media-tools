---
title: pdf2docx moved to an optional docx extra (AGPL PyMuPDF)
topics: [decisions, toolkits]
sources:
  - id: pdf-py
    type: file
    target: src/media_tools/tools/pdf.py
    title: "PDFToolkit.to_docx — pdf2docx with LibreOffice fallback"
  - id: pyproject-docx
    type: file
    target: pyproject.toml
    title: "pyproject.toml — the optional `docx` extra"
  - id: office-py
    type: file
    target: src/media_tools/tools/office.py
    title: "OfficeToolkit implementation"
  - id: changelog
    type: file
    target: CHANGELOG.md
    title: "CHANGELOG.md — Unreleased section"
  - id: readme
    type: file
    target: README.md
    title: "README.md — optional dependencies and pdf_to_docx note"
  - id: commit
    type: commit
    commit: 0603bf5
    title: "build: move pdf2docx (AGPL PyMuPDF) to optional docx extra"
---

# pdf2docx moved to an optional docx extra (AGPL PyMuPDF)

Decided 2026-09-20, commit `0603bf5` [@commit].

## Context

`pdf_to_docx` originally converted PDFs to DOCX with `pdf2docx`, which pulls in
`PyMuPDF` under the **AGPL-3.0** copyleft license. Bundling an AGPL dependency in
a required install meant redistributing the package carried copyleft for anyone
installing it normally. The user wanted to ship the package without that license
encumbrance by default.

No other library generates a real `.docx` with preserved layout: `liteparse`
(already a dependency) and `docling` render PDFs to Markdown or JSON, not DOCX.

## Decision

Moved `pdf2docx` from the required `PDFToolkit` dependencies to the optional
`docx` extra (`pyproject.toml`) [@pyproject-docx]. Installing it is explicit:

```bash
uv sync --extra docx
```

`PDFToolkit.to_docx` (pdf.py) now tries `from pdf2docx import Converter`; on
`ImportError` it falls back to LibreOffice headless (`soffice
--infilter=writer_pdf_import --convert-to docx`) [@pdf-py]. The change was
documented in the README, `AGENTS.md`, and the "Unreleased" section of
`CHANGELOG.md` [@changelog][@readme].

## Consequences

- A **default install no longer includes PyMuPDF** (AGPL). Only `uv sync --extra
  docx` adds it.
- The LibreOffice fallback **lands text in text boxes**, so the DOCX is far less
  editable and cannot reconstruct the original layout. The `docx` extra is
  required for real layout reconstruction; without it the tool still produces a
  usable but poorly-laid-out `.docx`.
- `uv.lock` **still lists PyMuPDF**, because the lockfile records optional
  extras. A normal `uv sync` does not install it, so the lockfile entry is
  informational only.
- Release **`v0.1.0` was published before this change** and still bundles
  `pdf2docx` as a required dependency. It was not backported to that release.
- Publishing to PyPI is declined partly because of the AGPL dependency (and the
  lack of a stdio mode), so the copyleft question never becomes a distribution
  problem.

## Gotcha: the fallback is silent

`to_docx` swallows the `ImportError` and returns the LibreOffice result without
an error. A caller that expects an editable DOCX with preserved layout gets a
valid file that puts text in boxes, with no failure surfaced. Install the `docx`
extra when layout matters; do not assume a missing `pdf2docx` import means the
tool failed.

## Related

- The Office toolkit also gained `office_inspect` and `office_edit` (OfficeCLI,
  [`brew install officecli`](https://github.com/iOfficeAI/OfficeCLI)) and
  `url_to_markdown` (Firecrawl, the only tool that leaves the machine)
  [@office-py]. See [toolkit pattern](../architecture/toolkit-pattern).
- `pdf_to_markdown` and `office_to_markdown` convert to Markdown via `anydoc`;
  they do not produce DOCX and are not affected by this decision.
