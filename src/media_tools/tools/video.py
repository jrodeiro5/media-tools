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
        input_path: str, output: str,
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
        input_path: str, output: str,
        width: int = 480, fps: int = 10,
        start: str = "00:00:00", duration: str = "5",
    ) -> str:
        """Convert a video segment into an animated GIF."""
        err = validate_input(input_path)
        if err:
            return err
        err = validate_output_dir(output)
        if err:
            return err

        palette = str(Path(output).with_suffix(".png"))
        cmd = [
            "ffmpeg", "-y",
            "-ss", start,
            "-t", duration,
            "-i", input_path,
            "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,palettegen",
            palette,
        ]
        _subprocess_with_logging(cmd, "Generated palette")

        cmd2 = [
            "ffmpeg", "-y",
            "-ss", start,
            "-t", duration,
            "-i", input_path,
            "-i", palette,
            "-filter_complex", f"fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse",
            output,
        ]
        desc, ok = _subprocess_with_logging(
            cmd2, "Generated GIF"
        )
        Path(palette).unlink(missing_ok=True)
        return desc

    @staticmethod
    def probe(input_path: str) -> str:
        """Get detailed video metadata."""
        err = validate_input(input_path)
        if err:
            return err

        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
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
            v = video.get('codec_name')
            w = video.get('width')
            h = video.get('height')
            fps = _rframe(video.get('r_frame_rate'))
            lines.append(f"Video: {v} {w}x{h} @ {fps} fps")
        if audio:
            a = audio.get('codec_name')
            sr = audio.get('sample_rate')
            ch = audio.get('channels')
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


    @staticmethod
    def slideshow(
        input_paths: list[str], output: str, fps: int = 30, duration_per_image: int = 5,
    ) -> str:
        """Create a video slideshow from images using MoviePy."""
        for p in input_paths:
            err = validate_input(p)
            if err:
                return err
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from moviepy import ImageClip, concatenate_videoclips
            clips = [ImageClip(p, duration=duration_per_image) for p in input_paths]
            video = concatenate_videoclips(clips, method="compose")
            video.write_videofile(output, fps=fps)
            video.close()
            logger.info("Slideshow → %s", output)
            return f"Slideshow → {output} ({len(input_paths)} images, {duration_per_image}s each)"
        except Exception as exc:
            logger.error("slideshow failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def extract_frames(
        input_path: str, output_dir: str, fps: int = 1, start: str = "00:00:00", duration: str | None = None,
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
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return "Error: Could not open video file"

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            frame_count = 0
            fps_actual = cap.get(cv2.CAP_PROP_FPS)
            skip_frames = int(fps_actual / fps)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % skip_frames == 0:
                    out_path = out_dir / f"frame_{frame_count:06d}.png"
                    cv2.imwrite(str(out_path), frame)
                frame_count += 1

            cap.release()
            logger.info("Extracted frames → %s", output_dir)
            return f"Extracted {frame_count // skip_frames} frames → {output_dir}"
        except Exception as exc:
            logger.error("extract_frames failed: %s", exc)
            return f"Error: {exc}"

    @staticmethod
    def audio_to_video(input_path: str, video_path: str, output: str) -> str:
        """Create a video with audio track using MoviePy."""
        err_audio = validate_input(input_path)
        if err_audio:
            return err_audio
        err_video = validate_input(video_path)
        if err_video:
            return err_video
        err = validate_output_dir(output)
        if err:
            return err

        try:
            from moviepy import AudioFileClip, VideoFileClip
            audio = AudioFileClip(input_path)
            video = VideoFileClip(video_path)
            video = video.set_audio(audio)
            video.write_videofile(output)
            video.close()
            audio.close()
            logger.info("Audio + Video → %s", output)
            return f"Audio + Video → {output}"
        except Exception as exc:
            logger.error("audio_to_video failed: %s", exc)
            return f"Error: {exc}"


def _human_size(size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
