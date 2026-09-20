<p align="center"><img src="assets/logo.svg" alt="media_tools" width="480"></p>

<p align="center">
  An MCP server that lets your AI client work with PDFs, images, audio, video and Office files.<br>
  90 tools, one command to start.
</p>

<p align="center">
  <a href="https://github.com/jrodeiro5/media-tools/actions/workflows/ci.yml"><img src="https://github.com/jrodeiro5/media-tools/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-ffb02e" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-12141a" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/MCP-streamable--http-12141a" alt="MCP streamable-http">
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#tools">Tools</a> ·
  <a href="#cli">CLI</a> ·
  <a href="#development">Development</a>
</p>

<p align="center"><img src="assets/demo.svg" alt="Terminal demo: merge and compress PDFs, then start the MCP server" width="720"></p>

---

Ask your assistant to "merge these three PDFs, then compress the result" or "cut 10 seconds from this clip and make a GIF". It calls the matching tools; the files never leave your machine.

Built on [FastMCP](https://github.com/PrefectHQ/fastmcp). Works with any MCP client: Claude Desktop, OpenWebUI, Cursor and others.

## Quick start

```bash
git clone https://github.com/jrodeiro5/media-tools && cd media-tools
uv sync
uv run media-tools-server        # http://localhost:8020/mcp
```

Point your client at it. For a client that reads an `mcpServers` block:

```json
{
  "mcpServers": {
    "media-tools": { "url": "http://localhost:8020/mcp" }
  }
}
```

Set `PORT` to change the port. To expose only one family of tools (and keep the client's context small), run a scoped server: `media-tools-server-pdf`, `-image`, `-audio`, `-video`, `-office`, `-ai` or `-tts`. Or set `MEDIA_TOOLS_SEARCH=1` on the full server to list just `search_tools` + `call_tool` (~330 tokens instead of ~13.7k) and let the agent find tools by query.

## Tools

<table>
<tr><td><b>PDF</b> · 27</td><td>merge, split, compress, rotate, reorder, delete pages, watermark, page numbers, protect, unlock, sign, fill forms, compare, <b>redact</b>, returns reclaim, extract text / images / tables / screenshots / structured data, convert to Markdown, DOCX or PDF/A, images to PDF, Markdown to branded PDF, salvage</td></tr>
<tr><td><b>Image</b> · 18</td><td>convert, resize, compress, crop, rotate, flip, text overlay, border, merge, watermark, collage, blur, OCR, info, remove background, brand kit, image to video, social pack</td></tr>
<tr><td><b>Audio</b> · 12</td><td>convert, trim, fade, speed, merge, normalize, chunk on silence, transcribe, transcribe chunks, pad to duration, info, audio to video</td></tr>
<tr><td><b>Video</b> · 21</td><td>convert, trim, compress, probe, to GIF, GIF to MP4, extract audio, merge, crop, rotate, resize, watermark, reverse, speed, subtitle burn, extract frames, thumbnail, contact sheet, social pack, chroma cut, object erase</td></tr>
<tr><td><b>Office</b> · 5</td><td>to Markdown, to PDF (via LibreOffice), inspect and edit .docx/.xlsx/.pptx (via OfficeCLI), URL to Markdown (via Firecrawl, cloud)</td></tr>
<tr><td><b>PII</b> · 2</td><td>find Spanish/EU identifiers (DNI/NIF, NIE, passport, IBAN, email, phone), redact them from a PDF</td></tr>
<tr><td><b>AI</b> · 3</td><td>summarize, question answering, translate</td></tr>
<tr><td><b>Speech</b> · 1</td><td>text to speech</td></tr>
<tr><td><b>Batch</b> · 1</td><td>folder sweep: one op across every matching file, outputs to a separate dir, never in place</td></tr>
</table>

`pii_scan` and `pii_redact` need the optional extra (`uv sync --extra pii`, adds Presidio). They match by pattern and checksum, so names and addresses are not detected, and `pii_scan` returns masked previews, never the raw values.

`pdf_redact` renders the matched pages to images and paints over the matches, so the text is gone from the file, not just hidden. Those pages lose their selectable text.

<details>
<summary>Full tool names</summary>

**PDF:** `pdf_merge` `pdf_split` `pdf_compress` `pdf_extract_text` `pdf_extract_images` `pdf_extract_tables` `pdf_rotate` `pdf_info` `pdf_extract_structured` `pdf_extract_screenshots` `pdf_watermark` `pdf_page_numbers` `pdf_protect` `pdf_unlock` `images_to_pdf` `pdf_reorder_pages` `pdf_delete_pages` `pdf_sign` `pdf_fill_form` `pdf_compare` `pdf_to_a` `pdf_to_markdown` `pdf_to_docx` `pdf_redact` `returns_reclaim` `md_to_branded_pdf` `pdf_salvage`

**Image:** `image_convert` `image_resize` `image_compress` `image_crop` `image_rotate` `image_flip` `image_text` `image_border` `image_merge` `image_watermark` `image_collage` `image_blur` `image_ocr` `image_info` `image_remove_background` `image_apply_brand` `image_to_video` `image_export_social_pack`

**Audio:** `audio_convert` `audio_trim` `audio_fade` `audio_speed` `audio_merge` `audio_normalize` `audio_chunk_silence` `audio_transcribe` `audio_transcribe_chunks` `audio_pad_to_duration` `audio_info` `audio_to_video`

**Video:** `video_convert` `video_trim` `video_compress` `video_to_gif` `gif_to_mp4` `video_probe` `video_extract_audio` `video_merge` `video_crop` `video_rotate` `video_resize` `video_watermark` `video_reverse` `video_speed` `video_subtitle_burn` `video_extract_frames` `video_thumbnail` `video_contact_sheet` `video_export_social_pack` `video_chroma_cut` `video_object_erase`

**Office:** `office_to_markdown` `office_to_pdf` `office_inspect` `office_edit` `url_to_markdown`

**PII:** `pii_scan` `pii_redact`

**AI:** `document_summarize` `document_qa` `document_translate`

**Speech:** `text_to_speech`

**Batch:** `batch_sweep`

</details>

## CLI

The same toolkits run without a server:

```bash
media-tools pdf merge a.pdf b.pdf --output merged.pdf
media-tools pdf compress merged.pdf --output small.pdf
media-tools --help
```

The CLI covers most server tools, some under shorter names (`pdf reorder`, `video info`). Not in the CLI: the AI tools, `text_to_speech`, `pdf_redact`, `pdf_info`, `pdf_to_docx`, `pdf_extract_structured` / `_screenshots`, `image_remove_background`, `image_to_video`, `audio_to_video`, `video_extract_audio` and `video_extract_frames`.

## Requirements

- Python 3.11 or newer and [uv](https://github.com/astral-sh/uv)
- `ffmpeg` for audio and video, LibreOffice (`soffice`) for Office conversion, `tesseract` for OCR. On macOS: `brew install ffmpeg tesseract && brew install --cask libreoffice`
- Optional: [OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) for `office_inspect`/`office_edit` (`brew install officecli`); the Firecrawl CLI plus `FIRECRAWL_API_KEY` for `url_to_markdown` (sends the URL to Firecrawl, unlike every other tool)
- Optional: a [LiteLLM](https://github.com/BerriAI/litellm) proxy for the AI tools, text to speech, and transcription

## Development

```bash
uv sync --group dev
uvx pre-commit run --all-files   # ruff, mypy, bandit, semgrep, gitleaks
```

CI runs the same hooks on Python 3.11 and 3.13, plus CodeQL, gitleaks and zizmor. Found a vulnerability? Use the repository's private vulnerability reporting rather than a public issue.

## License

[MIT](LICENSE). The logo wordmark is outlined from [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) (SIL OFL 1.1).
