---
authoritative: false
authority-reason: openwiki run ended status=interrupted, so these pages are part old and part new
type: Tool Reference
title: Video Tools
description: "23 video processing methods — 21 exposed via video-tagged MCP tools, plus image_to_video (image tag) and audio_to_video (audio tag); 19 reachable through the CLI media-tools video subcommands. Covers format conversion, trimming, compression, GIF creation, probing, frame extraction, cropping, rotation, resizing, reversal, speed changes, merging, thumbnails, contact sheets, watermarks, subtitle burning, social-pack export, chroma keying, and object erasure. Uses ffmpeg and OpenCV."
tags: [video, tools, ffmpeg, opencv]
sources:
  - id: openwiki-source-f24618d3fb91081293690cc3
    resource: repo://src/media_tools/cli.py
  - id: openwiki-source-a032591a12d56d656efb799c
    resource: repo://src/media_tools/server.py
  - id: openwiki-source-5d693fa860b270ba3e69348c
    resource: repo://src/media_tools/tools/video.py
generated: { by: "openwiki/0.5.2", at: "2026-09-20T15:15:56.877Z" }
---

## Overview

The `VideoToolkit` class (`/src/media_tools/tools/video.py`) provides 23 static video-processing methods. Every method is wired to the MCP server, and 19 of them are also reachable through the CLI `media-tools video …` subcommands.

The toolkit has one contract: every method returns a human-readable string and **never raises** — failures surface as `"Error: …"` results. Each method runs the same validation gate first (`validate_input` then `validate_output_dir`) and then shells out to ffmpeg, ffprobe, or (for frame-level operations) OpenCV via `_subprocess_with_logging`.

## Tool List

| Method | MCP Name | MCP Tag | CLI Command | Description | Key Deps |
|---|---|---|---|---|---|
| `convert` | `video_convert` | video | `video convert` | Convert between formats (extension determines codec) | ffmpeg |
| `trim` | `video_trim` | video | `video trim` | Trim video (HH:MM:SS, `--start`/`--end`) | ffmpeg |
| `compress` | `video_compress` | video | `video compress` | Compress with CRF (18 near-lossless, 23–28 good, 51 worst) | ffmpeg |
| `to_gif` | `video_to_gif` | video | `video to-gif` | Convert segment to animated GIF (width, fps, start, duration) | ffmpeg |
| `gif_to_mp4` | `gif_to_mp4` | video | `video gif-to-mp4` | Convert GIF to MP4 (h264 + yuv420p + faststart) | ffmpeg, ffprobe |
| `probe` | `video_probe` | video | `video info` | Get metadata: codec, resolution, duration, bitrate | ffprobe |
| `extract_audio` | `video_extract_audio` | video | *(none)* | Extract audio track (format: mp3, aac, wav, ogg, flac) | ffmpeg |
| `extract_frames` | `video_extract_frames` | video | *(none)* | Extract frames from video as images | OpenCV |
| `crop` | `video_crop` | video | `video crop` | Crop video to width/height at x/y | ffmpeg |
| `rotate` | `video_rotate` | video | `video rotate` | Rotate by angle (90/180/270°) | ffmpeg |
| `resize` | `video_resize` | video | `video resize` | Resize video (width, height; -2 preserves aspect) | ffmpeg |
| `reverse` | `video_reverse` | video | `video reverse` | Reverse playback (loads full clip into memory) | ffmpeg |
| `speed` | `video_speed` | video | `video speed` | Change playback speed (factor > 1 up, < 1 down) | ffmpeg |
| `merge` | `video_merge` | video | `video merge` | Merge multiple videos (stream-copy fast path or re-encode) | ffmpeg |
| `thumbnail` | `video_thumbnail` | video | `video thumbnail` | Grab a single frame as an image (fast input-seek or frame-exact) | ffmpeg |
| `contact_sheet` | `video_contact_sheet` | video | `video contact-sheet` | Grid contact sheet PNG + sidecar JSON manifest (tiles capped at 120) | ffmpeg |
| `watermark` | `video_watermark` | video | `video watermark` | Overlay an image watermark onto a video | ffmpeg |
| `subtitle_burn` | `video_subtitle_burn` | video | `video subtitle-burn` | Burn .srt/.ass subtitles into video (plain/karaoke/social presets) | ffmpeg |
| `export_social_pack` | `video_export_social_pack` | video | `video social-pack` | Export 9:16 / 1:1 / 16:9 MP4 variants in one decode pass | ffmpeg |
| `chroma_cut` | `video_chroma_cut` | video | `video chroma-cut` | Key out a solid color via colorkey, composited over background | ffmpeg |
| `object_erase` | `video_object_erase` | video | `video object-erase` | Erase fixed x,y,w,h rects on every frame via cv2.inpaint | OpenCV, ffmpeg |
| `slideshow` | `image_to_video` | **image** | *(none)* | Create a video slideshow from images | ffmpeg |
| `audio_to_video` | `audio_to_video` | **audio** | *(none)* | Mux an audio track onto a video, replacing its audio | ffmpeg |

