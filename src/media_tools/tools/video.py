"""Video manipulation toolkit — convert, trim, compress, GIF, probe, extract audio."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from media_tools.utils import _subprocess_with_logging, logger, validate_input, validate_output_dir


class VideoToolkit:
    name = "video"

    @staticmethod
    def convert(input_path: str, output: str) -> str:
        """Convert a video between formats."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        codec_args = _codec_for(output)
        cmd = ["ffmpeg", "-y", "-i", input_path, *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Converted to {output}")
        return desc

    @staticmethod
    def trim(
        input_path: str,
        output: str,
        start: str = "00:00:00",
        duration: str | None = None,
        end: str | None = None,
    ) -> str:
        """Trim a video. Times in HH:MM:SS. Use duration OR end (not both)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        codec_args = _codec_for(output)
        cmd = ["ffmpeg", "-y", "-i", input_path, "-ss", start]
        if end:
            cmd.extend(["-to", end])
        elif duration:
            cmd.extend(["-t", duration])
        cmd.extend(codec_args)
        cmd.append(output)
        desc, ok = _subprocess_with_logging(cmd, f"Trimmed → {output}")
        return desc

    @staticmethod
    def compress(input_path: str, output: str, crf: int = 28) -> str:
        """Compress a video. CRF: 18 near-lossless, 23-28 good, 51 worst."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        codec_args = _codec_for(output, crf=crf)
        cmd = ["ffmpeg", "-y", "-i", input_path, *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Compressed to {output}")
        return desc

    @staticmethod
    def to_gif(
        input_path: str,
        output: str,
        width: int = 480,
        fps: int = 10,
        start: str = "00:00:00",
        duration: str = "5",
    ) -> str:
        """Convert a video segment into an animated GIF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        palette = str(Path(output).with_suffix(".png"))
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                start,
                "-t",
                duration,
                "-i",
                input_path,
                "-vf",
                f"fps={fps},scale={width}:-1:flags=lanczos,palettegen",
                palette,
            ]
            _subprocess_with_logging(cmd, "Generated palette")

            cmd2 = [
                "ffmpeg",
                "-y",
                "-ss",
                start,
                "-t",
                duration,
                "-i",
                input_path,
                "-i",
                palette,
                "-filter_complex",
                f"fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse",
                output,
            ]
            desc, ok = _subprocess_with_logging(cmd2, "Generated GIF")
        finally:
            Path(palette).unlink(missing_ok=True)
        return desc

    @staticmethod
    def probe(input_path: str) -> str:
        """Get detailed video metadata."""
        err = validate_input(input_path)
        if err:
            return err

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            input_path,
        ]
        logger.debug("Running ffprobe: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("ffprobe failed: %s", result.stderr.strip())
            return f"Error: {result.stderr}"

        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        video = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), None)
        audio = next((s for s in data.get("streams", []) if s["codec_type"] == "audio"), None)

        lines = [
            f"Duration: {fmt.get('duration', 'N/A')}s",
            f"Size: {_human_size(int(fmt.get('size', 0)))}",
            f"Format: {fmt.get('format_name', 'N/A')}",
        ]
        if video:
            v = video.get("codec_name")
            w = video.get("width")
            h = video.get("height")
            fps = _rframe(video.get("r_frame_rate"))
            lines.append(f"Video: {v} {w}x{h} @ {fps} fps")
        if audio:
            a = audio.get("codec_name")
            sr = audio.get("sample_rate")
            ch = audio.get("channels")
            lines.append(f"Audio: {a} {sr}Hz {ch}ch")
        logger.info("Probed %s", input_path)
        return "\n".join(lines)

    @staticmethod
    def extract_audio(input_path: str, output: str, format: str = "mp3", bitrate: str = "192k") -> str:
        """Extract the audio track from a video."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        ext_map = {"mp3": "libmp3lame", "aac": "aac", "wav": "pcm_s16le", "ogg": "libvorbis", "flac": "flac"}
        codec = ext_map.get(format, "libmp3lame")
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vn", "-c:a", codec, "-b:a", bitrate, output]
        desc, ok = _subprocess_with_logging(cmd, f"Audio extracted to {output}")
        return desc

    @staticmethod
    def crop(input_path: str, output: str, width: int, height: int, x: int = 0, y: int = 0) -> str:
        """Crop a video to a rectangle (width x height, offset x,y)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        codec_args = _codec_for(output)
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", f"crop={width}:{height}:{x}:{y}", *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Cropped → {output}")
        return desc

    @staticmethod
    def rotate(input_path: str, output: str, angle: int = 90) -> str:
        """Rotate a video by 90, 180, or 270 degrees clockwise."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        transpose = {90: "transpose=1", 180: "transpose=1,transpose=1", 270: "transpose=2"}
        vf = transpose.get(angle % 360)
        if not vf:
            return "Error: angle must be 90, 180, or 270"

        codec_args = _codec_for(output)
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", vf, *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Rotated {angle}° → {output}")
        return desc

    @staticmethod
    def resize(input_path: str, output: str, width: int, height: int = -2) -> str:
        """Resize a video. Height -2 preserves aspect ratio (even dimensions)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        codec_args = _codec_for(output)
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", f"scale={width}:{height}", *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Resized → {output}")
        return desc

    @staticmethod
    def reverse(input_path: str, output: str) -> str:
        """Reverse a video (and its audio) — loads the full clip into memory."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        codec_args = _codec_for(output)
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", "reverse", "-af", "areverse", *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Reversed → {output}")
        return desc

    @staticmethod
    def speed(input_path: str, output: str, factor: float = 2.0) -> str:
        """Change playback speed. factor > 1 speeds up, < 1 slows down."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if factor <= 0:
            return "Error: factor must be positive"

        codec_args = _codec_for(output)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            f"setpts={1 / factor}*PTS",
            "-af",
            f"atempo={factor}",
            *codec_args,
            output,
        ]
        desc, ok = _subprocess_with_logging(cmd, f"Speed x{factor} → {output}")
        return desc

    @staticmethod
    def merge(input_paths: list[str], output: str, cover: bool = False) -> str:
        """Concatenate multiple videos in order.

        Fast path: when all inputs share container + video/audio codecs, join
        with the concat demuxer + `-c copy` (no re-encode). Otherwise (or when
        codec detection is inconclusive) fall back to re-encoding.

        cover: when True, also grab a fast thumbnail of the merged output
        (`<output-stem>_cover.png` next to the output) and return a JSON
        string with its path. Default False = plain-text return, unchanged.
        """
        for p in input_paths:
            err = validate_input(p)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err

        probed = [_stream_codecs(p) for p in input_paths]
        fast = bool(probed) and all(s is not None for s in probed) and all(s == probed[0] for s in probed)

        list_path = str(Path(output).with_suffix(".txt"))
        try:
            with open(list_path, "w") as f:
                for p in input_paths:
                    f.write(f"file '{Path(p).resolve()}'\n")

            if fast:
                cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output]
                desc, ok = _subprocess_with_logging(cmd, f"Merged {len(input_paths)} clips → {output} (stream copy)")
            else:
                desc, ok = _merge_reencode(input_paths, probed, output)
        finally:
            Path(list_path).unlink(missing_ok=True)
        if not cover:
            return desc
        if not ok:
            return desc
        cover_path = str(Path(output).with_name(f"{Path(output).stem}_cover.png"))
        thumb = VideoToolkit.thumbnail(output, cover_path)
        if thumb.startswith("Error"):
            return json.dumps({"result": desc, "output": output, "cover_error": thumb}, ensure_ascii=False)
        return json.dumps({"result": desc, "output": output, "cover": cover_path}, ensure_ascii=False)

    @staticmethod
    def thumbnail(input_path: str, output: str, timestamp: str = "00:00:01", accurate: bool = False) -> str:
        """Grab a single frame as an image.

        Fast path (default): input-seeking (`-ss` BEFORE `-i`) jumps straight to
        the nearest seek point — instant, but approximate (lands on a keyframe).
        Pass accurate=True for output-seeking (`-ss` AFTER `-i`): decodes up to
        the exact timestamp, so the grab is frame-exact but slower.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        if accurate:
            cmd = ["ffmpeg", "-y", "-i", input_path, "-ss", timestamp, "-frames:v", "1", output]
            desc, ok = _subprocess_with_logging(cmd, f"Thumbnail @ {timestamp} → {output} (accurate)")
        else:
            cmd = ["ffmpeg", "-y", "-ss", timestamp, "-i", input_path, "-frames:v", "1", output]
            desc, ok = _subprocess_with_logging(cmd, f"Thumbnail @ {timestamp} → {output}")
        return desc

    @staticmethod
    def contact_sheet(
        input_path: str,
        output_png: str,
        cols: int = 4,
        fps: int = 1,
        thumb_width: int = 320,
        manifest: bool = True,
    ) -> str:
        """Render a grid contact sheet (single PNG) + sidecar JSON manifest.

        ONE ffmpeg pass: `-vf fps={fps},scale={w}:-1,tile={cols}x{rows}`.
        Manifest `<output-stem>.json` holds per-tile `{tile_index, timestamp}`
        entries plus a probe summary (duration, codec, resolution).

        TILE CAP: total tiles are capped at 120. When duration*fps exceeds
        it, the sampling rate is auto-reduced to (120 / duration) so long
        videos can't produce gigapixel PNGs. `effective_fps` in the manifest
        and return records the rate actually used.

        TIMESTAMPS ARE APPROXIMATE: fps sampling picks wall-clock-spaced
        frames, which drifts on variable-frame-rate (VFR) input where frame
        intervals are uneven — tile i sits near i/effective_fps seconds, not
        exactly on it. Future tools must treat these as scrub hints, not
        frame-exact seeks (use thumbnail(accurate=True) for exact grabs).
        """
        import math

        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_png)
        if err:
            return err

        duration = _probe_duration(input_path)
        if duration is None:
            return f"Error: could not probe duration of {input_path}"
        if duration <= 0:
            return f"Error: zero-length video: {input_path}"

        max_tiles = 120
        eff_fps = float(fps)
        if duration * eff_fps > max_tiles:
            eff_fps = max_tiles / duration
        n_tiles = max(1, int(duration * eff_fps))
        rows = max(1, math.ceil(n_tiles / cols))

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            f"fps={eff_fps:.6f},scale={thumb_width}:-1,tile={cols}x{rows}",
            "-frames:v",
            "1",
            output_png,
        ]
        desc, ok = _subprocess_with_logging(cmd, f"Contact sheet → {output_png}")
        if not ok:
            return desc

        summary = _probe_summary(input_path)
        tiles = [{"tile_index": i, "timestamp": round(i / eff_fps, 3)} for i in range(n_tiles)]
        payload = {
            "result": desc,
            "output": output_png,
            "cols": cols,
            "rows": rows,
            "requested_fps": fps,
            "effective_fps": round(eff_fps, 6),
            "tile_cap": max_tiles,
            "capped": eff_fps < float(fps),
            "tiles": n_tiles,
            "probe": summary,
        }
        manifest_path = str(Path(output_png).with_suffix(".json"))
        if manifest:
            try:
                Path(manifest_path).write_text(json.dumps({**payload, "manifest": tiles}, indent=2), encoding="utf-8")
                payload["manifest"] = manifest_path
            except OSError as exc:
                return json.dumps({"result": desc, "output": output_png, "manifest_error": str(exc)})
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def watermark(
        input_path: str,
        watermark_path: str,
        output: str,
        position: str = "bottom-right",
        margin: int = 10,
    ) -> str:
        """Overlay an image watermark onto a video."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_input(watermark_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        positions = {
            "top-left": f"{margin}:{margin}",
            "top-right": f"main_w-overlay_w-{margin}:{margin}",
            "bottom-left": f"{margin}:main_h-overlay_h-{margin}",
            "bottom-right": f"main_w-overlay_w-{margin}:main_h-overlay_h-{margin}",
            "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
        }
        overlay_pos = positions.get(position)
        if not overlay_pos:
            return f"Error: position must be one of {list(positions)}"

        codec_args = _codec_for(output)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-i",
            watermark_path,
            "-filter_complex",
            f"overlay={overlay_pos}",
            *codec_args,
            output,
        ]
        desc, ok = _subprocess_with_logging(cmd, f"Watermarked → {output}")
        return desc

    _SUBTITLE_PRESETS = {
        "plain": None,
        "karaoke": (
            "FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,"
            "BackColour=&H80000000,BorderStyle=1,Outline=2,Shadow=1,"
            "Alignment=2,MarginV=25,Bold=1"
        ),
        "social": (
            "FontSize=36,PrimaryColour=&H00FFFFFF,OutlineColour=&HFF000000,"
            "BackColour=&H80000000,BorderStyle=1,Outline=3,Shadow=0,"
            "Alignment=8,MarginV=60,Bold=1"
        ),
    }

    @staticmethod
    def subtitle_burn(input_path: str, subtitle_path: str, output: str, preset: str = "plain") -> str:
        """Burn an .srt/.ass subtitle file into the video (hardcoded, non-toggleable).

        preset: 'plain' (source styling, default), 'karaoke' (bold bottom-caption
        look), or 'social' (large centered upper-third look for 9:16).
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_input(subtitle_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        style = VideoToolkit._SUBTITLE_PRESETS.get(preset)
        if preset not in VideoToolkit._SUBTITLE_PRESETS:
            return f"Error: unknown preset '{preset}'. Valid presets: {sorted(VideoToolkit._SUBTITLE_PRESETS)}"

        escaped = str(subtitle_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        vf = f"subtitles='{escaped}'"
        if style:
            vf += f":force_style='{style}'"
        codec_args = _codec_for(output)
        cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", vf, *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Burned subtitles ({preset}) → {output}")
        return desc

    @staticmethod
    def gif_to_mp4(input_path: str, output: str) -> str:
        """Convert a GIF (or any silent looping input) to MP4 (h264 + yuv420p + faststart)."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", input_path]
        probe = subprocess.run(probe_cmd, capture_output=True, text=True)
        if probe.returncode != 0:
            logger.error("ffprobe failed: %s", probe.stderr.strip())
            return f"Error: {probe.stderr.strip()}"
        try:
            streams = json.loads(probe.stdout).get("streams", [])
        except json.JSONDecodeError as exc:
            return f"Error: could not parse ffprobe output: {exc}"
        if not any(s.get("codec_type") == "video" for s in streams):
            return f"Error: input has no video stream: {input_path}"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output,
        ]
        desc, ok = _subprocess_with_logging(cmd, f"Converted GIF → {output}")
        return desc

    @staticmethod
    def slideshow(
        input_paths: list[str],
        output: str,
        fps: int = 30,
        duration_per_image: int = 5,
    ) -> str:
        """Create a video slideshow from images (each shown duration_per_image seconds)."""
        for p in input_paths:
            err = validate_input(p)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err

        n = len(input_paths)
        inputs: list[str] = []
        for p in input_paths:
            inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", p])
        filters = "".join(
            f"[{i}:v]scale=1280:720:force_original_aspect_ratio=decrease,"
            f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[v{i}];"
            for i in range(n)
        )
        filters += "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
        codec_args = _codec_for(output)
        if "-c:a" in codec_args:  # slideshow has no audio stream
            codec_args = codec_args[: codec_args.index("-c:a")]
        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filters, "-map", "[v]", *codec_args, output]
        desc, ok = _subprocess_with_logging(cmd, f"Slideshow → {output} ({n} images, {duration_per_image}s each)")
        return desc

    @staticmethod
    def extract_frames(
        input_path: str,
        output_dir: str,
        fps: int = 1,
        start: str = "00:00:00",
        duration: str | None = None,
    ) -> str:
        """Extract frames from video as images using OpenCV."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output_dir)
        if err:
            return err

        try:
            import cv2

            def _to_seconds(value: str) -> float:
                parts = [float(p) for p in value.split(":")]
                seconds = 0.0
                for part in parts:
                    seconds = seconds * 60 + part
                return seconds

            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return "Error: Could not open video file"

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            fps_actual = cap.get(cv2.CAP_PROP_FPS) or fps
            skip_frames = max(1, int(fps_actual / fps))

            start_seconds = _to_seconds(start)
            if start_seconds:
                cap.set(cv2.CAP_PROP_POS_MSEC, start_seconds * 1000)
            end_seconds = start_seconds + _to_seconds(duration) if duration else None

            frame_count = 0
            saved_count = 0
            while True:
                if end_seconds is not None and cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 >= end_seconds:
                    break
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % skip_frames == 0:
                    out_path = out_dir / f"frame_{frame_count:06d}.png"
                    cv2.imwrite(str(out_path), frame)
                    saved_count += 1
                frame_count += 1

            cap.release()
            logger.info("Extracted frames → %s", output_dir)
            return f"Extracted {saved_count} frames → {output_dir}"
        except Exception as exc:
            logger.error("extract_frames failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def export_social_pack(src: str, out_dir: str, mode: str = "center-crop") -> str:
        """Export 9:16 / 1:1 / 16:9 MP4 variants of one video in a single decode pass.

        ONE list-form ffmpeg command: split=3 + per-branch crop/scale/pad →
        three MP4s. Targets are 1080x1920 / 1080x1080 / 1920x1080, but content
        is NEVER upscaled — small sources yield smaller (aspect-correct) files.

        mode 'center-crop': crop to the target aspect first, then scale down.
        mode 'letterbox': scale-to-fit then pad with black to the exact target.

        LOAD-BEARING RISK: naive center-crop can decapitate faces/subjects —
        it cuts symmetric edges with no saliency awareness. Smart-focal
        detection is a future upgrade, not this method.
        """
        err = validate_input(src)
        if err:
            return err
        err = validate_output_dir(out_dir)
        if err:
            return err
        if mode not in ("center-crop", "letterbox"):
            return "Error: mode must be 'center-crop' or 'letterbox'"

        probed = _stream_codecs(src)
        if probed is None or not probed[3] or not probed[4]:
            return f"Error: could not probe video dimensions of {src}"
        sw, sh = probed[3], probed[4]
        has_audio = probed[2] is not None

        def _even(n: int) -> int:
            return max(2, (n // 2) * 2)

        targets = {"9x16": (1080, 1920), "1x1": (1080, 1080), "16x9": (1920, 1080)}
        branches: list[str] = []
        variants: list[dict[str, object]] = []
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        for i, (label, (tw, th)) in enumerate(targets.items()):
            aspect = tw / th
            if mode == "center-crop":
                if sw / sh > aspect:
                    cw, ch = min(sw, int(sh * aspect)), sh
                else:
                    cw, ch = sw, min(sh, int(sw / aspect))
                cw, ch = _even(cw), _even(ch)
                scale = min(1.0, tw / cw, th / ch)
                ow, oh = _even(int(cw * scale)), _even(int(ch * scale))
                filt = f"crop={cw}:{ch},scale={ow}:{oh}:flags=lanczos,setsar=1,format=yuv420p"
            else:
                ow, oh = _even(tw), _even(th)
                filt = (
                    f"scale={ow}:{oh}:force_original_aspect_ratio=decrease,"
                    f"pad={ow}:{oh}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p"
                )
            branches.append(f"[s{i}]{filt}[v{label}]")
            dest = str(out / f"{Path(src).stem}_{label}.mp4")
            variants.append({"label": label, "path": dest, "width": ow, "height": oh})

        labels = "".join(f"[s{i}]" for i in range(3))
        filtergraph = f"split=3{labels};" + ";".join(branches)
        codec_args = _codec_for("out.mp4")
        if not has_audio and "-c:a" in codec_args:  # silent input → no audio stream
            codec_args = codec_args[: codec_args.index("-c:a")]
        cmd = ["ffmpeg", "-y", "-i", src, "-filter_complex", filtergraph]
        for v in variants:
            cmd.extend(["-map", f"[v{v['label']}]"])
            if has_audio:
                cmd.extend(["-map", "0:a?"])
            cmd.extend([*codec_args, str(v["path"])])
        desc, ok = _subprocess_with_logging(cmd, f"Social pack ({mode}) → {out_dir}")
        if not ok:
            return desc
        return json.dumps({"mode": mode, "source": src, "variants": variants}, ensure_ascii=False)

    @staticmethod
    def audio_to_video(input_path: str, video_path: str, output: str) -> str:
        """Mux an audio track onto a video, replacing its audio if any."""
        err_audio = validate_input(input_path)
        if err_audio:
            return err_audio
        err_video = validate_input(video_path)
        if err_video:
            return err_video
        err = validate_output_dir(output)
        if err:
            return err

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-i",
            input_path,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            output,
        ]
        desc, ok = _subprocess_with_logging(cmd, f"Audio + Video → {output}")
        return desc

    @staticmethod
    def chroma_cut(
        input_path: str,
        output: str,
        color: str = "00FF00",
        similarity: float = 0.3,
        blend: float = 0.1,
        background: str = "black",
    ) -> str:
        """Key out a solid color via colorkey, composited over a background image or color."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        cleaned = color.lstrip("#")
        if len(cleaned) != 6:
            return f"Error: color must be a 6-digit hex like 00FF00, got '{color}'"
        try:
            int(cleaned, 16)
        except ValueError:
            return f"Error: color must be a 6-digit hex like 00FF00, got '{color}'"
        if not 0.0 <= similarity <= 1.0:
            return f"Error: similarity must be 0..1, got {similarity}"
        if not 0.0 <= blend <= 1.0:
            return f"Error: blend must be 0..1, got {blend}"

        keyed = f"colorkey=0x{cleaned}:{similarity}:{blend}"
        codec_args = _codec_for(output)
        if Path(background).exists():
            err = validate_input(background)
            if err:
                return err
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-i",
                background,
                "-filter_complex",
                f"[0:v]{keyed}[fg];[1:v][fg]scale2ref[bg][fg2];[bg][fg2]overlay=0:0,format=yuv420p",
                *codec_args,
                output,
            ]
        else:
            bg = background.lstrip("#") or "black"
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-filter_complex",
                f"[0:v]{keyed}[fg];color={bg}[c];[c][fg]scale2ref[bg][fg2];"
                "[bg][fg2]overlay=0:0:shortest=1,format=yuv420p",
                *codec_args,
                output,
            ]
        desc, ok = _subprocess_with_logging(cmd, f"Chroma cut → {output}")
        if not ok:
            return desc
        return json.dumps(
            {
                "result": desc,
                "output": output,
                "color": cleaned,
                "similarity": similarity,
                "blend": blend,
                "background": background,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def object_erase(
        input_path: str,
        output: str,
        boxes: list[str],
        start: str | None = None,
        duration: str | None = None,
    ) -> str:
        """Erase fixed x,y,w,h rects on every frame via cv2.inpaint (TELEA).

        Time range via start/duration (seconds or HH:MM:SS); frames outside
        the range pass through untouched.
        """
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err
        if not boxes:
            return "Error: at least one --box x,y,w,h is required"

        parsed: list[tuple[int, int, int, int]] = []
        for box in boxes:
            try:
                x, y, w, h = (int(v) for v in box.split(","))
            except ValueError:
                return f"Error: box must be 'x,y,w,h' ints, got '{box}'"
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                return f"Error: box needs x,y >= 0 and w,h > 0, got '{box}'"
            parsed.append((x, y, w, h))

        def _to_seconds(value: str) -> float:
            parts = [float(p) for p in value.split(":")]
            seconds = 0.0
            for part in parts:
                seconds = seconds * 60 + part
            return seconds

        try:
            import tempfile

            import cv2
            import numpy as np
        except Exception as exc:
            return f"Error: {exc}"

        try:
            start_seconds = _to_seconds(start) if start else 0.0
            duration_seconds = _to_seconds(duration) if duration else None
        except ValueError:
            return f"Error: start/duration must be seconds or HH:MM:SS, got '{start}/{duration}'"

        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return "Error: Could not open video file"
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if start_seconds:
                cap.set(cv2.CAP_PROP_POS_MSEC, start_seconds * 1000)
            end_msec = (start_seconds + duration_seconds) * 1000 if duration_seconds else None
            kernel = np.ones((3, 3), np.uint8)
            with tempfile.TemporaryDirectory() as tmp:
                frame_idx = 0
                processed = 0
                while True:
                    if end_msec is not None and cap.get(cv2.CAP_PROP_POS_MSEC) >= end_msec:
                        break
                    ret, frame = cap.read()
                    if not ret:
                        break
                    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                    for x, y, w, h in parsed:
                        x2 = min(frame.shape[1], x + w)
                        y2 = min(frame.shape[0], y + h)
                        if x2 > x and y2 > y:
                            mask[y:y2, x:x2] = 255
                    mask = cv2.dilate(mask, kernel, iterations=1)
                    frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
                    cv2.imwrite(str(Path(tmp) / f"frame_{frame_idx:06d}.png"), frame)
                    frame_idx += 1
                    processed += 1
                cap.release()
                if processed == 0:
                    return "Error: no frames processed in the given time range"
                codec_args = _codec_for(output)
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(Path(tmp) / "frame_%06d.png"),
                    *codec_args,
                    output,
                ]
                desc, ok = _subprocess_with_logging(cmd, f"Object erase → {output}")
                if not ok:
                    return desc
        except Exception as exc:
            logger.error("object_erase failed: %s", exc)
            return f"Error: {exc}"
        return json.dumps(
            {
                "result": desc,
                "output": output,
                "frames_processed": processed,
                "boxes": boxes,
                "width": width,
                "height": height,
                "hint": "verify with video_contact_sheet before/after "
                "(inpaint can leave smeared ghosts on large boxes)",
            },
            ensure_ascii=False,
        )


def _merge_reencode(
    input_paths: list[str],
    probed: list[tuple[str | None, str | None, str | None, int | None, int | None] | None],
    output: str,
) -> tuple[str, bool]:
    """Join mismatched inputs via the concat filter (re-encode).

    Normalizes every segment to the first input's resolution and a common
    audio format so clips with different codecs/sizes join at full length.
    Audio is kept only when every input has it (and the output isn't .gif).
    """
    n = len(input_paths)
    first = probed[0] if probed and probed[0] else (None, None, None, None, None)
    width, height = first[3] or 320, first[4] or 240
    keep_audio = Path(output).suffix.lower() != ".gif" and all(s is not None and s[2] is not None for s in probed)

    inputs: list[str] = []
    for p in input_paths:
        inputs.extend(["-i", p])
    filters = "".join(f"[{i}:v]scale={width}:{height},setsar=1,format=yuv420p[v{i}];" for i in range(n))
    vlabels = "".join(f"[v{i}]" for i in range(n))
    if keep_audio:
        filters += "".join(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}];" for i in range(n))
        filters += vlabels + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
        maps = ["-map", "[v]", "-map", "[a]"]
        codec_args = _codec_for(output)
    else:
        filters += vlabels + f"concat=n={n}:v=1:a=0[v]"
        maps = ["-map", "[v]"]
        codec_args = _codec_for(output)
        if "-c:a" in codec_args:  # no audio stream to encode
            codec_args = codec_args[: codec_args.index("-c:a")]
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filters, *maps, *codec_args, output]
    return _subprocess_with_logging(cmd, f"Merged {n} clips → {output} (re-encode)")


def _probe_duration(path: str) -> float | None:
    """Return container duration in seconds, or None when undetectable."""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return float(json.loads(result.stdout).get("format", {}).get("duration", "nan"))
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def _probe_summary(path: str) -> dict:
    """Return a small {duration, video codec, width, height} probe summary."""
    info = _stream_codecs(path)
    duration = _probe_duration(path)
    if info is None:
        return {"duration": duration}
    fmt, vcodec, acodec, width, height = info
    return {
        "duration": duration,
        "format": fmt,
        "video_codec": vcodec,
        "audio_codec": acodec,
        "width": width,
        "height": height,
    }


def _stream_codecs(
    path: str,
) -> tuple[str | None, str | None, str | None, int | None, int | None] | None:
    """Probe (container, video codec, audio codec, width, height) for concat-compatibility.

    Returns None when detection is inconclusive (ffprobe failure, unparsable
    output, or no video stream) — callers must fall back, never fail.
    """
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    fmt = data.get("format", {}).get("format_name")
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        return None
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    acodec = audio.get("codec_name") if audio else None
    return (fmt, video.get("codec_name"), acodec, video.get("width"), video.get("height"))


def _codec_for(output: str, crf: int | None = None) -> list:
    """Return ffmpeg codec args based on output file extension."""
    ext = Path(output).suffix.lower()
    if ext == ".mp4":
        args = ["-c:v", "libx264", "-preset", "medium"]
    elif ext == ".webm":
        args = ["-c:v", "libvpx-vp9"]
    elif ext == ".mov":
        args = ["-c:v", "prores_ks", "-profile:v", "3"]
    elif ext == ".gif":
        return []
    else:
        args = ["-c:v", "libx264"]
    if crf is not None:
        args.extend(["-crf", str(crf)])
    args.extend(["-c:a", "aac", "-b:a", "128k"])
    return args


def _rframe(rate: str) -> str:
    """Convert FPS fraction string to decimal float."""
    try:
        num, den = rate.split("/")
        return f"{float(num) / float(den):.1f}"
    except (ValueError, ZeroDivisionError):
        return rate


def _human_size(size: float) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
