---
name: media-video
description: "Use for video/audio-subtitle workflows via media-tools: transcode, transcription to SRT, burned subtitles, face blur, social packs. Examples: 'subtitle this video', 'transcribe and burn', 'blur the faces', 'make a GIF', 'mute this clip', 'export vertical version'"
---

# Video workflows (media-tools)

Start with `media_probe(path)` — it reports streams, duration, audio presence, and ranks tools.

## Subtitles: the 3-step chain (transcribe ≠ burn)

Transcription and burning are separate tools on purpose. Chain them:

1. `video_transcribe(input, out_dir)` → `{srt, transcript_json, txt}`. Extracts audio, chunks on silence, transcribes via LiteLLM proxy (needs it reachable; otherwise it returns `Error:`, fail loud, don't fake it). Review the `.srt` — whisper hallucinates on music/tones.
2. Inspect/fix the `.srt` (valid `HH:MM:SS,mmm`, monotonic, non-empty cues — `audio_to_srt` converts transcript JSONs to strict SRT if you re-segment manually).
3. `video_subtitle_burn(input, srt, output, preset=plain|karaoke|social)` for hardcoded subs. **Requires ffmpeg with libass** — the tool pre-checks and errors clearly (Debian/docker builds fine; stock Homebrew lacks it).

## Anonymize

- `video_blur_faces` (Haar frontal, pixelate default; `every_n_frames` + IoU tracking) and `image_blur_faces`. Frontal, well-lit faces only — profile/sunglasses won't match. Zero faces is success (`faces:0`), not an error.
- Output video is **video-only** (audio dropped, `object_erase` precedent) — re-mux with `video_merge` or ffmpeg if you need sound.
- No plate detection tool exists (no clean local model). Faces only.

## Transcode & social

`video_convert/trim/compress` (crf-based), `video_crop/rotate/resize`, `video_speed`, `video_reverse`, `video_mute` (`-an` one-liner), `video_to_gif`/`gif_to_mp4`, `video_extract_audio` (use it before audio tools), `video_extract_frames/thumbnail/contact_sheet`, `video_export_social_pack` (9:16 + 1:1 + 16:9, center-crop, never upscaled), `video_chroma_cut`, `video_object_erase`, `video_watermark`, `video_probe` (ffprobe JSON when you need raw streams).
