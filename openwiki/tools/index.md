---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
generated: { by: openwiki/local-ornith-35b, at: 2026-09-19T20:06:13.453Z }
---
# Files

- [AI Document Tools](ai.md) - 3 AI-powered document tools exposed via the MCP server: document_summarize, document_qa, and document_translate. They read a document via anydoc and call an LLM through a local LiteLLM proxy (Gemma 4). No CLI commands.
- [Audio Tools](audio.md) - 7 audio processing methods (5 exposed via CLI, 7 via MCP): convert, trim, fade, speed, info, plus merge and normalize. Uses pydub for format conversion and manipulation.
- [Image Tools](image.md) - 15 image processing methods (12 exposed via CLI, 7 via MCP): convert, resize, compress, crop, rotate, flip, text overlay, border, merge, blur, watermark, collage, OCR, and info. Supports jpg, png, webp, gif, bmp, tiff, ico, heic, heif, avif.
- [Office Tools](office.md) - 2 Office document tools exposed via the MCP server and CLI: office_to_markdown (converts 14 Office/text formats to Markdown via firecrawl-anydoc) and office_to_pdf (converts Office documents to PDF via LibreOffice soffice headless).
- [PDF Toolkit](pdf.md) - 26 PDF processing methods in PDFToolkit — 21 exposed via the CLI and 20 via the MCP server, with ocr and crop implemented but not wired to either interface. Covers merge, split, compress, text/image/structured/screenshots extraction, rotate, info, watermark, page numbers, protect/unlock, sign, fill form, compare, PDF/A, reorder/delete, Markdown export, PDF-to-DOCX, and redaction.
- [Text-to-Speech](tts.md) - 1 MCP tool (text_to_speech) that converts text to speech locally via a LiteLLM proxy running the Kokoro TTS model. No API key, no network egress. Supports wav (native) and mp3 (via pydub/ffmpeg). No CLI command.
- [Video Tools](video.md) - 17 video processing methods — 7 exposed via MCP (video_convert, video_trim, video_compress, video_to_gif, video_probe, video_extract_audio, video_extract_frames), 3 more via the CLI (convert, trim, compress, to-gif, info), and 3 implemented but unexposed (crop, rotate, resize). Provides convert, trim, compress, GIF, probe, audio extraction, OpenCV frame extraction, MoviePy slideshow and audio_to_video. Uses ffmpeg, moviepy, and OpenCV.
