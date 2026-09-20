# Contributing

## Setup

```bash
uv sync --group dev              # add --extra pii for the PII tools
uvx pre-commit install
```

External binaries are not Python deps: `brew install ffmpeg tesseract officecli && brew install --cask libreoffice`.

## Before opening a PR

- Run `uvx pre-commit run --all-files` — ruff, ruff-format, bandit, mypy, semgrep,
  and gitleaks all need to pass. Fix the code; do not weaken the config.
- Tests are assert scripts, not pytest: add or update `tests/check_<area>.py` and run it with
  `.venv/bin/python tests/check_<area>.py`.
- Keep tools scoped to their toolkit (`src/media_tools/tools/<category>.py`)
  and register new MCP tools with a category tag in `server.py`.
- Tools stay local-first and never write in place; anything that calls a cloud service must say so in its docstring and README row.

## Adding a new tool

1. Implement it as a static method on the relevant `*Toolkit` class in
   `src/media_tools/tools/`.
2. Expose it in `server.py` with `@mcp.tool(name=..., tags={"<category>"})`.
3. Add a CLI subcommand in `cli.py` if it makes sense as a standalone command.
4. Update the tool count/list in `README.md`.

## Reporting bugs / requesting features

Open a GitHub issue using the provided templates.
