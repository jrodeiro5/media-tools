# Backlog — path to iLovePDF/iLoveIMG/TinyWow tool parity

Scope: MCP+CLI tool gaps only. No web UI/hosting — that's a different product.

## OCR (researched via Brave/Firecrawl, 2026-08-09)

Currently: `pytesseract` is a dependency but unused — no OCR-output tool exists yet
(`pdf_extract_text` only reads embedded text, fails on scanned/image PDFs).

| Option | What it is | License/cost | Fit here |
|---|---|---|---|
| **Tesseract (pytesseract)** | Classic OCR engine, already a dep | Apache-2.0, free, local, no GPU | Lightest — wire existing dep into a `pdf_ocr` / `image_ocr` tool. Lower accuracy on complex layout/tables. |
| **MinerU** (opendatalab) | VLM+OCR document parser, PDF/DOCX/PPTX/XLSX→MD/JSON, 109 languages, MCP server built-in, SOTA on OmniDocBench | Custom license (commercial-use clauses since Apr 2026), CLA required | Best accuracy, but pulls in VLM model weights + optional GPU backend — heavy dependency for what's currently a lean toolkit |
| **OpenDataLoader PDF** | PDF→AI-ready data, built-in OCR 80+ langs, hybrid mode (routes only complex pages to a backend/LLM, keeps simple pages local) | Open-source (Apache-2.0-style) | Good middle ground — JVM-based (Java dependency), but hybrid mode keeps most work local/cheap |
| **Baidu PaddleOCR** | Mature OSS OCR+doc parsing toolkit, 80+ langs, table extraction, API/MCP service | Apache-2.0 | Comparable to MinerU on tables; PaddlePaddle framework dependency (heavier install than Tesseract) |
| **Baidu Unlimited-OCR** | New (2026) "one-shot long-horizon parsing" model, served via sglang/OpenAI-compatible API | Model weights, self-hosted or API | Needs a served model (sglang), not a pip-install-and-go — infra cost, best treated as a future upgrade path if local OCR proves insufficient |

**Recommendation:** ship `pdf_ocr`/`image_ocr` on Tesseract first (zero new deps, YAGNI — the tool already sits unused). Revisit MinerU/OpenDataLoader/PaddleOCR only if Tesseract's accuracy on real inputs proves insufficient (tables, handwriting, non-Latin scripts). Benchmark reference: OmniDocBench (opendatalab/OmniDocBench, CVPR 2025) — current SOTA ~94.6% (GLM-OCR).

## PDF

- [ ] `pdf_ocr` — OCR scanned/image PDF → searchable PDF or text (Tesseract, see above)
- [ ] `pdf_to_pptx`, `pdf_to_xlsx`
- [ ] `pdf_crop` — crop page margins
- [ ] `pdf_repair` — fix corrupt/malformed PDFs
- [ ] `html_to_pdf`
- [ ] fix dead code: `pdf.py` has 6 duplicate method defs (`add_page_numbers`, `protect`, `unlock`, `images_to_pdf`, `reorder_pages`, `delete_pages`) — flagged, not yet cleaned, needs go-ahead

## Image

- [x] `image_ocr` — already shipped (`ImageToolkit.ocr`), note was stale
- [x] `image_rotate` — already shipped (`ImageToolkit.rotate`), note was stale
- [ ] `image_watermark`
- [ ] `image_upscale` — AI upscale/enhance
- [ ] `image_to_ico` — favicon/ICO export
- [ ] `image_collage`

## Video

- [x] `video_merge`, `video_crop`, `video_rotate`, `video_resize`, `video_watermark`, `video_reverse`, `video_speed`, `video_subtitle_burn` — implemented 2026-08-09 in `VideoToolkit` (ffmpeg-based, same pattern as `trim`/`compress`). **Not yet wired into `server.py`/`cli.py`** — those files have a large uncommitted rewrite in progress, left untouched; wire in once that rewrite lands.
- [ ] `transcribe` — video/audio → text (whisper or similar; separate research needed before picking a model)

## Audio

- [ ] `audio_merge` — join clips
- [ ] `audio_normalize` — volume normalize
- [ ] `transcribe` — shared with video, see above

## Cross-cutting

- [ ] Batch/zip multi-file output for any tool that produces >1 file
- [ ] Known bug fixed 2026-08-09: `video.py` `audio_to_video` used moviepy v1 API (`set_audio`, removed in v2) — now `with_audio`

## Security/version audit (2026-08-09)

- bandit: 6 Low/High-confidence findings, all `subprocess` usage (ffmpeg/ffprobe/firecrawl CLI wrappers, list-form args, no `shell=True`) — non-exploitable, no action.
- hexora: 3 matching `HX3010` findings (same subprocess pattern), ML score 0.01 each — no action.
- pip-audit (run against project `.venv`, not a throwaway uv-tool env — first pass falsely reported clean because it hit the wrong interpreter): found 47 real CVEs across 9 packages. Fixed by upgrading in `.venv` + bumping floors in `pyproject.toml`: `mcp` 1.27.2→1.29.0 (capped `<2`, see below), `pypdf` 6.13.0→6.15.0, `fastmcp` 3.4.2→3.4.6, `rembg` 2.0.69→2.0.75 (venv-only, see below), `cryptography`/`protobuf`/`pydantic-settings`/`setuptools`/`starlette` bumped transitively. Re-audit: clean.
- **`mcp` 2.0.0 exists and is real** — stable release for the [2026-07-28 MCP spec revision](https://blog.modelcontextprotocol.io/posts/2026-07-28/) (stateless protocol, renamed core classes). `fastmcp` (latest 3.4.6) does not support it yet — importing `media_tools.server` breaks under mcp 2.x. Pinned `mcp>=1.29.0,<2` until fastmcp ships v2 support; re-check periodically.
- **Residual risk, not fixed**: `Pillow` stays on the vulnerable 11.3.0 per `uv.lock` because `moviepy==2.2.1` (latest available) hard-pins `pillow<12`, and `rembg>=2.0.75`'s fix requires `pillow>=12.1.0` — those two constraints are mutually exclusive for a from-scratch `uv sync`. Manually upgraded Pillow to 12.3.0 and rembg to 2.0.75 in the live `.venv` only (verified moviepy still imports/runs fine at runtime despite the metadata conflict); `pyproject.toml`/`uv.lock` floors left at the old values since they can't resolve otherwise. Revisit if moviepy ships a pillow<13 release, or drop moviepy in favor of ffmpeg-only implementations for `slideshow`/`audio_to_video`.
- **Pre-existing, unrelated to this audit**: `uv.lock` is already stale against `pyproject.toml`'s uncommitted dev-dependency WIP (`complexipy>=6.2` isn't in the lock at all) — a fresh `uv lock` fails today even without any of my version bumps, due to a `complexipy`/`semgrep`/`tomli` conflict. Not touched; needs its own fix pass on the CLI/server rewrite WIP.
- ctx7/Context7 not run — the pip-audit + WebSearch findings above already answered the version-currency question directly.
- **Verdict: not "perfect."** No exploitable security findings and dependencies are now patched (in the running venv) with no known CVEs, but: 86 pre-existing mypy errors on HEAD, uncommitted cli.py/server.py/pyproject.toml rewrite in progress, Pillow/rembg/moviepy version deadlock above, and the ~20 open tool-gap items elsewhere in this backlog remain.
