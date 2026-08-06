---
type: Tool Reference
title: Audio Tools
description: "5 audio processing tools: convert, trim, fade, speed, and info. Uses pydub for format conversion and manipulation."
resource: /src/media_tools/tools/audio.py
tags: [audio, tools, pydub]
---

## Overview

The `AudioToolkit` class provides 5 audio processing operations accessible via both the MCP server and CLI.

## Tool List

| MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|------------------|
| `audio_convert` | `audio convert` | Convert between formats (mp3, wav, aac, ogg, flac) | pydub |
| `audio_trim` | `audio trim` | Trim by milliseconds (start_ms, end_ms) | pydub |
| `audio_fade` | `audio fade` | Add fade-in/fade-out effects (fade_in_ms, fade_out_ms) | pydub |
| `audio_speed` | `audio speed` | Change playback speed (factor: 2.0 = double, 0.5 = half) | pydub |
| `audio_info` | `audio info` | Get metadata: duration, channels, sample rate, file size | pydub |

## Implementation Details

### Dependencies

**Required:**
- `pydub >= 0.25` — Audio processing (convert, trim, fade, speed)

### Key Implementation Notes

- **Format support**: Depends on ffmpeg installation for format conversion.
- **Bitrate**: Default 192k for conversion (configurable per format).
- **Trim**: If `end_ms=0`, trims from `start_ms` to end of file.
- **Speed**: Changes frame rate while preserving audio data.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how audio tools are exposed via MCP/CLI
- [Video Tools](/openwiki/tools/video.md) — `video_extract_audio` cross-reference
