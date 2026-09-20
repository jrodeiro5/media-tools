---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: "Reference"
title: "Inputs and output"
openwiki_generated: true
verified:
  - by: openwiki/0.5.2
    at: 2026-09-19T19:14:37.934Z
sources:
  - id: openwiki-source-f7be093be4a966caaa381229
    resource: repo://src/media_tools/utils.py
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
---



The media-tools package centralizes input validation, output-directory handling, and error reporting in `src/media_tools/utils.py`. Every toolkit method — regardless of toolkit — follows the same contract: it calls `validate_input` then `validate_output_dir` up front, and on any failure returns a plain `'Error: ...'` string instead of raising. This keeps the 50+ tools (exposed through the MCP server in `src/media_tools/server.py` and the agent-native CLI in `src/media_tools/cli.py`) free of exception propagation, so callers get a uniform, JSON-serializable result string.

## The validation contract

The contract is enforced informally but uniformly across the toolkits. Each public toolkit method begins with:

```python
err = validate_input(input_path)
if err:
    return err
...
err = validate_output_dir(output)
if err:
    return err
```

The order matters: the input is validated before the output directory, and validation happens before any side effect (file writes, subprocess spawns, model calls). Most methods return early on the first error, so a bad input never reaches the work phase.

### `validate_input`

`validate_input(path, label="input")` returns an error string if the path is invalid, otherwise `None`. It performs four checks in sequence:

1. **Empty check** — a blank or whitespace-only path returns `"{label} path is empty"`.
2. **URL passthrough** — any path starting with `http://` or `https://` is accepted immediately (`return None`). This is what allows Firecrawl and LiteLLM-based tools to accept remote document URLs without tripping the file-system checks below.
3. **Path-traversal blocking** — the path is split with `pathlib.Path(path).parts`, and if any component equals `'..'` the call returns `"{label} path contains '..' — path traversal blocked: {path}"`. This is the core path-traversal defense: `../../etc/passwd` and similar escapes are rejected outright, before existence is even checked.
4. **Existence / file / readability** — the path must `exists()`, `is_file()`, and pass `os.access(path, os.R_OK)`, yielding `"does not exist"`, `"is not a file"`, or `"is not readable"` messages respectively.

Because the `'..'` check runs before the `exists()` check, traversal attempts are reported as traversal attempts rather than "does not exist" — a deliberate ordering that surfaces the security intent in error output.

### `validate_output_dir`

`validate_output_dir(path, label="output")` returns an error string if the output location cannot be written, otherwise `None`. It derives the target directory (`p.parent` if the path has a suffix, else the path itself), creates it with `Path.mkdir(parents=True, exist_ok=True)` when absent (catching `OSError` and returning `"cannot create output directory ..."`), and finally checks `os.access(str(parent), os.W_OK)`, returning `"output directory is not writable"` when it fails. The auto-create step means callers can pass a not-yet-existing nested directory without pre-creating it.

### `safe_basename`

A small helper, `safe_basename(path)`, returns `Path(path).name`, stripping any parent components. It is used where only a filename is wanted and path traversal must not leak through.

## The `'Error: ...'` return-string convention

Rather than raising exceptions, toolkit methods return strings. Successful operations return a human-readable status string (e.g. `"Merged N files into ..."`), while failures return a string beginning with the literal prefix `"Error: "`. This convention is used pervasively:

- **Validation failures** return the exact strings from `validate_input` / `validate_output_dir` (which do not all carry the `"Error: "` prefix — e.g. `"{label} path is empty"`), but they are still treated as failures by callers checking `if err:`.
- **Runtime failures** are wrapped in `f"Error: {exc}"` inside `except` blocks.
- **Domain-specific guards** return `"Error: ..."` for precondition violations that validation cannot catch — for example `reorder_pages` / `delete_pages` returning `"Error: page {p} out of range (1-{total})"`, `unlock` returning `"Error: PDF is not password-protected"`, `watermark` returning `"Error: specify either text or image_path"`, and `pdf_to_a` returning `"Error: Ghostscript (gs) not found..."`.

