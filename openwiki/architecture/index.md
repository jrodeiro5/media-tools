---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
generated: { by: openwiki/local-ornith-35b, at: 2026-09-19T20:06:13.453Z }
---
# Files

- [Architecture Overview](overview.md) - End-to-end request flow of media-tools — how a tool call travels from FastMCP registration or the CLI dispatcher through a pure static-method toolkit, the shared validate_input/validate_output_dir and logging pipeline in utils.py, and where external dependencies (ffmpeg, LibreOffice, tesseract, LiteLLM) enter.
- [Server vs. CLI Entry Points](server-and-cli.md) - How media-tools exposes the same seven toolkits through two presentation layers — a FastMCP server (all 49 tools plus seven category-scoped servers via mcp.enable(tags)) and a hand-rolled argparse CLI dispatcher — wired by console scripts in pyproject.toml.