**Totals:** 23 MCP tools (21 video-tagged, 1 image-tagged, 1 audio-tagged) and 19 CLI commands.

## Wiring

### MCP server (`/src/media_tools/server.py`)

`VideoToolkit` is imported at module level (L15) and most video-tagged tool handlers delegate directly — e.g. `video_convert` → `VideoToolkit.convert`. Seven handlers instead **lazily import** `VideoToolkit` inside the function body to defer the import:

- `video_contact_sheet` (L291)
- `video_export_social_pack` (L299)
- `video_chroma_cut` (L314)
- `video_object_erase` (L328)
- `video_extract_frames` (L688)
- `image_to_video` (L674, tagged **image**)
- `audio_to_video` (L696, tagged **audio**)

`main_video()` runs the server scoped to the `video` tag only via `_run_scoped("video")` (L861–L862).

### CLI (`/src/media_tools/cli.py`)

The `video` category (L628) registers 19 subcommands, each handled by a `_video_*` closure that pulls arguments from the parsed namespace. Notably the CLI `trim` passes only `start`/`end` (no `duration`), and `to-gif` passes only `width`/`fps`, so those CLI invocations fall back to the toolkit defaults. `merge` also gains a `--cover` flag that triggers thumbnail generation. Three methods (`extract_audio`, `extract_frames`, `slideshow`) have no CLI subcommand.

## Implementation Details

### Dependencies

- **ffmpeg** — System installation required for all methods except the two OpenCV-based operations (`extract_frames`, `object_erase`).
- **moviepy** — Previously used by the composition tools; no longer imported by any current method (composition tools were rewritten to pure ffmpeg).
- **opencv-python-headless ≥ 5.0.0.93** — Imported lazily inside `extract_frames` and `object_erase`.

### Validation gate

Every method runs `validate_input(input_path)` followed by `validate_output_dir(output)` and returns the first error string. `validate_input` rejects empty paths, paths containing `..` (path traversal), and non-existent / non-file / non-readable paths, but allows `http(s)://` URLs through. `validate_output_dir` creates the parent directory if missing and rejects unwritable output. This gate is identical across the audio, image, and video toolkits.

### `_codec_for()` — extension → codec mapping

`_codec_for(output, crf=None)` (`/src/media_tools/tools/video.py#L1056-L1072`) maps the output file extension to a fixed set of ffmpeg arguments and is called by `convert`, `compress`, `trim`, `crop`, `rotate`, `resize`, `reverse`, `speed`, `merge`, `watermark`, `subtitle_burn`, `contact_sheet`, `export_social_pack`, and `chroma_cut`:

