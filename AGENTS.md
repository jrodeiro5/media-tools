<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **media-tools** (605 symbols, 1281 relationships, 50 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/media-tools/context` | Codebase overview, check index freshness |
| `gitnexus://repo/media-tools/clusters` | All functional areas |
| `gitnexus://repo/media-tools/processes` | All execution flows |
| `gitnexus://repo/media-tools/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

<!-- OPENWIKI:START -->

## OpenWiki

See [AGENTS.md](AGENTS.md) for OpenWiki agent instructions.

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

Atlas regenerates the entity doc from scans — hand-edits go below its
`<!-- manual -->` marker only. Source: ~/dev/infra/atlas.
<!-- atlas:end -->
 last commit, and what is
currently running out of it.

```bash
qmd get atlas/repos/media-tools.md    # this repo's entity doc
qmd query "<topic>"             # search every repo/service/config on this machine
```

Also here: `almanac/` = why it was built this way (mined decisions,
pitfalls, incidents). `openwiki/` = how it works right now (generated from
current code).

Atlas regenerates the entity doc from scans — hand-edits go below its
`<!-- manual -->` marker only. Source: ~/dev/infra/atlas.
<!-- atlas:end -->
