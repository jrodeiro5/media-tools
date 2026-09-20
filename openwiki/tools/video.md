---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Tool Reference
title: Video Tools
description: "17 video processing methods — 7 exposed via MCP (video_convert, video_trim, video_compress, video_to_gif, video_probe, video_extract_audio, video_extract_frames), 3 more via the CLI (convert, trim, compress, to-gif, info), and 3 implemented but unexposed (crop, rotate, resize). Provides convert, trim, compress, GIF, probe, audio extraction, OpenCV frame extraction, MoviePy slideshow and audio_to_video. Uses ffmpeg, moviepy, and OpenCV."
resource: /src/media_tools/tools/video.py
tags: [video, tools, ffmpeg, moviepy, opencv]
verified:
  - by: openwiki/0.5.2
    at: 2026-09-19T19:14:37.934Z
sources:
  - id: openwiki-source-f24618d3fb91081293690cc3
    resource: repo://src/media_tools/cli.py
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-5d693fa860b270ba3e69348c
    resource: repo://src/media_tools/tools/video.py
generated: { by: "openwiki/0.5.2", at: "2026-09-19T19:14:37.934Z" }
---

## Overview

The `VideoToolkit` class provides 17 video processing methods. The core operations (convert, trim, compress, to_gif, probe, extract_audio, extract_frames) are exposed through the MCP server as `video_convert`, `video_trim`, `video_compress`, `video_to_gif`, `video_probe`, `video_extract_audio`, and `video_extract_frames`. Five of these — convert, trim, compress, to-gif, and info — are additionally reachable through the CLI `media-tools video …` subcommands. The remaining composition tools (`slideshow` → `image_to_video`, `audio_to_video`) are wired to the MCP server, while `crop`, `rotate`, and `resize` are implemented but not yet wired to either interface.

The toolkit has one contract: every method returns a human-readable string and **never raises** — failures surface as `"Error: …"` results. Each method runs the same validation gate first (`validate_input` then `validate_output_dir`) and then shells out to ffmpeg, ffprobe, or (for the composition tools) MoviePy/OpenCV via `_subprocess_with_logging`.

## Tool List

| Method | MCP Name | CLI Command | Description | Key Dependencies |
|----------|-------------|-------------|-------------|------------------|
| `convert` | `video_convert` | `video convert` | Convert between formats (extension determines codec) | ffmpeg |
| `trim` | `video_trim` | `video trim` | Trim video (HH:MM:SS, `--start`/`--end`) | ffmpeg |
| `compress` | `video_compress` | `video compress` | Compress with CRF (18 near-lossless, 23-28 good, 51 worst) | ffmpeg |
| `to_gif` | `video_to_gif` | `video to-gif` | Convert segment to animated GIF (width, fps, start, duration) | ffmpeg |
| `probe` | `video_probe` | `video info` | Get metadata: codec, resolution, duration, bitrate | ffprobe |
| `extract_audio` | `video_extract_audio` | *(none)* | Extract audio track (format: mp3, aac, wav, ogg, flac) | ffmpeg |
| `extract_frames` | `video_extract_frames` | *(none)* | Extract frames from video as images | OpenCV |
| `crop` *(not exposed)* | *(none)* | *(none)* | Crop video to width/height at x/y | ffmpeg |
| `rotate` *(not exposed)* | *(none)* | *(none)* | Rotate by angle (90/180/270°) | ffmpeg |
| `resize` *(not exposed)* | *(none)* | *(none)* | Resize video (width, height) | ffmpeg |
| `reverse` *(not exposed)* | *(none)* | *(none)* | Reverse playback | ffmpeg |
| `speed` *(not exposed)* | *(none)* | *(none)* | Change playback speed (factor) | ffmpeg |
| `merge` *(not exposed)* | *(none)* | *(none)* | Merge multiple videos | ffmpeg |
| `watermark` *(not exposed)* | *(none)* | *(none)* | Watermark video | ffmpeg |
| `subtitle_burn` *(not exposed)* | *(none)* | *(none)* | Burn subtitles into video | ffmpeg |
| `slideshow` | `image_to_video` | *(none)* | Create a video slideshow from images | MoviePy |
| `audio_to_video` | `audio_to_video` | *(none)* | Create a video with an audio track | MoviePy |

## Wiring

**MCP server** (`/src/media_tools/server.py`): The seven core tools are top-level `@mcp.tool` functions that delegate directly to `VideoToolkit` (e.g. `video_convert` → `VideoToolkit.convert`). The composition tools import `VideoToolkit` lazily inside the function body — `image_to_video` → `slideshow`, `video_extract_frames` → `extract_frames`, `audio_to_video` → `audio_to_video` — and are tagged `image`, `video`, and `audio` respectively. `main_video()` runs the server scoped to the `video` tag only (`_run_scoped("video")`).