The CLI layer (`_result` / `_error` in `src/media_tools/cli.py`) distinguishes success from failure by JSON structure: a raw string is wrapped as `{"result": value}` while an error is wrapped as `{"error": msg}`. The convention's reliability therefore depends on toolkit methods consistently prefixing machine-facing errors with `"Error: "`.

## The subprocess-with-logging helper

`_subprocess_with_logging(cmd, description)` is a private helper in `utils.py` that runs an external command and returns a `(result_string, success)` tuple — `(description, True)` on success, or `("Error: <stderr>", False)` when the return code is non-zero. It logs the command at debug level and the outcome at info/error level, so subprocess failures surface the stderr text in the returned string.

Toolkits that shell out to external binaries use this helper:

- **PDF/A conversion** (`pdf_to_a`) runs Ghostscript (`gs`) and, if `_subprocess_with_logging` returns `ok=False`, returns the `"Error: ..."` string it produced. If Ghostscript is missing, `FileNotFoundError` is caught and converted to `"Error: Ghostscript (gs) not found..."`.
- **Office-to-PDF** (`to_pdf`) runs LibreOffice (`soffice --headless --convert-to pdf ...`) through the helper and returns its result string on failure.
- **Video toolkits** route `ffmpeg` operations (convert, trim, compress, gif, crop, rotate, resize, reverse, speed, merge, watermark, subtitle burn, speed) through the helper.

### Inconsistent subprocess handling

Not every external command goes through `_subprocess_with_logging`. Two notable exceptions:

- **Firecrawl parse** (`pdf_to_markdown`) invokes `npx firecrawl parse ...` with a raw `subprocess.run(..., timeout=120)`. It handles the return code, API-key/401 and rate-limit messages, `subprocess.TimeoutExpired`, and `FileNotFoundError` by hand, each returning a distinct `"Error: ..."` string. It does **not** use the logging helper.
- **Video `probe`** runs `ffprobe` with a raw `subprocess.run` and returns `f"Error: {result.stderr}"` on failure.

This means the `(result_string, success)` contract is not applied uniformly to every subprocess call — some paths rely on ad-hoc return-code checks.

## URL passthrough (Firecrawl / LiteLLM)

`validate_input`'s URL passthrough is what lets document-processing tools accept remote URLs. `PDFToolkit.pdf_to_markdown` passes a URL straight through `validate_input` and then hands it to the Firecrawl CLI. Similarly, `AIToolkit` (in `src/media_tools/tools/ai.py`) accepts URLs: it reads the document via `anydoc.to_markdown`, then calls an LLM through a LiteLLM proxy (`_get_lite_llm_url`, defaulting to `http://localhost:4000`) and model (`_get_model`, defaulting to `local-gemma4-e4b-vision`). Both `summarize` and `qa` call `validate_input` first, and both internally check for a `"Error:"`-prefixed document-read result before proceeding.

## Coverage and exceptions

The contract is **not** universal. Image and audio toolkits do not call `validate_input` / `validate_output_dir` — validation is concentrated in the PDF, Office, AI, and Video toolkits. Within the PDF toolkit, `info` and `compare` call only `validate_input` (they produce no output file), while `extract_text` and `summarize`/`qa` call `validate_output_dir` only when an `output` path is supplied. Methods that accept multiple inputs (e.g. `merge`, `images_to_pdf`, `sign`, `watermark`) validate each input argument in turn before validating the output directory.

## Representative test

`tests/check_redact.py` exercises the pipeline end to end: it builds a two-page PDF, calls `PDFToolkit.redact(src, out, text_patterns=["TOPSECRET"])`, and asserts the result starts with `"Redacted"`, that the secret text is gone from the output bytes, and that the second page's text remains. This covers the happy path of a method that runs `validate_input` / `validate_output_dir` and then rasterizes/redacts pages.
