---
type: Tool Reference
title: Video Tools
description: "6 video processing tools: convert, trim, compress, to_gif, probe, and extract_audio. Uses ffmpeg for all operations."
resource: /src/media_tools/tools/video.py
tags: [video, tools, ffmpeg]
---

## Overview

The `VideoToolkit` class provides 6 video processing operations accessible via both the MCP server and CLI.

## Tool List

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `video_convert` | `video convert` | Convert between formats (extension determines codec) | ffmpeg |
| `video_trim` | `video trim` | Trim video (HH:MM:SS times, duration OR end) | ffmpeg |
| `video_compress` | `video compress` | Compress with CRF (18 near-lossless, 23-28 good, 51 worst) | ffmpeg |
| `video_to_gif` | `video to-gif` | Convert segment to animated GIF (width, fps, start, duration) | ffmpeg |
| `video_probe` | `video probe` | Get metadata: codec, resolution, duration, bitrate | ffmpeg |
| `video_extract_audio` | `video extract-audio` | Extract audio track (format: mp3, aac, wav, ogg, flac) | ffmpeg, pydub |

## Implementation Details

### Dependencies

**Required:**
- `ffmpeg` — System installation required (e.g., `brew install ffmpeg` on macOS)

### Key Implementation Notes

- **Codec selection**: Output codec determined by file extension.
- **CRF**: Video compression quality (18 = near-lossless, 23-28 = good, 51 = worst).
- **GIF generation**: Two-pass process (palettegen + paletteuse) for better quality.
- **Audio extraction**: Delegates to `AudioToolkit` (via pydub) for format conversion.
- **Time formats**: HH:MM:SS for trim operations.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how video tools are exposed via MCP/CLI
- [Audio Tools](/openwiki/tools/audio.md) — `video_extract_audio` cross-reference
