# Contributing

## Setup

```bash
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install
```

## Before opening a PR

- Run `pre-commit run --all-files` — ruff, ruff-format, bandit, mypy, semgrep,
  and gitleaks all need to pass.
- Add or update tests for behavior you change.
- Keep tools scoped to their toolkit (`src/media_tools/tools/<category>.py`)
  and register new MCP tools with a category tag in `server.py`.

## Adding a new tool

1. Implement it as a static method on the relevant `*Toolkit` class in
   `src/media_tools/tools/`.
2. Expose it in `server.py` with `@mcp.tool(name=..., tags={"<category>"})`.
3. Add a CLI subcommand in `cli.py` if it makes sense as a standalone command.
4. Update the tool count/list in `README.md`.

## Reporting bugs / requesting features

Open a GitHub issue using the provided templates.
