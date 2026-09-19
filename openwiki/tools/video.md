---
type: Tool Reference
title: Video Tools
description: "17 video processing methods (7 exposed via MCP, 5 via CLI): convert, trim, compress, to_gif, probe, extract_audio, extract_frames, crop, rotate, resize, reverse, speed, merge, watermark, subtitle_burn, slideshow, audio_to_video. Uses ffmpeg, moviepy, and OpenCV."
resource: /src/media_tools/tools/video.py
tags: [video, tools, ffmpeg, moviepy, opencv]
generated: { by: openwiki/local-ornith-35b, at: 2026-08-22T14:25:15.555Z }
---

## Overview

The `VideoToolkit` class provides 17 video processing methods. Seven are exposed via the MCP server (convert, trim, compress, to_gif, probe, extract_audio, extract_frames) and five via the CLI (convert, trim, compress, to-gif, info). Several methods — crop, rotate, resize, reverse, speed, merge, watermark, subtitle_burn — are implemented but not yet wired to either interface.

## Tool List

| Method | MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|-------------|------------------|
| `convert` | `video_convert` | `video convert` | Convert between formats (extension determines codec) | ffmpeg |
| `trim` | `video_trim` | *(none)* | Trim video (HH:MM:SS times, duration OR end) | ffmpeg |
| `compress` | `video_compress` | `video compress` | Compress with CRF (18 near-lossless, 23-28 good, 51 worst) | ffmpeg |
| `to_gif` | `video_to_gif` | `video to-gif` | Convert segment to animated GIF (width, fps, start, duration) | ffmpeg |
| `probe` | `video_probe` | `video info` | Get metadata: codec, resolution, duration, bitrate | ffmpeg |
| `extract_audio` | `video_extract_audio` | *(none)* | Extract audio track (format: mp3, aac, wav, ogg, flac) | ffmpeg, pydub |
| `extract_frames` | `video_extract_frames` | *(none)* | Extract frames from video as images | OpenCV |
| `crop` *(not exposed)* | *(none)* | *(none)* | Crop video to width/height at x/y | ffmpeg |
| `rotate` *(not exposed)* | *(none)* | *(none)* | Rotate by angle (default 90°) | ffmpeg |
| `resize` *(not exposed)* | *(none)* | *(none)* | Resize video (width, height) | ffmpeg |
| `reverse` *(not exposed)* | *(none)* | *(none)* | Reverse playback | ffmpeg |
| `speed` *(not exposed)* | *(none)* | *(none)* | Change playback speed (factor) | ffmpeg |
| `merge` *(not exposed)* | *(none)* | *(none)* | Merge multiple videos | ffmpeg |
| `watermark` *(not exposed)* | *(none)* | *(none)* | Watermark video | ffmpeg |
| `subtitle_burn` *(not exposed)* | *(none)* | *(none)* | Burn subtitles into video | ffmpeg |
| `slideshow` | `image_to_video` | *(none)* | Create a video slideshow from images | MoviePy |
| `audio_to_video` | `audio_to_video` | *(none)* | Create a video with an audio track | MoviePy |

## Implementation Details

### Dependencies

**Required:**
- `ffmpeg` — System installation required (e.g., `brew install ffmpeg` on macOS)
- `moviepy >= 2.2.1` — Slideshow, audio_to_video composition
- `opencv-python-headless >= 5.0.0.93` — Frame extraction

### Key Implementation Notes

- **Codec selection**: Output codec determined by file extension.
- **CRF**: Video compression quality (18 = near-lossless, 23-28 = good, 51 = worst).
- **GIF generation**: Two-pass process (palettegen + paletteuse) for better quality.
- **Audio extraction**: Delegates to `AudioToolkit` (via pydub) for format conversion.
- **Time formats**: HH:MM:SS for trim operations.
- **Not yet exposed**: `crop`, `rotate`, `resize`, `reverse`, `speed`, `merge`, `watermark`, and `subtitle_burn` have no `@mcp.tool` or CLI registration. Wire them through `server.py` and `cli.py` to expose them.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how video tools are exposed via MCP/CLI
- [Audio Tools](/openwiki/tools/audio.md) — `video_extract_audio` cross-reference
