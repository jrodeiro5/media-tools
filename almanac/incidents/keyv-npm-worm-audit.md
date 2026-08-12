---
title: keyv/Cacheable npm worm (Shai-Hulud) — machine audit
topics: [incidents]
sources:
  - id: kodem-ioc
    type: web
    target: https://www.kodemsecurity.com/resources/keyv-supply-chain-attack-shai-hulud-npm-worm-affected-versions-iocs-and-first-hour-response-runbook
    title: "Keyv npm Supply Chain Attack | IOCs and Runbook | Kodem"
  - id: thehackernews
    type: web
    target: https://thehackernews.com/2026/08/keyv-linked-npm-worm-poisons-hundreds.html
    title: "Keyv-Linked npm Worm Poisons Hundreds of Packages, Plants Claude Code and VS Code Hooks"
  - id: cloudsmith
    type: web
    target: https://cloudsmith.com/blog/keyv-and-cacheable-npm-packages-compromised-in-active-supply-chain-attack
    title: "Keyv and Cacheable npm Packages Compromised in Active Supply-Chain Attack | Cloudsmith"
  - id: aikido
    type: web
    target: https://www.aikido.dev/blog/keyv-and-friends-compromised-in-npm-supply-chain-attack
    title: "Keyv and friends compromised in npm supply chain attack"
  - id: socket
    type: web
    target: https://socket.dev/blog/popular-npm-packages-in-the-keyv-and-cacheable-namespaces-compromised-in-active-supply-chain
    title: "Popular npm Packages in the keyv and Cacheable Namespaces Compromised in Active Supply-Chain"
  - id: strobes
    type: web
    target: https://strobes.co/blog/keyv-cacheable-npm-supply-chain-attack/
    title: "Keyv and Cacheable npm Supply Chain Attack: What to Do | Strobes"
  - id: wiz
    type: web
    target: https://www.wiz.io/blog/keyv-and-cacheable-npm-package-hijacked-in-supply-chain-attack
    title: "keyv and cacheable npm Package Hijacked in Supply Chain Attack | Wiz Blog"
---

# keyv/Cacheable npm worm (Shai-Hulud) — machine audit

On August 4, 2026, attackers compromised the GitHub account behind the `keyv` and
`cacheable` npm namespaces and published malicious versions of those packages and
their common dependencies. The resulting self-propagating worm, tracked as
**keyv-shai-hulud**, poisoned 353 versions across 79 package names and specifically
targeted Claude Code and VS Code installations [@kodem-ioc].

This page records the audit performed on this machine (Aug 5 2026) and the
reusable procedure for checking whether the machine is affected. Multiple
security researchers independently documented the attack and its remediation:
Kodem Security published the IOC list and runbook [@kodem-ioc], Cloudsmith
analyzed the compromised namespace [@cloudsmith], Socket.dev mapped the affected
packages [@socket], Aikido published a remediation guide [@aikido], Strobes documented what to do [@strobes], and Wiz published a post-incident analysis [@wiz],
[@aikido; @strobes], and The Hacker News reported on the worm's targeting of
Claude Code and VS Code installations [@thehackernews].

## What the attack does

The worm uses a malicious `setup.mjs` preinstall hook that runs during `npm
install`. Its stages are:

1. **Seed.** Injects itself into published package versions.
2. **Download.** Fetches a standalone Bun runtime from `npm-cache.com`.
3. **Credential harvest.** Steals Git, npm, and cloud provider tokens from
   environment variables and credential stores.
4. **Exfiltration and self-propagation.** Sends stolen tokens to attacker-controlled
   infrastructure and publishes new malicious package versions to expand the
   attack surface [@kodem-ioc].

A notable persistence twist: the worm installs Claude Code and VS Code hooks that
run *without* triggering `npm install`, so simply not installing the compromised
packages does not guarantee safety if the hooks were already planted [@kodem-ioc].

## Audit procedure