**CLI** (`/src/media_tools/cli.py`): The `video` category registers five subcommands — `convert`, `trim`, `compress`, `to-gif`, `info` — each handled by a `_video_*` closure that pulls arguments from the parsed namespace. Notably the CLI `trim` passes only `start`/`end` (no `duration`), and `to-gif` passes only `width`/`fps`, so those CLI invocations fall back to the toolkit defaults.

## Implementation Details

### Dependencies

- `ffmpeg` — System installation required for every method except the MoviePy composition tools.
- `moviepy >= 2.2.1` — Imported lazily inside `slideshow` and `audio_to_video`.
- `opencv-python-headless >= 5.0.0.93` — Imported lazily inside `extract_frames`.

### Validation gate

Every method runs `validate_input(input_path)` followed by `validate_output_dir(output)` and returns the first error string. `validate_input` rejects empty paths, paths containing `..` (path traversal), and non-existent / non-file / non-readable paths, but allows `http(s)://` URLs through. `validate_output_dir` creates the parent directory if missing and rejects unwritable output. This gate is identical to the audio/image toolkits.

### `_codec_for()` — extension → codec mapping

`_codec_for(output, crf=None)` (`/src/media_tools/tools/video.py`) maps the output file extension to a fixed set of ffmpeg arguments and is called by `convert`, `compress`, `trim`, `crop`, `rotate`, `resize`, `reverse`, `speed`, `merge`, `watermark`, and `subtitle_burn`:

- `.mp4` → `-c:v libx264 -preset medium`
- `.webm` → `-c:v libvpx-vp9`
- `.mov` → `-c:v prores_ks -profile:v 3`
- `.gif` → `[]` (no codec args — GIFs are handled by `to_gif`'s two-pass flow)
- anything else → `-c:v libx264`

The mapping always appends `-c:a aac -b:a 128k` for the audio track, and when `compress` passes a `crf` value, `-crf <value>` is inserted before the audio args.

### `to_gif()` — two-pass palette flow

`to_gif` produces a higher-quality GIF with two ffmpeg passes (`/src/media_tools/tools/video.py`): the first pass renders `fps={fps},scale={width}:-1:flags=lanczos,palettegen` into a temporary `<output>.png` palette file; the second pass reuses that palette with `paletteuse`. The palette file is deleted with `Path(palette).unlink(missing_ok=True)` afterward.

### `probe()` — ffprobe JSON parsing

`probe` runs `ffprobe -v quiet -print_format json -show_format -show_streams` and parses the JSON (`/src/media_tools/tools/video.py`). It reads `format` for duration and size (formatted by `_human_size`), then finds the first `video` and `audio` stream by `codec_type`. Video is rendered as `{codec_name} {width}x{height} @ {_rframe(r_frame_rate)} fps` and audio as `{codec_name} {sample_rate}Hz {channels}ch`. `_rframe` converts an FPS fraction string (e.g. `30000/1001`) to a decimal; on parse failure it returns the raw string. A non-zero return code returns `"Error: {stderr}"`.

### `extract_frames()` — OpenCV skip_frames logic

`extract_frames` opens the video with `cv2.VideoCapture` (`/src/media_tools/tools/video.py`), creates the output directory, and computes `skip_frames = max(1, int(fps_actual / fps))` where `fps_actual` is the capture's real FPS (falling back to the requested `fps`). It seeks to `start` via `CAP_PROP_POS_MSEC`, optionally bounds the run by `start + duration`, then reads frames and saves every `skip_frames`-th frame as `frame_{NNNNNN}.png` via `cv2.imwrite`. A failure to open the file returns `"Error: Could not open video file"`; any other exception is caught and returned as `"Error: {exc}"`.

### Composition tools (MoviePy)

`slideshow` (`image_to_video`) builds one `ImageClip(p, duration=duration_per_image)` per image and concatenates them with `concatenate_videoclips(clips, method="compose")`, then `write_videofile(output, fps=fps)`; it always calls `video.close()`. `audio_to_video` pairs an `AudioFileClip` with a `VideoFileClip` via `video.with_audio(audio)` before `write_videofile`. Both wrap MoviePy in a try/except and return `"Error: {exc}"` on failure.

### Other unexposed methods

`reverse` applies `-vf reverse -af areverse`; `speed` applies `setpts={1/factor}*PTS` and `atempo={factor}` (rejecting non-positive factors); `merge` writes a concat demuxer list file and runs `ffmpeg -f concat -safe 0`; `watermark` maps a named position to an `overlay=` expression; `subtitle_burn` escapes the subtitle path and applies the `subtitles=` video filter. All use `_codec_for(output)` and the shared subprocess helper.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how video tools are exposed via MCP/CLI
- [Audio Tools](/openwiki/tools/audio.md) — `video_extract_audio` cross-reference
- [Inputs and Outputs](/openwiki/concepts/inputs-and-output.md) — input/output validation conventions
