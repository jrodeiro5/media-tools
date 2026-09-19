---
title: Utilities
topics: [architecture]
sources:
  - id: utils-py
    type: file
    target: src/media_tools/utils.py
    title: "media_tools/utils.py — shared helpers"
---

# Utilities

`utils.py` provides shared validation, logging, and subprocess helpers used
by all toolkit classes [@utils-py].

## `validate_input(path, label="input")`

Returns an error string if the path is invalid, else `None`. Checks:

- Path is not empty
- Path does not contain `..` components (path traversal protection)
- Path exists and is a file (or is a URL — URLs pass through)

URLs are explicitly allowed because some tools (Firecrawl, LiteLLM) accept
remote resources.

## `validate_output_dir(path, label="output")`

Returns an error string if the output directory is unwritable, else `None`.
Creates parent directories if they do not exist.

## `_subprocess_with_logging(cmd, description)`

Runs a subprocess command with logging. Returns `(result_string, success)`.
Used by toolkits that wrap external CLI tools (ffmpeg, Ghostscript, etc.).

## `setup_logging(level="INFO")`

Configures the root logger for the `media_tools` package. Uses a simple
timestamped format.

## Constraints

- `validate_input` and `validate_output_dir` are imported by every
  toolkit, so changes to them affect every tool. `_subprocess_with_logging`
  is used only by toolkits that wrap external CLIs (pdf, video, office);
  image, audio, ai, and tts do not import it.
- `validate_input` allows URLs — this is intentional for tools that accept
  remote resources, but means path traversal protection does not apply to
  URLs.
- The logging setup is minimal. Production deployments should configure
  logging separately.

## Related pages

- [Toolkit pattern](../architecture/toolkit-pattern) — the classes that
  import these helpers and call them from every tool. They are the sole
  consumers, so changes here affect every tool in the repo.
