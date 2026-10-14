---
title: Refusals — machine-readable error tickets
topics: [toolkits, architecture]
sources:
  - id: refusals-py
    type: file
    target: src/media_tools/refusals.py
    title: "media_tools/refusals.py — machine-readable refusal tickets"
  - id: office-overwrite
    type: file
    target: src/media_tools/tools/office.py
    title: "OfficeToolkit.to_docx — overwrite_blocked caller"
  - id: pdf-refusals
    type: file
    target: src/media_tools/tools/pdf.py
    title: "PDFToolkit — missing_binary / encrypted_pdf callers"
---

# Refusals — machine-readable error tickets

`src/media_tools/refusals.py` is the single module that produces every
toolkit refusal string. It defines the exact text contract for `Error: ...`
returns and a set of stable machine-readable error codes, so a future agent
(or an MCP client) can recognize *why* a tool refused without re-reading each
toolkit.

## The contract

Every refusal is a `TicketedString` — a `str` subclass whose text is
byte-identical to the historical plain `"Error: ..."` message, but which also
carries a structured `Ticket` on its `.ticket` attribute and `.to_dict()`
[@refusals-py]. Callers only `return` it, so existing string-only behavior is
preserved; the structured ticket is optional metadata for downstream agents.

Three stable codes live in `REGISTRY`:

| code | when emitted | fix_hint |
|---|---|---|
| `E_OVERWRITE_BLOCKED` | output path equals the input (edits never in place) | pass a different output path |
| `E_ENCRYPTED_PDF` | the PDF is password-protected | unlock first (`pdf_unlock`) or supply the password |
| `E_MISSING_BINARY` | an external CLI (Ghostscript `gs`) is not installed | `brew install ghostscript` / `sudo apt-get install ghostscript` |

`missing_binary(binary=...)` rewrites the hint for non-`gs` binaries, so the
binary name lives only in `remedy` (`install_binary:<name>`) and the human
hint carries the install command [@refusals-py].

## The "edits never in place" invariant

`office.py` returns `overwrite_blocked(...)` when the requested output equals
the input, so in-place edits are refused [@office-overwrite]. `pdf.py` uses
`missing_binary(...)` when Ghostscript is absent in `pdf_to_a`, and
`encrypted_pdf(...)` when `pdf_to_markdown` hits an encrypted PDF
[@pdf-refusals]. Because every refusal is a plain string, the refusal is
indistinguishable from any other `Error:` return to string-only callers — the
invariant is enforced by the code, not by a raised exception.

## Prototype status

The module docstring marks it a **prototype**: only `office.py` and `pdf.py`
are wired to it so far. The other seven toolkits still return plain
`"Error: ..."` strings directly and do not import `media_tools.refusals`.
Wiring another tool to a refusal helper means returning one of them instead of
an inline string, which also gives that tool a stable code for free.

## Related

- [Toolkit pattern](toolkit-pattern) — the classes that
  import `media_tools.refusals`.
- [CLI dispatch](cli-dispatch) and [MCP server](mcp-server) — the entrypoints that wrap these refusal strings in `{"error": ...}` JSON.