- `.mp4` → `-c:v libx264 -preset medium`
- `.webm` → `-c:v libvpx-vp9`
- `.mov` → `-c:v prores_ks -profile:v 3`
- `.gif` → `[]` (no codec args — GIFs are handled by `to_gif`'s two-pass flow)
- anything else → `-c:v libx264`

The mapping always appends `-c:a aac -b:a 128k` for the audio track, and when `compress` passes a `crf` value, `-crf <value>` is inserted before the audio args.

### `to_gif()` — two-pass palette flow

`to_gif` (`/src/media_tools/tools/video.py#L72-L124`) produces a higher-quality GIF with two ffmpeg passes: the first renders `fps={fps},scale={width}:-1:flags=lanczos,palettegen` into a temporary `<output>.png` palette file; the second reuses that palette with `paletteuse`. The palette file is deleted with `Path(palette).unlink(missing_ok=True)` in a `finally` block.

### `probe()` — ffprobe JSON parsing

`probe` (`/src/media_tools/tools/video.py#L126-L171`) runs `ffprobe -v quiet -print_format json -show_format -show_streams` and parses the JSON. It reads `format` for duration and size (formatted by `_human_size`), then finds the first `video` and `audio` stream by `codec_type`. Video is rendered as `{codec_name} {width}x{height} @ {_rframe(r_frame_rate)} fps` and audio as `{codec_name} {sample_rate}Hz {channels}ch`. `_rframe` converts an FPS fraction string (e.g. `30000/1001`) to a decimal; on parse failure it returns the raw string. A non-zero return code returns `"Error: {stderr}"`.

### `extract_frames()` — OpenCV skip_frames logic

`extract_frames` (`/src/media_tools/tools/video.py#L601-L660`) opens the video with `cv2.VideoCapture`, creates the output directory, and computes `skip_frames = max(1, int(fps_actual / fps))` where `fps_actual` is the capture's real FPS (falling back to the requested `fps`). It seeks to `start` via `CAP_PROP_POS_MSEC`, optionally bounds the run by `start + duration`, then reads frames and saves every `skip_frames`-th frame as `frame_{NNNNNN}.png` via `cv2.imwrite`. A failure to open the file returns `"Error: Could not open video file"`; any other exception is caught and returned as `"Error: {exc}"`.

### `object_erase()` — OpenCV inpaint

`object_erase` (`/src/media_tools/tools/video.py#L847-L963`) parses one or more `x,y,w,h` box specifications, opens the video with `cv2.VideoCapture`, and for each frame within the optional time range builds a binary mask from the boxes, dilates it with a 3×3 kernel, and applies `cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)`. Processed frames are written to a temporary directory and reassembled via ffmpeg with the detected FPS.

### `contact_sheet()` — single-pass ffmpeg grid

`contact_sheet` (`/src/media_tools/tools/video.py#L352-L436`) probes the video duration, auto-reduces the sampling rate when `duration × fps` exceeds a 120-tile cap, then runs a single ffmpeg pass with `-vf fps={eff_fps},scale={w}:-1,tile={cols}x{rows}`. It writes a sidecar JSON manifest with per-tile `{tile_index, timestamp}` entries and a probe summary.

### `export_social_pack()` — single-decode multi-output

`export_social_pack` (`/src/media_tools/tools/video.py#L662-L735`) probes source dimensions, builds a 3-way ffmpeg `split=3` filter graph with per-branch crop/scale/pad targeting 1080×1920 (9:16), 1080×1080 (1:1), and 1920×1080 (16:9), and encodes all three variants in one decode pass. Supports `center-crop` and `letterbox` modes. Content is never upscaled.

### `chroma_cut()` — colorkey compositing

`chroma_cut` (`/src/media_tools/tools/video.py#L772-L845`) applies the `colorkey` filter with configurable similarity and blend, then composites over a background. When the `background` argument is a file path, it is used as the backdrop image; otherwise it is treated as a hex color name (defaulting to `black`).

### Composition tools — now pure ffmpeg

Both composition methods were rewritten from MoviePy to direct ffmpeg commands:

**`slideshow`** (`/src/media_tools/tools/video.py#L568-L599`) loops each input image with `-loop 1 -t {duration}`, applies scale/pad/fps filters, and joins them with `concat=n={n}:v=1:a=0`. The output codec args strip `-c:a` since slideshows have no audio stream.

**`audio_to_video`** (`/src/media_tools/tools/video.py#L737-L770`) maps `0:v:0` and `1:a:0`, copies the video codec (`-c:v copy`), and re-encodes audio to AAC at 128k.

### Other ffmpeg-based methods

`reverse` applies `-vf reverse -af areverse`; `speed` applies `setpts={1/factor}*PTS` and `atempo={factor}` (rejecting non-positive factors); `merge` writes a concat demuxer list file and runs `ffmpeg -f concat -safe 0` with a fast path (`-c copy`) when all inputs share codecs, falling back to a re-encode path that normalizes resolution and audio format; `watermark` maps a named position to an `overlay=` expression; `subtitle_burn` escapes the subtitle path and applies the `subtitles=` video filter with optional `force_style` for karaoke/social presets. `thumbnail` supports both fast input-seek (before `-i`) and frame-exact output-seek (`accurate=True`). All use `_codec_for(output)` and the shared subprocess helper.

## See Also

- [Architecture Overview](/openwiki/architecture/overview.md) — how video tools are exposed via MCP/CLI
- [Audio Tools](/openwiki/tools/audio.md) — `video_extract_audio` cross-reference
- [Image Tools](/openwiki/tools/image.md) — `image_to_video` cross-reference