The following checks were run on this machine. They are reusable for any
subsequent sweep.

### 1. Identify affected package names

The compromised packages are all within the `keyv` and `cacheable` namespaces,
plus a set of commonly depended-upon packages that were hijacked. The full list
is documented by Kodem Security [@kodem-ioc]. Key packages to check:

- `keyv` (all versions)
- `cacheable` (all versions)
- `@keyv/sqlite`, `@keyv/postgres`, `@keyv/mongo`, `@keyv/mysql`
- `@keyv/redis`, `@keyv/sqlite`, `@keyv/sqlite3`
- `@keyv/compress-gzip`, `@keyv/compress-brotli`
- `cacheable-memory`, `cacheable-lru`, `cacheable-fs`
- `@keyv/json-file`, `@keyv/sqlite`

### 2. Check global npm packages

```bash
npm ls -g --depth=0 2>&1
```

On this machine, the 5 globally installed packages
(`@firecrawl/prometheus-cli`, `@kaelio/ktx`, `@llamaindex/liteparse`,
`agentmail-cli`, `openwiki`) are clean — none are in the keyv/cacheable family.

### 3. Check local `node_modules` for malicious `setup.mjs`

```bash
find ~ -path '*/node_modules/*/setup.mjs' -not -path '*/node_modules/*' 2>/dev/null
```

Search for the malicious payload sizes (29918 bytes and 727680 bytes) and the
`bun-dl-*` temp directories the worm creates. On this machine, no malicious
`setup.mjs` was found.

### 4. Check `.claude/hooks` and `settings.json` for tampering

```bash
ls -la ~/.claude/hooks 2>/dev/null
cat ~/.claude/settings.json 2>/dev/null | grep -A3 '"hooks"'
find ~/dev -maxdepth 6 -iname "*.claude*" -name "settings.json" 2>/dev/null
```

No tampered hooks were found.

### 5. Check `.vscode/tasks.json` for folderOpen persistence

```bash
find ~ -name ".vscode" -type d -exec grep -l "folderOpen" {} \; 2>/dev/null
```

No folder-open persistence hooks found.

### 6. Check `package-lock.json` files for compromised versions

```bash
find ~/dev -name "package-lock.json" -exec grep -l "keyv\|cacheable" {} \; 2>/dev/null
```

Several personal projects reference `keyv: 4.5.4` in their lockfiles, but these
are the legitimate version (not the malicious ones). No compromised versions
detected.

## Findings

This machine was audited on August 5, 2026. Results:

- Global npm packages: clean (none in keyv/cacheable family)
- Local `node_modules`: no malicious `setup.mjs` found
- `.claude/hooks` and `settings.json`: no tampering detected
- `.vscode/tasks.json`: no folder-open persistence hooks
- `package-lock.json` files: legitimate `keyv: 4.5.4` in 5 projects, no compromised versions

The machine was determined to be clean.

## References

- [Kodem Security IOC and Runbook](https://www.kodemsecurity.com/resources/keyv-supply-chain-attack-shai-hulud-npm-worm-affected-versions-iocs-and-first-hour-response-runbook)
- [The Hacker News coverage](https://thehackernews.com/2026/08/keyv-linked-npm-worm-poisons-hundreds.html)
- [Cloudsmith analysis](https://cloudsmith.com/blog/keyv-and-cacheable-npm-packages-compromised-in-active-supply-chain-attack)
- [Aikido blog](https://www.aikido.dev/blog/keyv-and-friends-compromised-in-npm-supply-chain-attack)
- [Socket.dev blog](https://socket.dev/blog/popular-npm-packages-in-the-keyv-and-cacheable-namespaces-compromised-in-active-supply-chain)
- [Strobes response guide](https://strobes.co/blog/keyv-cacheable-npm-supply-chain-attack/)
- [Wiz blog](https://www.wiz.io/blog/keyv-and-cacheable-npm-package-hijacked-in-supply-chain-attack)
