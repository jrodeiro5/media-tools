---
generated: { by: openwiki/local-ornith-35b, at: 2026-08-22T14:25:15.555Z }
---
# Files

- [AI Document Tools](ai.md) - 3 AI-powered document tools exposed via the MCP server: document_summarize, document_qa, and document_translate. They read a document via anydoc and call an LLM through a local LiteLLM proxy (Gemma 4). No CLI commands.
- [Audio Tools](audio.md) - 7 audio processing methods (5 exposed via CLI, 5 via MCP): convert, trim, fade, speed, info, plus merge and normalize. Uses pydub for format conversion and manipulation.
- [Image Tools](image.md) - 15 image processing methods (12 exposed via CLI, 7 via MCP): convert, resize, compress, crop, rotate, flip, text overlay, border, merge, blur, watermark, collage, OCR, and info. Supports jpg, png, webp, gif, bmp, tiff, ico, heic, heif, avif.
- [Office Tools](office.md) - 2 Office document processing tools: convert to Markdown (via MarkItDown) and convert to PDF (via LibreOffice).
- [PDF Tools](pdf.md) - 23 PDF processing tools (25 toolkit methods, 2 not yet exposed via MCP/CLI): merge, split, compress, extract text/images, rotate, watermark, page numbers, protect/unlock, sign, fill forms, compare, PDF/A conversion, reorder/delete pages, Markdown export, plus OCR, crop, PDF-to-DOCX, and redaction.
- [Text-to-Speech](tts.md) - 1 MCP tool (text_to_speech) that converts text to speech locally via a LiteLLM proxy running the Kokoro TTS model. No API key, no network egress. Supports wav (native) and mp3 (via pydub/ffmpeg). No CLI command.
- [Video Tools](video.md) - 17 video processing methods (7 exposed via MCP, 5 via CLI): convert, trim, compress, to_gif, probe, extract_audio, extract_frames, crop, rotate, resize, reverse, speed, merge, watermark, subtitle_burn, slideshow, audio_to_video. Uses ffmpeg, moviepy, and OpenCV.
