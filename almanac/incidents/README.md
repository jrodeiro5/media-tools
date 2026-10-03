---
title: Incidents
topics: [incidents]
---

Incident pages record a security audit or operational event performed on this
machine, plus the reusable procedure for checking whether the machine is still
affected. They are operational runbooks, not architecture.

This folder holds one audit:

- [keyv/Cacheable npm worm (Shai-Hulud) — machine audit](../incidents/keyv-npm-worm-audit) — what the worm did, the six-step check that was run on Aug 5 2026, and the finding (machine clean).

If a new supply-chain or hook-tampering incident arises, reuse the audit's
six-step procedure rather than writing a new check from scratch: identify the
affected package names, check global packages, scan `node_modules` for a
malicious `setup.mjs`, inspect `.claude/hooks` and `.vscode/tasks.json`, then
scan `package-lock.json` files for compromised versions.
