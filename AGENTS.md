# media-tools

MCP server (FastMCP, streamable-http, no stdio) plus a homegrown argparse CLI over the same toolkits: PDF, image, audio, video, Office, PII, AI, TTS, batch sweep. 90 tools; `src/media_tools/tools/*.py` hold the toolkits, `server.py` registers them (tagged by family), `cli.py` mirrors most of them.

## Commands

- Setup: `uv sync --group dev` (add `--extra pii` for Presidio). Run: `uv run media-tools-server` (`PORT`, default 8020); scoped: `media-tools-server-{pdf,image,audio,video,office,ai,tts}`.
- `MEDIA_TOOLS_SEARCH=1` exposes only `search_tools` + `call_tool` (BM25) instead of all tools.
- Checks: `uvx pre-commit run --all-files` (ruff, mypy, bandit, semgrep, gitleaks). Tests are assert scripts, no pytest: `.venv/bin/python tests/check_*.py`.

## Rules

- Local-first: files never leave the machine. The one exception is `url_to_markdown` (Firecrawl cloud, `FIRECRAWL_API_KEY` from the environment, never a literal key). Keep new tools local unless flagged like that.
- Never edit in place: outputs go to a new path (`office_edit`, `batch_sweep`, `returns_reclaim` all refuse to overwrite).
- External binaries, not Python deps: ffmpeg, tesseract, LibreOffice (`soffice`), `officecli` (`brew install officecli`), `firecrawl` CLI. Tools return `Error: ...` strings when one is missing.
- A new tool needs: toolkit method, `@mcp.tool` in `server.py` with a family tag, a CLI command if it fits, a README table row, and one `tests/check_*.py` assert.
- Don't weaken bandit/mypy config to pass hooks; fix the code. `pdf2docx` (PyMuPDF, AGPL-3.0) lives in the optional `docx` extra; without it `pdf_to_docx` falls back to LibreOffice.
- `AGENTS.md` and `CLAUDE.md` are one file (`CLAUDE.md` is a git symlink to `AGENTS.md`); edit either, never split them. Keep this section above the generated blocks below.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **media-tools** (671 symbols, 1305 relationships, 56 execution flows).

> Index stale? Run `node .gitnexus/run.cjs analyze --index-only` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? Bootstrap with `npx`, `bunx`, or `pnpm dlx` — e.g. `bunx gitnexus@latest analyze` (npm 11 npx crash; #1939).

## Always Do

- **MUST run impact before editing.** Use `impact({target: "symbolName", direction: "upstream"})` or `node .gitnexus/run.cjs impact "symbolName" --direction upstream --repo .`; report callers, processes, and risk. Never substitute grep for graph analysis.
- **MUST analyze graph changes before committing.** Use `detect_changes({scope: "all"})` (MCP) or `node .gitnexus/run.cjs detect-changes --scope all --repo .` (CLI fallback). `partial: true` or `truncated: true` is not a clean check — a zero means unseen, not unaffected; re-run it. For regression review: `detect_changes({scope: "compare", base_ref: "main"})` or `node .gitnexus/run.cjs detect-changes --scope compare --base-ref "main" --repo .`.
- MUST warn on HIGH/CRITICAL `risk` pre-edit; never use `riskSharedAxes` to waive a HIGH/CRITICAL `risk` warning. Compare File/symbol: MCP File omits axes; Graph-RAG expands File.
- **MUST treat `risk: UNKNOWN` as unresolved, not as low.** An empty caller set is not evidence the symbol is unused — it can also mean the callers are not resolvable by the index (plain-object property access, dynamic dispatch, cross-language calls). `impact` pairs `UNKNOWN` with a `riskNote` saying so. Confirm with a text search before treating the symbol as safe to change or delete; do not proceed on the strength of a zero.
- **MUST use `query({search_query: "concept"})` for concepts/flows, `context({name: "symbolName"})` for a named symbol, or `impact` for blast radius, on read-only callers, dependencies, imports, or execution flow.** Graph first; text search only for empty/`UNKNOWN`/literals.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method before MCP/CLI impact analysis.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis, and never read `UNKNOWN` as an all-clear — it means the walk could not answer, which is the one verdict that requires confirming by other means.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit before MCP/CLI graph change analysis.

## Resources

| Resource | Use for |
| --- | --- |
| `gitnexus://repo/media-tools/context` | Codebase overview, check index freshness |
| `gitnexus://repo/media-tools/clusters` | All functional areas |
| `gitnexus://repo/media-tools/processes` | All execution flows |
| `gitnexus://repo/media-tools/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
| --- | --- |
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

<!-- OPENWIKI:START -->

## OpenWiki

This repository has a generated `openwiki/` evidence index. It is optional just-in-time context, not required startup reading.

- Treat source code and tests as authoritative. A brief's unknowns and review items are verification gaps, not automatic requirements.
- Prefer the narrowest quiet validation that proves the changed behavior. Preserve complete failure output.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->

<!-- atlas:start -->
## Atlas — machine-wide context

Atlas maps every repo, service and config dir on this machine. This one's entity
doc carries its role, stack, services, CI state, last commit, and what is
currently running out of it.

```bash
qmd get atlas/repos/media-tools.md    # this repo's entity doc
qmd query "<topic>"             # search every repo/service/config on this machine
```

Also here: `almanac/` = why it was built this way (mined decisions,
pitfalls, incidents). `openwiki/` = how it works right now (generated from
current code).

### Qué NO editar aquí

Tres cosas de este repo las escribe la máquina, no tú:

- `openwiki/` — regenerado por el cascade en cada commit (modelo local). Editarlo a
  mano no se pierde al instante: se pierde en el siguiente commit, sin avisar.
  ¿Falta algo? Arréglalo en el código o en los docs, y deja que se regenere.
- `almanac/` — lo mina CodeAlmanac y lo auto-commitea. Tus ediciones van **sólo**
  bajo su marker `<!-- manual -->`; por encima, se reescriben.
- `AGENTS.md` — symlink a `CLAUDE.md` (algún repo lo lleva como fichero real, por
  convención): edita `CLAUDE.md`. El cascade lo sustituye por una copia real mientras
  genera y lo restaura al terminar, así que un `T` transitorio en `git status` es ese
  swap, no corrupción.

Los hooks (`pre-commit` = gitleaks, `post-commit` = este cascade) son de atlas y
compartidos por todos los repos de la máquina: no los edites aquí.

Atlas regenerates the entity doc from scans — hand-edits go below its
`<!-- manual -->` marker only. Source: ~/dev/infra/atlas.
<!-- atlas:end -->
