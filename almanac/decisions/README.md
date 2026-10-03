---
title: Decisions
topics: [decisions]
---

Decision pages record one architecturally meaningful choice so future
maintainers do not have to accept or reverse it blindly. Each page states the
context, the decision, the status, and the consequences future work must
respect.

This folder holds the choices that shaped media-tools' dependency and
platform boundaries:

- [pdf2docx moved to an optional docx extra (AGPL PyMuPDF)](../decisions/docx-optional-extra) — why a required AGPL-3.0 dependency was demoted to an optional extra, and the silent LibreOffice fallback that hides the layout loss.
- [Local TTS uses Kokoro, not Chatterbox](../decisions/local-tts-kokoro-not-chatterbox) — why a non-autoregressive model was chosen over an autoregressive one that silently ran away on Spanish.

Both decisions are about avoiding a dependency or model that fails in a way the
code cannot surface at call time: AGPL copyleft carried in a required install,
and an autoregressive TTS model that returns noise with an HTTP 200. Both tie
to the [toolkits](../architecture/toolkit-pattern) that implement the affected
tools.

Read the [toolkit pattern](../architecture/toolkit-pattern) first if you are
changing a tool's dependencies — the consequences in each decision page describe
what future work must preserve.
