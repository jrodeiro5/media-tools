---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
generated: { by: openwiki/xsub_mimo-v2.5, at: 2026-09-20T19:51:25.332Z }
---
# Files

- [AI Document Tools](ai.md) - 3 AI-powered document tools exposed via the MCP server: document_summarize, document_qa, and document_translate. They read a document via anydoc and call an LLM through a local LiteLLM proxy (Gemma 4). No CLI commands.
- [Audio Tools](audio.md) - 7 audio processing methods (5 exposed via CLI, 7 via MCP): convert, trim, fade, speed, info, plus merge and normalize. Uses pydub for format conversion and manipulation.
- [Image Tools](image.md) - 23 ImageToolkit methods plus image_to_video (VideoToolkit.slideshow), yielding 24 MCP tools tagged image and 22 CLI subcommands. Covers format conversion, resize, compress, crop, rotate, flip, text overlay, border, merge, blur, watermark, collage, OCR, info, remove_background, grayscale, sharpen, circle_crop, split_tiles, upscale, blur_faces, apply_brand, export_social_pack, and image_to_video. Supports jpg, png, webp, gif, bmp, tiff, ico, heic, heif, avif.
- [Office Tools](office.md) - 2 Office document tools exposed via the MCP server and CLI: office_to_markdown (converts 14 Office/text formats to Markdown via firecrawl-anydoc) and office_to_pdf (converts Office documents to PDF via LibreOffice soffice headless).
- [PDF Toolkit](pdf.md) - 26 PDF processing methods in PDFToolkit — 21 exposed via the CLI and 20 via the MCP server, with ocr and crop implemented but not wired to either interface. Covers merge, split, compress, text/image/structured/screenshots extraction, rotate, info, watermark, page numbers, protect/unlock, sign, fill form, compare, PDF/A, reorder/delete, Markdown export, PDF-to-DOCX, and redaction.
- [Text-to-Speech](tts.md) - 1 MCP tool (text_to_speech) that converts text to speech locally via a LiteLLM proxy running the Kokoro TTS model. No API key, no network egress. Supports wav (native) and mp3 (via pydub/ffmpeg). No CLI command.
- [Video Tools](video.md) - 23 video processing methods — 21 exposed via video-tagged MCP tools, plus image_to_video (image tag) and audio_to_video (audio tag); 19 reachable through the CLI media-tools video subcommands. Covers format conversion, trimming, compression, GIF creation, probing, frame extraction, cropping, rotation, resizing, reversal, speed changes, merging, thumbnails, contact sheets, watermarks, subtitle burning, social-pack export, chroma keying, and object erasure. Uses ffmpeg and OpenCV.
