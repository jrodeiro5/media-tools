---
type: Tool Reference
title: Audio Tools
description: "7 audio processing methods (5 exposed via CLI, 5 via MCP): convert, trim, fade, speed, info, plus merge and normalize. Uses pydub for format conversion and manipulation."
resource: /src/media_tools/tools/audio.py
tags: [audio, tools, pydub, ffmpeg]
generated: { by: openwiki/local-ornith-35b, at: 2026-08-22T14:25:15.555Z }
---

## Overview

The `AudioToolkit` class provides 7 audio processing methods. Five are exposed via the CLI (convert, trim, fade, speed, info) and five via the MCP server (convert, trim, fade, speed, info). Two methods — `merge` and `normalize` — are implemented but not yet wired to either interface.

## Tool List

| Method | MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|-------------|------------------|
| `convert` | `audio_convert` | `audio convert` | Convert between formats (mp3, wav, aac, ogg, flac) | pydub |
| `trim` | `audio_trim` | `audio trim` | Trim by milliseconds (start_ms, end_ms) | pydub |
| `fade` | `audio_fade` | `audio fade` | Add fade-in/fade-out effects (fade_in_ms, fade_out_ms) | pydub |
| `speed` | `audio_speed` | `audio speed` | Change playback speed (factor: 2.0 = double, 0.5 = half) | pydub |
| `info` | `audio_info` | `audio info` | Get metadata: duration, channels, sample rate, file size | pydub |
| `merge` *(not exposed)* | *(none)* | *(none)* | Merge multiple audio files | pydub |
| `normalize` *(not exposed)* | *(none)* | *(none)* | Normalize to a target loudness (default -20 dB) | pydub |

## Implementation Details

### Dependencies

**Required:**
- `pydub >= 0.25` — Audio processing (convert, trim, fade, speed, merge, normalize)

### Key Implementation Notes

- **Format support**: Depends on ffmpeg installation for format conversion.
- **Bitrate**: Default 192k for conversion (configurable per format).
- **Trim**: If `end_ms=0`, trims from `start_ms` to end of file.
- **Speed**: Changes frame rate while preserving audio data.
- **Not yet exposed**: `AudioToolkit.merge` and `AudioToolkit.normalize` have no `@mcp.tool` or CLI registration. Wire them through `server.py` and `cli.py` to expose them.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how audio tools are exposed via MCP/CLI
- [Video Tools](/openwiki/tools/video.md) — `video_extract_audio` cross-reference
